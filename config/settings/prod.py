from .base import *
import os

DEBUG = os.environ.get('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = [".onrender.com"]

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# =========================
# EMAIL — producción (Gmail SMTP)
# Variables requeridas en Render → Environment:
#   EMAIL_HOST_USER     tucorreo@gmail.com
#   EMAIL_HOST_PASSWORD App Password de Google (16 caracteres)
# =========================
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
