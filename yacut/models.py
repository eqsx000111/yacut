from datetime import datetime
from http import HTTPStatus
import random
import re

from flask import url_for

from . import db
from .constants import (
    ALLOWED_CHARS,
    AUTO_GENERATE_SHORT_MAX_LENGTH,
    FORBIDDEN_SHORT,
    MAX_SHORT_GENERATION_ATTEMPTS,
    ORIGINAL_LINK_MAX_LENGTH,
    REDIRECT_VIEW,
    SHORT_REG_EXPR,
    USER_SHORT_MAX_LENGTH,
)
from .error_handlers import InvalidAPIUsage

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
    def get(short):
        return URLMap.query.filter_by(short=short).first()

    @staticmethod
    def get_or_404(short):
        return URLMap.query.filter_by(short=short).first_or_404()

    @staticmethod
    def create(original, short, from_form=False):
        if short:
            if not from_form:
                if short in FORBIDDEN_SHORT or URLMap.get(short):
                    raise InvalidAPIUsage(
                        SHORT_EXIST_TEXT
                    )
                if len(short) > USER_SHORT_MAX_LENGTH or not re.fullmatch(
                    SHORT_REG_EXPR, short
                ):
                    raise InvalidAPIUsage(
                        INVALID_SHORT_TEXT
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
        raise InvalidAPIUsage(
            CANT_GENERATE_UNIQUE_SHORT,
            HTTPStatus.INTERNAL_SERVER_ERROR
        )

    def get_short_url(self):
        return url_for(REDIRECT_VIEW, short=self.short, _external=True)
