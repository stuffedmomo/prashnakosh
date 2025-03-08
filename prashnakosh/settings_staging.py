"""
Staging settings for Prashnakosh.
These settings are for a staging/testing environment that mimics production.
"""

import os
from .settings_production import *  # Import production settings as base

# Use a different staging domain or subdomain
ALLOWED_HOSTS = ['staging.prashnakosh.in', 'test.prashnakosh.in']

# Enable debug for staging
DEBUG = True

# Adjust database name for staging
if 'DB_NAME' in os.environ:
    DATABASES['default']['NAME'] = os.environ.get('STAGING_DB_NAME', os.environ.get('DB_NAME') + '_staging')

# Disable some production settings for staging
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_PRELOAD = False

# Set staging email prefix
EMAIL_SUBJECT_PREFIX = '[Prashnakosh Staging] '

# Adjust logging for staging
for handler in LOGGING['handlers'].values():
    if 'filename' in handler and '/var/log/prashnakosh/' in handler['filename']:
        handler['filename'] = handler['filename'].replace('/var/log/prashnakosh/', '/var/log/prashnakosh/staging/')

# Override Sentry environment
if 'SENTRY_DSN' in os.environ:
    sentry_sdk.init(
        dsn=os.environ.get('SENTRY_DSN'),
        integrations=[DjangoIntegration()],
        traces_sample_rate=0.5,
        send_default_pii=False,
        environment="staging",
    ) 