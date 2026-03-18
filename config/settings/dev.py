from .base import *
import os

DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'mi_db'),
        'USER': os.environ.get('DB_USER', 'postgres'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}

# =========================
# EMAIL — Imprime los emails en la terminal.
# =========================
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'