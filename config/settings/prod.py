from .base import *
import os
import dj_database_url

DEBUG = False

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")

ALLOWED_HOSTS = [
    "pcicertpro.twilightparadox.com",
    "18.191.160.202",
]

# ── HTTPS ─────────────────────────────────────────────────────
SECURE_PROXY_SSL_HEADER        = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT            = True
SECURE_HSTS_SECONDS            = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD            = True

# ── Sesión segura ─────────────────────────────────────────────
SESSION_COOKIE_AGE      = 900    # 15 minutos
SESSION_COOKIE_SECURE   = True   # Solo HTTPS
SESSION_COOKIE_HTTPONLY = True   # Inaccesible por JS
SESSION_COOKIE_SAMESITE = "Lax"  # Protección CSRF básica
SESSION_SAVE_EVERY_REQUEST = True

# ── CSRF ──────────────────────────────────────────────────────
CSRF_COOKIE_SECURE      = True
CSRF_COOKIE_HTTPONLY    = True
CSRF_TRUSTED_ORIGINS    = ['https://pcicertpro.twilightparadox.com']

# ── Archivos estáticos ────────────────────────────────────────
STATIC_URL  = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# ── Base de datos ─────────────────────────────────────────────
DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get("DATABASE_URL"),
        conn_max_age=600,  
        ssl_require=True
    )
}

# ── reCAPTCHA ─────────────────────────────────────────────────
RECAPTCHA_PUBLIC_KEY  = os.getenv('RECAPTCHA_PUBLIC_KEY')
RECAPTCHA_PRIVATE_KEY = os.getenv('RECAPTCHA_PRIVATE_KEY')

# ── Email Resend ──────────────────────────────────────────────
EMAIL_BACKEND       = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST          = 'smtp.resend.com'
EMAIL_PORT          = 587
EMAIL_USE_TLS       = True
EMAIL_HOST_USER     = 'resend'
EMAIL_HOST_PASSWORD = os.environ.get('RESEND_API_KEY')
DEFAULT_FROM_EMAIL  = 'onboarding@resend.dev'