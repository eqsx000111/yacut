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
    SHORT_REG_EXPR,
    USER_SHORT_MAX_LENGTH,
)
from .models import URLMap

EXIST_SHORT = 'Предложенный вариант короткой ссылки уже существует.'
INVALID_CHAR_IN_SHORT = (
    'Для данного поля допустимо использование только латинских букв '
    '(верхнего и нижнего регистра) и цифр.'
)
REQUIRED_FIELD = 'Обязательное поле'
ORIGINAL_LINK = 'Длинная ссылка'
SHORT = 'Ваш вариант короткой ссылки'


class ShortUrlForm(FlaskForm):
    original_link = URLField(
        ORIGINAL_LINK,
        validators=[DataRequired(message=REQUIRED_FIELD),
                    Length(max=ORIGINAL_LINK_MAX_LENGTH)]
    )
    custom_id = URLField(
        SHORT,
        validators=[
            Length(max=USER_SHORT_MAX_LENGTH),
            Regexp(SHORT_REG_EXPR, message=INVALID_CHAR_IN_SHORT),
            Optional()
        ]
    )
    submit = SubmitField()

    def validate_custom_id(self, field):
        if field.data:
            if field.data in FORBIDDEN_SHORT or URLMap.get(
                field.data
            ):
                raise ValidationError(EXIST_SHORT)


class FilesShortUrlForm(FlaskForm):
    files = MultipleFileField(
        validators=[DataRequired(message=REQUIRED_FIELD)]
    )
    submit = SubmitField()
