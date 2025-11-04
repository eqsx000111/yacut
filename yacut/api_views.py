from flask import jsonify, request, url_for

from . import app, db
from .constants import FORBIDDEN_LINK
from .error_handlers import InvalidAPIUsage
from .models import URLMap
from .views import generate_short_url


@app.route('/api/id/', methods=['POST'])
def get_short_url():
    data = request.get_json()
    if not data or 'url' not in data:
        raise InvalidAPIUsage(
            'В запросе отсутствует обязательное поле - "url".'
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
            raise InvalidAPIUsage('Короткая ссылка занята или не доступна.')

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


@app.route('/api/id/<int:short_id>', methods=['GET'])
def get_full_url(short_id):
    full_url = URLMap.query.get(short_id)
    if not full_url:
        raise InvalidAPIUsage(f'Указанный id: {short_id} - не найден', 404)
    return jsonify({'url': full_url.original})