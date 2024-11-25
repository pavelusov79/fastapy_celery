from dotenv import load_dotenv
import os

load_dotenv()

DB_HOST = os.environ.get('DB_HOST')
DB_PORT = os.environ.get('DB_PORT')
DB_USER = os.environ.get('DB_USER')
DB_PASS = os.environ.get('DB_PASSWORD')
DB_NAME = os.environ.get('DB_NAME')
SECRET_API_KEY = os.environ.get('SECRET_API_KEY')
DB_PORT_TEST = os.environ.get('DB_PORT_TEST')
DB_HOST_TEST = os.environ.get('DB_HOST_TEST')
DB_NAME_TEST = os.environ.get('DB_NAME_TEST')
DB_USER_TEST = os.environ.get('DB_USER_TEST')
DB_PASSWORD_TEST = os.environ.get('DB_PASSWORD_TEST')
REDIS_HOST = os.environ.get('REDIS_HOST')
REDIS_PORT = os.environ.get('REDIS_PORT')
