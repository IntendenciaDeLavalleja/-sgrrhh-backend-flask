import os
from dotenv import load_dotenv
from .redis_utils import build_redis_url_from_env

load_dotenv()


def _parse_list_from_env(name: str) -> list[str]:
    raw = os.environ.get(name)
    if raw:
        return [item.strip() for item in raw.split(',') if item.strip()]
    return []


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get('DATABASE_URL')
        or os.environ.get('DATABASE_URI')
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Mail Config
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') == 'True'
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL') == 'True'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')

    # Frontend URL for email links
    FRONTEND_URL = os.environ.get('FRONTEND_URL') or 'http://localhost:5173'

    # Redis Settings
    REDIS_HOST = os.environ.get('REDIS_HOST', 'redis')
    REDIS_PORT = os.environ.get('REDIS_PORT', '6379')
    REDIS_DB = os.environ.get('REDIS_DB', '0')
    REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD')
    REDIS_URL = build_redis_url_from_env(os.environ)

    # Flask-Limiter
    RATELIMIT_STORAGE_URI = os.environ.get(
        'RATELIMIT_STORAGE_URI',
        'memory://',
    )

    # JWT Settings (24h expiry)
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or os.environ.get('SECRET_KEY') or 'jwt-secret-change-me'
    JWT_ACCESS_TOKEN_EXPIRES = 86400  # 24 horas en segundos

    CORS_ALLOWED_ORIGINS = _parse_list_from_env('CORS_ORIGINS')

    # MinIO / S3-compatible object storage
    MINIO_ENDPOINT = os.environ.get('MINIO_ENDPOINT', 'localhost:9000')
    MINIO_ACCESS_KEY = os.environ.get('MINIO_ACCESS_KEY', '')
    MINIO_SECRET_KEY = os.environ.get('MINIO_SECRET_KEY', '')
    MINIO_SECURE = os.environ.get('MINIO_SECURE', 'False').lower() == 'true'
    MINIO_BUCKET_NAME = os.environ.get('MINIO_BUCKET_NAME', 'gestion-recursos-humanos-uploads')

    PROPAGATE_EXCEPTIONS = False
    TRAP_HTTP_EXCEPTIONS = False

    _is_sqlite = bool(
        SQLALCHEMY_DATABASE_URI
        and SQLALCHEMY_DATABASE_URI.startswith('sqlite')
    )
    if _is_sqlite:
        SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_pre_ping': True,
        }
    else:
        SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_pre_ping': True,
            'pool_recycle': int(os.environ.get('DB_POOL_RECYCLE', '1800')),
            'pool_timeout': int(os.environ.get('DB_POOL_TIMEOUT', '30')),
            'pool_size': int(os.environ.get('DB_POOL_SIZE', '10')),
            'max_overflow': int(os.environ.get('DB_MAX_OVERFLOW', '20')),
        }
