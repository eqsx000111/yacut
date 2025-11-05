import asyncio
import os
import urllib

import aiohttp
from dotenv import load_dotenv


API_HOST = 'https://cloud-api.yandex.net/'
API_VERSION = 'v1'
REQUEST_UPLOAD_URL = f'{API_HOST}{API_VERSION}/disk/resources/upload'
DOWNLOAD_URL = f'{API_HOST}{API_VERSION}/disk/resources/download'
load_dotenv()
DISK_TOKEN = os.environ.get('DISK_TOKEN')
AUTH_HEADERS = {'Authorization': f'OAuth {DISK_TOKEN}'}


async def upload_files_to_yandex_disk(files):
    if not files:
        tasks = []
    tasks = []
    async with aiohttp.ClientSession() as session:
        for file in files:
            tasks.append(
                asyncio.create_task(upload_file_and_get_url(session, file))
            )
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
            raise Exception(f'Ошибка получения upload URL: {data}')

    async with session.put(upload_href, data=file.read()) as upload_resp:
        if upload_resp.status not in (201, 202):
            raise Exception(f'Ошибка загрузки: {upload_resp.status}')
        location = upload_resp.headers.get('Location')
        if not location:
            raise Exception(
                'Нет заголовка Location в ответе при загрузке файла!'
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
                raise Exception(f'Ошибка получения download link: {link}')
            return link['href']