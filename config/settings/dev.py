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

# reCAPTCHA — claves de prueba para desarrollo local
RECAPTCHA_PUBLIC_KEY  = '6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI'
RECAPTCHA_PRIVATE_KEY = '6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe'
SILENCED_SYSTEM_CHECKS = ['django_recaptcha.recaptcha_test_key_error']

# STATICFILES_DIRS = [BASE_DIR / "users" / "static"]

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
