import asyncio
import os
import urllib

import aiohttp
from dotenv import load_dotenv

from . import app
from .error_handlers import YandexDiskError

API_HOST = app.config['API_HOST']
API_VERSION = app.config['API_VERSION']
REQUEST_UPLOAD_URL = f'{API_HOST}{API_VERSION}/disk/resources/upload'
DOWNLOAD_URL = f'{API_HOST}{API_VERSION}/disk/resources/download'
load_dotenv()
AUTH_HEADERS = {'Authorization': f'OAuth {os.getenv("DISK_TOKEN")}'}

GET_UPLOAD_URL_ERROR_TEXT = 'Ошибка получения upload URL: '
UPLOAD_ERROR_TEXT = 'Ошибка загрузки: '
NO_LOCATION_HEADER_TEXT = 'Нет заголовка Location в ответе при загрузке файла!'
DOWNLOAD_LINK_ERROR_TEXT = 'Ошибка получения download link: '


async def upload_files_to_yandex_disk(files):
    async with aiohttp.ClientSession() as session:
        tasks = [
            asyncio.create_task(upload_file_and_get_url(session, file))
            for file in files
        ]
        urls = await asyncio.gather(*tasks)
    return urls


async def upload_file_and_get_url(session, file):
    payload = {
        'path': f'app:/{file.filename}',
        'overwrite': 'True'
    }
    async with session.get(
        REQUEST_UPLOAD_URL,
        headers=AUTH_HEADERS,
        params=payload
    ) as response:
        data = await response.json()
        upload_href = data.get('href')
        if not upload_href:
            raise YandexDiskError(f'{GET_UPLOAD_URL_ERROR_TEXT} {data}')
    file.stream.seek(0)
    async with session.put(upload_href, data=file.read()) as upload_resp:
        if upload_resp.status not in (201, 202):
            raise YandexDiskError(f'{UPLOAD_ERROR_TEXT} {upload_resp.status}')
        location = upload_resp.headers.get('Location')
        if not location:
            raise YandexDiskError(
                f'{NO_LOCATION_HEADER_TEXT}'
            )
        location = urllib.parse.unquote(location)
        location = location.replace('/disk', '')
    return location


async def get_download_link(file_url):
    async with aiohttp.ClientSession() as session:
        async with session.get(
            url=DOWNLOAD_URL,
            headers=AUTH_HEADERS,
            params={'path': file_url}
        ) as resp:
            link = await resp.json()
            if 'href' not in link:
                raise YandexDiskError(f'{DOWNLOAD_LINK_ERROR_TEXT} {link}')
            return link['href']
