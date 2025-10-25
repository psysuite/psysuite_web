import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Mail settings
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    
    # Admin settings
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL') or 'alberto.inuggi@gmail.com'
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD') or 'antares'
    
    # Upload settings
    MAX_CONTENT_LENGTH = 200 * 1024 * 1024  # 200MB max file size (for APK uploads)
    UPLOAD_TIMEOUT = 300  # 5 minutes timeout for large uploads
    
    # Session settings
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour
    
    # API settings - reuse SECRET_KEY for API authentication
    PSYSUITE_API_KEY = os.environ.get('PSYSUITE_API_KEY') or SECRET_KEY


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app-dev.db')


class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://user:password@localhost/psysuite_web'


class TestingConfig(Config):
    TESTING = True
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}