from http import HTTPStatus

from flask import jsonify, request

from . import app
from .error_handlers import InvalidAPIUsage
from .models import URLMap

NO_DATA_TEXT = 'Отсутствует тело запроса'
NO_URL_TEXT = '"url" является обязательным полем!'
ID_NOT_FOUND_TEXT = 'Указанный id не найден'
UNEXPECTED_ERROR = 'Непредвиденная ошибка при создании короткой ссылки:'


@app.route('/api/id/', methods=['POST'])
def create_short_url_api():
    data = request.get_json(silent=True)
    if not data:
        raise InvalidAPIUsage(NO_DATA_TEXT)
    if 'url' not in data:
        raise InvalidAPIUsage(
            NO_URL_TEXT
        )
    try:
        url_map = URLMap.create(
            original=data['url'],
            short=data.get('custom_id')
        )
    except Exception as validation_error:
        raise validation_error
    except Exception as unexpected_error:
        raise InvalidAPIUsage(
            f'{UNEXPECTED_ERROR} {unexpected_error}',
            HTTPStatus.INTERNAL_SERVER_ERROR
        )
    return jsonify(
        {'url': data['url'], 'short_link': url_map.get_short_url()}
    ), 201


@app.route('/api/id/<string:short>/', methods=['GET'])
def get_full_url(short):
    if not (full_url := URLMap.get(short)):
        raise InvalidAPIUsage(ID_NOT_FOUND_TEXT, HTTPStatus.NOT_FOUND)
    return jsonify({'url': full_url.original})
