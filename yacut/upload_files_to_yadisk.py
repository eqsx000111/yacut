import asyncio
from http import HTTPStatus
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
GET_UPLOAD_URL_ERROR_FULL = f'{GET_UPLOAD_URL_ERROR_TEXT} {{data}}'
UPLOAD_ERROR_FULL = f'{UPLOAD_ERROR_TEXT} {{status}}'
DOWNLOAD_LINK_ERROR_FULL = f'{DOWNLOAD_LINK_ERROR_TEXT} {{link}}'


async def upload_files_to_yandex_disk(files):
    async with aiohttp.ClientSession() as session:

        async def upload_and_get_url(file):
            payload = {'path': f'app:/{file.filename}', 'overwrite': 'True'}
            async with session.get(
                REQUEST_UPLOAD_URL,
                headers=AUTH_HEADERS,
                params=payload
            ) as resp:
                data = await resp.json()
                upload_href = data.get('href')
                if not upload_href:
                    raise YandexDiskError(
                        GET_UPLOAD_URL_ERROR_FULL.format(data=data)
                    )
            file.stream.seek(0)
            async with session.put(
                upload_href,
                data=file.read()
            ) as upload_resp:
                if upload_resp.status not in (
                    HTTPStatus.CREATED,
                    HTTPStatus.ACCEPTED
                ):
                    raise YandexDiskError(
                        UPLOAD_ERROR_FULL.format(status=upload_resp.status)
                    )
                location = upload_resp.headers.get('Location')
                if not location:
                    raise YandexDiskError(NO_LOCATION_HEADER_TEXT)
                location = urllib.parse.unquote(location)
                location = location.replace('/disk', '')
            async with session.get(
                DOWNLOAD_URL,
                headers=AUTH_HEADERS,
                params={'path': location}
            ) as download_resp:
                link = await download_resp.json()
                if 'href' not in link:
                    raise YandexDiskError(
                        DOWNLOAD_LINK_ERROR_FULL.format(link=link)
                    )
                return link['href']
        tasks = [asyncio.create_task(
            upload_and_get_url(file)
        ) for file in files]
        urls = await asyncio.gather(*tasks)
    return urls