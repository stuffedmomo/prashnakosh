"""
Development settings for Prashnakosh.
"""

import os
from .settings import *  # Import base settings

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-v@)^!6w*6sazu3yjxuwzc$(+xsv@dqp75t4+4x_!prm*c@afc2'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Local hosts
ALLOWED_HOSTS = ['prashnakosh.in', 'www.prashnakosh.in', '15.207.165.91', 'localhost', '127.0.0.1']

# Database - Use Supabase for development
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'postgres'),
        'USER': os.environ.get('DB_USER', 'postgres'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', ''),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}

# Mock Google Analytics ID for development
GOOGLE_ANALYTICS_ID = '' 
