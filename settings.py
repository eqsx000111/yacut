import os


class Config(object):
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URI', 'sqlite:///db.sqlite3')
    SECRET_KEY = os.getenv('SECRET_KEY', 'DEFAULT_SECRET_KEY')
    API_HOST = 'https://cloud-api.yandex.net/'
    API_VERSION = 'v1'


config = Config()
