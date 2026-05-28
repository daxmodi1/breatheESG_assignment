"""
Production settings — PostgreSQL via DATABASE_URL, strict security.
"""
import os
from .base import *  # noqa: F401,F403

DEBUG = False


def _split_env(name):
    return [value.strip() for value in os.environ.get(name, '').split(',') if value.strip()]


ALLOWED_HOSTS = _split_env('ALLOWED_HOSTS')

render_external_host = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if render_external_host and render_external_host not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(render_external_host)

# PostgreSQL via DATABASE_URL (Render provides this automatically)
import dj_database_url  # noqa: E402

DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL'),
        conn_max_age=600,
    )
}

# Security
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_HSTS_SECONDS = 31_536_000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# CORS — only allow the frontend origin
CORS_ALLOWED_ORIGINS = _split_env('CORS_ALLOWED_ORIGINS')

CSRF_TRUSTED_ORIGINS = [
    f'https://{host}' for host in ALLOWED_HOSTS if host != '*'
]
