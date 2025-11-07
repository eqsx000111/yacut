from flask_wtf import FlaskForm
from flask_wtf.file import MultipleFileField
from wtforms import SubmitField, URLField
from wtforms.validators import (
    DataRequired,
    Length,
    Optional,
    Regexp,
    ValidationError,
)

from .constants import (
    FORBIDDEN_SHORT,
    ORIGINAL_LINK_MAX_LENGTH,
    REG_EXPR,
    USER_CUSTOM_ID_MAX_LENGTH,
)
from .models import URLMap

EXIST_SHORT_TEXT = 'Предложенный вариант короткой ссылки уже существует.'
INVALID_CHAR_IN_SHORT_TEXT = (
    'Для данного поля допустимо использование только латинских букв '
    '(верхнего и нижнего регистра) и цифр.'
)
REQUIRED_FIELD = 'Обязательное поле'


class ShortUrlForm(FlaskForm):
    original_link = URLField(
        'Длинная ссылка',
        validators=[DataRequired(message=REQUIRED_FIELD),
                    Length(max=ORIGINAL_LINK_MAX_LENGTH)]
    )
    custom_id = URLField(
        'Ваш вариант короткой ссылки',
        validators=[
            Length(max=USER_CUSTOM_ID_MAX_LENGTH),
            Regexp(REG_EXPR, message=INVALID_CHAR_IN_SHORT_TEXT),
            Optional()
        ]
    )
    submit = SubmitField()

    def validate_custom_id(self, field):
        if field.data:
            if FORBIDDEN_SHORT in field.data:
                raise ValidationError(EXIST_SHORT_TEXT)
            if URLMap.get_by_short(field.data):
                raise ValidationError(EXIST_SHORT_TEXT)


class FilesShortUrlForm(FlaskForm):
    files = MultipleFileField(
        validators=[DataRequired(message=REQUIRED_FIELD)]
    )
    submit = SubmitField()