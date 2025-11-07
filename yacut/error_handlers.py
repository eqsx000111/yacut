from http import HTTPStatus
from flask import flash, jsonify, redirect, render_template, request, url_for

from . import app, db


class InvalidAPIUsage(Exception):

    def __init__(self, message, status_code=HTTPStatus.BAD_REQUEST):
        super().__init__()
        self.message = message
        self.status_code = status_code
        if status_code is not HTTPStatus.BAD_REQUEST:
            self.status_code = status_code

    def to_dict(self):
        return dict(message=self.message)


@app.errorhandler(InvalidAPIUsage)
def invalid_api_usage(error):
    if request.is_json or request.path.startswith('/api/'):
        return jsonify(error.to_dict()), error.status_code
    else:
        flash(error.message)
        return redirect(url_for('url_shortener'))


@app.errorhandler(HTTPStatus.NOT_FOUND)
def page_not_found(error):
    return render_template('404.html'), HTTPStatus.NOT_FOUND


@app.errorhandler(HTTPStatus.INTERNAL_SERVER_ERROR)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), HTTPStatus.INTERNAL_SERVER_ERROR


class YandexDiskError(Exception):
    def __init__(self, message, status_code=None):
        super().__init__()
        self.message = message
        if status_code is not HTTPStatus.BAD_REQUEST:
            self.status_code = status_code

    def to_dict(self):
        return {'message': self.message}