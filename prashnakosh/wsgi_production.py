"""
WSGI config for prashnakosh project in production.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prashnakosh.settings_production')
os.environ.setdefault('DJANGO_ENV', 'production')

application = get_wsgi_application() 