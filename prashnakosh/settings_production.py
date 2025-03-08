"""
Production settings for Prashnakosh.
"""

import os
from .settings import *  # Import base settings

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Allowed hosts - Add your domain
ALLOWED_HOSTS = ['prashnakosh.in', 'www.prashnakosh.in']

# Security settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
X_FRAME_OPTIONS = 'DENY'

# Supabase Database configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'postgres'),
        'USER': os.environ.get('DB_USER', 'postgres'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', ''),
        'PORT': os.environ.get('DB_PORT', '5432'),
        'OPTIONS': {
            'sslmode': 'require',
        },
    }
}

# Static and media files settings
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
MEDIA_ROOT = os.path.join(BASE_DIR, 'mediafiles')

# Add Whitenoise for static files serving
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Email configuration for error reporting
ADMINS = [('Admin', os.environ.get('ADMIN_EMAIL', 'admin@prashnakosh.in'))]
EMAIL_HOST = os.environ.get('EMAIL_HOST')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = 'Prashnakosh <no-reply@prashnakosh.in>'
SERVER_EMAIL = 'errors@prashnakosh.in'

# Logging adjustments for production
LOGGING['handlers']['file']['filename'] = '/var/log/prashnakosh/app.log'
LOGGING['handlers']['error_file']['filename'] = '/var/log/prashnakosh/error.log'
LOGGING['handlers']['security_file']['filename'] = '/var/log/prashnakosh/security.log'
LOGGING['handlers']['performance_file']['filename'] = '/var/log/prashnakosh/performance.log'

# Google Analytics settings
GOOGLE_ANALYTICS_ID = os.environ.get('GOOGLE_ANALYTICS_ID', '')

# Enable HTTPS headers handling
# Uncomment if you're using a load balancer or proxy that sets the X-Forwarded-Proto header
# SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Sentry configuration
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

if 'SENTRY_DSN' in os.environ:
    sentry_sdk.init(
        dsn=os.environ.get('SENTRY_DSN'),
        integrations=[DjangoIntegration()],
        traces_sample_rate=0.5,
        send_default_pii=False,
        environment="production",
    ) 