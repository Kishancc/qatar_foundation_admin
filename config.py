import os

class Config:
    """Flask configuration for SQLite (local) and PostgreSQL (online)"""
    
    # Secret key for session management
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database URL from environment variable (use for Neon PostgreSQL on Vercel)
    database_url = os.environ.get('DATABASE_URL')
    
    # Set database URI
    if database_url:
        # Online database (PostgreSQL from Neon)
        # Fix postgres:// to postgresql:// if needed
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        SQLALCHEMY_DATABASE_URI = database_url
    else:
        # Local database (SQLite for development)
        SQLALCHEMY_DATABASE_URI = 'sqlite:///admin_portal.db'
    
    # SQLAlchemy settings
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Connection pool settings for better stability
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,      # Test connection before using
        'pool_recycle': 3600,       # Recycle connections after 1 hour
        'echo': False,              # Set to True for SQL debugging
    }