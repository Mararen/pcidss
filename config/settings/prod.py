from .base import *

DEBUG = True

ALLOWED_HOSTS = []

DATABASES['default']['HOST'] = 'localhost'

SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False