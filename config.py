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

class Config:
    SECRET_KEY = 'secret123'
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:@localhost/agrichain_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join('Static', 'uploads') 
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
    ADMIN_MASTER_KEY = os.environ.get('ADMIN_MASTER_KEY', 'agrichain123')
