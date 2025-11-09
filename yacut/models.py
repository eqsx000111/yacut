from datetime import datetime
from http import HTTPStatus
import random
import re

from flask import url_for

from . import db
from .constants import (
    ALLOWED_CHARS,
    AUTO_GENERATE_SHORT_MAX_LENGTH,
    FORBIDDEN_SHORTS,
    MAX_SHORT_GENERATION_ATTEMPTS,
    ORIGINAL_LINK_MAX_LENGTH,
    REDIRECT_VIEW,
    SHORT_REG_EXPR,
    USER_SHORT_MAX_LENGTH,
)
from .errors import ShortUrlError

INVALID_ORIGINAL_URL_TEXT = 'Указано недопустимое имя для длинной ссылки'
INVALID_SHORT_TEXT = 'Указано недопустимое имя для короткой ссылки'
SHORT_EXIST_TEXT = 'Предложенный вариант короткой ссылки уже существует.'
CANT_GENERATE_UNIQUE_SHORT = (
    'Не удалось сгенерировать уникальную короткую ссылку за 10 попыток'
)


class URLMap(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    original = db.Column(db.String(ORIGINAL_LINK_MAX_LENGTH), nullable=False)
    short = db.Column(
        db.String(AUTO_GENERATE_SHORT_MAX_LENGTH),
        nullable=False,
        unique=True
    )
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    @staticmethod
    def get(short, raise_404=False):
        query = URLMap.query.filter_by(short=short)
        if raise_404:
            return query.first_or_404()
        return query.first()

    @staticmethod
    def create(original, short, validate_short=False, validate_original=False):
        if not validate_original and len(original) > ORIGINAL_LINK_MAX_LENGTH:
            raise ShortUrlError(INVALID_ORIGINAL_URL_TEXT)
        if short:
            if not validate_short:
                if len(short) > USER_SHORT_MAX_LENGTH or not re.fullmatch(
                    SHORT_REG_EXPR, short
                ):
                    raise ShortUrlError(
                        INVALID_SHORT_TEXT
                    )
                if short in FORBIDDEN_SHORTS or URLMap.get(short):
                    raise ShortUrlError(
                        SHORT_EXIST_TEXT
                    )
        else:
            short = URLMap.generate_unique_short()

        url_map = URLMap(original=original, short=short)
        db.session.add(url_map)
        db.session.commit()
        return url_map

    @staticmethod
    def generate_unique_short():
        for _ in range(MAX_SHORT_GENERATION_ATTEMPTS):
            short = ''.join(random.choices(
                ALLOWED_CHARS,
                k=AUTO_GENERATE_SHORT_MAX_LENGTH
            ))
            if not URLMap.get(short):
                return short
        raise ShortUrlError(
            CANT_GENERATE_UNIQUE_SHORT,
            HTTPStatus.INTERNAL_SERVER_ERROR
        )

    def get_short_url(self):
        return url_for(REDIRECT_VIEW, short=self.short, _external=True)
