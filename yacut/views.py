import random
import string

from flask import flash, redirect, render_template, url_for

from . import app, db
from .constants import FORBIDDEN_LINK, LENGTH
from .forms import FilesShortUrlForm, ShortUrlForm
from .models import URLMap
from .upload_files_to_yadisk import (
    get_download_link,
    upload_files_to_yandex_disk
)


@app.route('/', methods=['GET', 'POST'])
def url_shortener():
    form = ShortUrlForm()
    short_url = None

    if form.validate_on_submit():
        custom_link = form.custom_id.data
        full_link = form.original_link.data
        if custom_link:
            if (
                FORBIDDEN_LINK in custom_link or
                URLMap.query.filter_by(short=custom_link).first()
            ):
                flash('Предложенный вариант короткой ссылки уже существует.')
                return render_template('url_shortener.html', form=form)
        else:
            while True:
                custom_link = generate_short_url()
                if not URLMap.query.filter_by(short=custom_link).first():
                    break
        link = URLMap(original=full_link, short=custom_link)
        db.session.add(link)
        db.session.commit()
        short_url = url_for(
            'redirect_view',
            short=custom_link,
            _external=True
        )
        return render_template(
            'url_shortener.html',
            form=form,
            short_url=short_url
        )
    return render_template('url_shortener.html', form=form)


def generate_short_url():
    return ''.join(
        random.choice(
            string.ascii_letters + string.digits
        ) for _ in range(LENGTH)
    )


@app.route('/files', methods=['GET', 'POST'])
async def files_shortener():
    form = FilesShortUrlForm()
    if form.validate_on_submit():
        urls = await upload_files_to_yandex_disk(form.files.data)
        files_info = []
        for file_obj, original_url in zip(form.files.data, urls):
            download_url = await get_download_link(original_url)
            short_for_file = generate_short_url()
            file_entry = URLMap(
                original=download_url,
                short=short_for_file
            )
            db.session.add(file_entry)
            short_url = url_for(
                'redirect_view',
                short=short_for_file,
                _external=True
            )
            files_info.append({
                'name': file_obj.filename,
                'short_url': short_url
            })
        db.session.commit()
        return render_template(
            'files_shortener.html',
            form=form,
            files_info=files_info
        )
    return render_template('files_shortener.html', form=form)


@app.route('/<short>')
def redirect_view(short):
    file_entry = URLMap.query.filter_by(short=short).first_or_404()
    return redirect(file_entry.original)
