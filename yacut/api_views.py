import re
from flask import jsonify, request, url_for

from . import app, db
from .constants import FORBIDDEN_LINK
from .error_handlers import InvalidAPIUsage
from .models import URLMap
from .views import generate_short_url

SHORT_PATTERN = re.compile(r'^[A-Za-z0-9]{1,16}$')


@app.route('/api/id/', methods=['POST'])
def get_short_url():
    try:
        data = request.get_json()
    except Exception:
        raise InvalidAPIUsage('Отсутствует тело запроса', 400)
    if not data or 'url' not in data:
        raise InvalidAPIUsage(
            '"url" является обязательным полем!'
        )
    if 'custom_id' not in data or not data['custom_id']:
        short = generate_short_url()
        while URLMap.query.filter_by(short=short).first():
            short = generate_short_url()
    else:
        short = data['custom_id']
        if FORBIDDEN_LINK in short or URLMap.query.filter_by(
            short=short
        ).first():
            raise InvalidAPIUsage(
                'Предложенный вариант короткой ссылки уже существует.'
            )
        if not SHORT_PATTERN.fullmatch(short) or len(short) > 16:
            raise InvalidAPIUsage(
                'Указано недопустимое имя для короткой ссылки'
            )

    link = URLMap(original=data['url'], short=short)
    db.session.add(link)
    db.session.commit()
    return jsonify({
        'url': link.original,
        'short_link': url_for(
            'redirect_view',
            short=link.short,
            _external=True
        )
    }), 201


@app.route('/api/id/<string:short_id>/', methods=['GET'])
def get_full_url(short_id):
    full_url = URLMap.query.filter_by(short=short_id).first()
    if not full_url:
        raise InvalidAPIUsage('Указанный id не найден', 404)
    return jsonify({'url': full_url.original})
