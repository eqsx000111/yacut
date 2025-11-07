from flask import redirect, render_template

from . import app, db
from .error_handlers import InvalidAPIUsage
from .forms import FilesShortUrlForm, ShortUrlForm
from .models import URLMap
from .upload_files_to_yadisk import (
    get_download_link,
    upload_files_to_yandex_disk,
)

UPLOAD_ERROR_TEXT = 'Ошибка при загрузке файлов:'
CREATE_SHORT_UPLOAD_ERROR_TEXT = 'Ошибка при создании короткой ссылки:'


@app.route('/', methods=['GET', 'POST'])
def url_shortener():
    form = ShortUrlForm()
    if form.validate_on_submit():
        original_url = form.original_link.data
        custom_short = form.custom_id.data
        url_map = URLMap.create(original=original_url, short=custom_short)
        short_url = url_map.get_short_url()
        return render_template(
            'index.html',
            form=form,
            short_url=short_url
        )
    return render_template('index.html', form=form)


@app.route('/files', methods=['GET', 'POST'])
async def files_shortener():
    form = FilesShortUrlForm()
    if form.validate_on_submit():
        try:
            urls = await upload_files_to_yandex_disk(form.files.data)
        except Exception as e:
            raise InvalidAPIUsage(f'{UPLOAD_ERROR_TEXT} {e}')
        try:
            files_info = [
                {
                    'name': file_obj.filename,
                    'short_url': URLMap.create(
                        original=await get_download_link(original_url),
                        short=None
                    ).get_short_url()
                }
                for file_obj, original_url in zip(form.files.data, urls)
            ]
        except Exception as e:
            raise InvalidAPIUsage(f'{CREATE_SHORT_UPLOAD_ERROR_TEXT} {e}')
        db.session.commit()
        return render_template(
            'files_shortener.html',
            form=form,
            files_info=files_info
        )
    return render_template('files_shortener.html', form=form)


@app.route('/<short>')
def redirect_view(short):
    return redirect(URLMap.get_or_404(short=short).original)
