"""
Development settings — SQLite, DEBUG=True, permissive CORS.
"""
from .base import *  # noqa: F401,F403

DEBUG = True
ALLOWED_HOSTS = ['*']

import environ

env = environ.Env()
environ.Env.read_env(BASE_DIR / '.env')

# Use Postgres if DATABASE_URL is set, otherwise fallback to SQLite
DATABASES = {
    'default': env.db('DATABASE_URL', default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}")
}

# Allow the browsable API in dev
REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = (  # noqa: F405
    'rest_framework.renderers.JSONRenderer',
    'rest_framework.renderers.BrowsableAPIRenderer',
)

# CORS — allow everything in dev
CORS_ALLOW_ALL_ORIGINS = True
