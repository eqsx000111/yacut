from flask import flash, redirect, render_template

from . import app
from .error_handlers import InvalidAPIUsage
from .errors import ShortUrlError
from .forms import FilesShortUrlForm, ShortUrlForm
from .models import URLMap
from .upload_files_to_yadisk import (
    upload_files_to_yandex_disk,
)

UPLOAD_ERROR_TEXT = 'Ошибка при загрузке файлов:'
CREATE_SHORT_UPLOAD_ERROR_TEXT = 'Ошибка при создании короткой ссылки:'
UNEXPECTED_ERROR = 'Непредвиденная ошибка при создании короткой ссылки:'


@app.route('/', methods=['GET', 'POST'])
def url_shortener():
    form = ShortUrlForm()
    if not form.validate_on_submit():
        return render_template('index.html', form=form)
    try:
        url_map = URLMap.create(
            original=form.original_link.data,
            short=form.custom_id.data,
            validate_short=True,
            validate_original=True
        )
    except ShortUrlError as e:
        raise InvalidAPIUsage(str(e))
    return render_template(
        'index.html',
        form=form,
        short_url=url_map.get_short_url()
    )


@app.route('/files', methods=['GET', 'POST'])
async def files_shortener():
    form = FilesShortUrlForm()
    if not form.validate_on_submit():
        return render_template('files_shortener.html', form=form)
    try:
        urls = await upload_files_to_yandex_disk(form.files.data)
    except Exception:
        flash(UPLOAD_ERROR_TEXT, 'danger')
        return render_template('files_shortener.html', form=form)
    try:
        files_info = [
            {
                'name': file_obj.filename,
                'short_url': URLMap.create(
                    original=original_url,
                    short=None,
                    validate_short=True,
                    validate_original=True
                ).get_short_url()
            }
            for file_obj, original_url in zip(form.files.data, urls)
        ]
    except ShortUrlError as e:
        raise InvalidAPIUsage(str(e))
    return render_template(
        'files_shortener.html',
        form=form,
        files_info=files_info
    )


@app.route('/<short>')
def redirect_view(short):
    return redirect(URLMap.get(short=short, raise_404=True).original)
