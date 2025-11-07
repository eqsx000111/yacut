from flask import jsonify, request
from http import HTTPStatus
from . import app
from .error_handlers import InvalidAPIUsage
from .models import URLMap

NO_DATA_TEXT = 'Отсутствует тело запроса'
NO_URL_TEXT = '"url" является обязательным полем!'
ID_NOT_FOUND_TEXT = 'Указанный id не найден'


@app.route('/api/id/', methods=['POST'])
def create_short_url_api():
    data = request.get_json(silent=True)
    if not data:
        raise InvalidAPIUsage(NO_DATA_TEXT, HTTPStatus.BAD_REQUEST)
    if 'url' not in data:
        raise InvalidAPIUsage(
            NO_URL_TEXT, HTTPStatus.BAD_REQUEST
        )
    original = data.get('url')
    short = data.get('custom_id')

    url_map = URLMap.create(original=original, short=short)
    return jsonify(
        {'url': url_map.original, 'short_link': url_map.get_short_url()}
    ), 201


@app.route('/api/id/<string:short>/', methods=['GET'])
def get_full_url(short):
    full_url = URLMap.get_by_short(short)
    if not full_url:
        raise InvalidAPIUsage(ID_NOT_FOUND_TEXT, HTTPStatus.NOT_FOUND)
    return jsonify({'url': full_url.original})
