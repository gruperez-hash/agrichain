import os

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

if load_dotenv:
    load_dotenv()


def _is_supabase_database_url(database_url):
    return (
        'SUPABASE_DATABASE_URL' in os.environ
        or 'supabase' in database_url.lower()
    )


def _normalize_database_url(database_url):
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)

    if database_url.startswith('postgresql://'):
        database_url = database_url.replace('postgresql://', 'postgresql+psycopg://', 1)

    is_postgres = database_url.startswith('postgresql+')
    is_supabase = _is_supabase_database_url(database_url)

    if is_postgres and is_supabase and 'sslmode=' not in database_url.lower():
        separator = '&' if '?' in database_url else '?'
        database_url = f'{database_url}{separator}sslmode=require'

    return database_url


def _engine_options(database_url):
    options = {'pool_pre_ping': True}

    if database_url.startswith('postgresql+psycopg://') and _is_supabase_database_url(database_url):
        options['connect_args'] = {'prepare_threshold': None}

    return options


def _database_url():
    database_url = os.environ.get('SUPABASE_DATABASE_URL') or os.environ.get('DATABASE_URL')

    if database_url:
        return database_url

    if os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('RAILWAY_PROJECT_ID'):
        raise RuntimeError(
            'Missing SUPABASE_DATABASE_URL or DATABASE_URL. '
            'Add your Supabase Postgres connection string in Railway Variables.'
        )

    return 'mysql+pymysql://root:@localhost/agrichain_db'


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'secret123')
    SQLALCHEMY_DATABASE_URI = _normalize_database_url(_database_url())
    SQLALCHEMY_ENGINE_OPTIONS = _engine_options(SQLALCHEMY_DATABASE_URI)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join('Static', 'uploads')
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
    ADMIN_MASTER_KEY = os.environ.get('ADMIN_MASTER_KEY', 'agrichain123')
