from datetime import datetime
from http import HTTPStatus
import random
import re

from flask import abort, url_for

from . import db

from .constants import (
    ALLOWED_CHARS,
    CUSTUM_ID_MAX_LENGTH,
    FORBIDDEN_SHORT,
    MAX_SHORT_GENERATION_ATTEMPTS,
    ORIGINAL_LINK_MAX_LENGTH,
    REG_EXPR,
    USER_CUSTOM_ID_MAX_LENGTH
)
from .error_handlers import InvalidAPIUsage

INVALID_SHORT_TEXT = 'Указано недопустимое имя для короткой ссылки'
SHORT_EXIST_TEXT = 'Предложенный вариант короткой ссылки уже существует.'
CANT_GENERATE_UNIQUE_SHORT = (
    'Не удалось сгенерировать уникальную короткую ссылку'
)


class URLMap(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    original = db.Column(db.String(ORIGINAL_LINK_MAX_LENGTH), nullable=False)
    short = db.Column(
        db.String(CUSTUM_ID_MAX_LENGTH),
        nullable=False,
        unique=True
    )
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    @staticmethod
    def get_by_short(short):
        return URLMap.query.filter_by(short=short).first()

    @staticmethod
    def get_or_404(short):
        url = URLMap.query.filter_by(short=short).first()
        if url is None:
            abort(404)
        return url

    @staticmethod
    def create(original, short):
        if short:
            if FORBIDDEN_SHORT in short:
                raise InvalidAPIUsage(
                    SHORT_EXIST_TEXT,
                    HTTPStatus.BAD_REQUEST
                )
            if not re.fullmatch(
                REG_EXPR, short
            ) or len(short) > USER_CUSTOM_ID_MAX_LENGTH:
                raise InvalidAPIUsage(
                    INVALID_SHORT_TEXT, HTTPStatus.BAD_REQUEST
                )
            if URLMap.get_by_short(short):
                raise InvalidAPIUsage(SHORT_EXIST_TEXT, HTTPStatus.BAD_REQUEST)
        else:
            for _ in range(MAX_SHORT_GENERATION_ATTEMPTS):
                short = ''.join(
                    random.choices(ALLOWED_CHARS, k=CUSTUM_ID_MAX_LENGTH)
                )
                if not URLMap.get_by_short(short):
                    break
                else:
                    raise InvalidAPIUsage(
                        CANT_GENERATE_UNIQUE_SHORT,
                        HTTPStatus.INTERNAL_SERVER_ERROR
                    )

        url_map = URLMap(original=original, short=short)
        db.session.add(url_map)
        db.session.commit()
        return url_map

    def get_short_url(self):
        return url_for('redirect_view', short=self.short, _external=True)
