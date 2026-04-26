from .base import *
import os
from dotenv import load_dotenv

load_dotenv()

INSTALLED_APPS += ['django_extensions']

DEBUG = True

ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

# =========================
# SECRET KEY (desde .env)
# =========================
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")

# =========================
# DATABASE
# =========================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'pcidb'),
        'USER': os.getenv('DB_USER', 'django_user'),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

STATICFILES_DIRS = [BASE_DIR / "users" / "static"]

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
