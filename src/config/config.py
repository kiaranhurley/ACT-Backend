import os
from datetime import timedelta

from dotenv import load_dotenv


class Config:
    """Application configuration class"""
    def __init__(self):
        # Load environment variables from .env file
        load_dotenv()

        # Flask Configuration
        self.SECRET_KEY = os.getenv('SECRET_KEY', os.urandom(24).hex())
        self.DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
        self.HOST = os.getenv('FLASK_HOST', '127.0.0.1')
        self.PORT = int(os.getenv('FLASK_PORT', 5000))
        
        # API Configuration
        self.API_VERSION = '1.0'
        self.API_TITLE = 'ACT Backend API'
        self.API_PREFIX = '/api/v1'
        
        # CORS Configuration
        self.CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')
        
        # JWT Configuration
        self.JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-jwt-secret-key')
        self.JWT_ACCESS_TOKEN_EXPIRES = timedelta(
            seconds=int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 3600))
        )  # Default 1 hour
        self.JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)  # 30 days
        self.JWT_ALGORITHM = 'HS256'
        
        # Firebase Configuration
        self.FIREBASE_CREDS_PATH = os.getenv(
            'FIREBASE_CREDS_PATH', 
            os.path.join('credentials', 'firebase_credentials.json')
        )
        
        # Database Configuration
        self.SQLALCHEMY_DATABASE_URI = os.getenv(
            'DATABASE_URL',
            'sqlite:///app.db'
        )
        self.SQLALCHEMY_TRACK_MODIFICATIONS = False
        
        # File Upload Configuration
        self.UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
        self.MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
        self.ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}
        
        # Security Configuration
        self.BCRYPT_LOG_ROUNDS = 13
        self.PASSWORD_SALT = os.getenv('PASSWORD_SALT', 'your-password-salt')
        
        # Email Configuration
        self.MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
        self.MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
        self.MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
        self.MAIL_USERNAME = os.getenv('MAIL_USERNAME')
        self.MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
        self.MAIL_DEFAULT_SENDER = os.getenv(
            'MAIL_DEFAULT_SENDER',
            'noreply@actapp.com'
        )
        
        # Cache Configuration
        self.CACHE_TYPE = os.getenv('CACHE_TYPE', 'simple')
        self.CACHE_DEFAULT_TIMEOUT = int(os.getenv('CACHE_DEFAULT_TIMEOUT', 300))
        
        # Session Configuration
        self.SESSION_TYPE = 'filesystem'
        self.PERMANENT_SESSION_LIFETIME = timedelta(days=31)
        
        # Logging Configuration
        self.LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
        self.LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        self.LOG_FILE = os.getenv('LOG_FILE', 'logs/app.log')
        
        # API Rate Limiting
        self.RATELIMIT_DEFAULT = "200 per day;50 per hour;1 per second"
        self.RATELIMIT_STORAGE_URL = "memory://"
        
        # Development-specific Configuration
        if self.DEBUG:
            self.TESTING = True
            self.TEMPLATES_AUTO_RELOAD = True
            self.EXPLAIN_TEMPLATE_LOADING = True
            self.SQLALCHEMY_ECHO = True
            
    def init_app(self, app):
        """Initialize application configuration"""
        # Ensure upload folder exists
        os.makedirs(self.UPLOAD_FOLDER, exist_ok=True)
        
        # Ensure logs directory exists
        os.makedirs(os.path.dirname(self.LOG_FILE), exist_ok=True)
        
        # Set Flask configuration from this config object
        for key in [a for a in dir(self) if not a.startswith('_') and a.isupper()]:
            app.config[key] = getattr(self, key)

class DevelopmentConfig(Config):
    """Development configuration"""
    def __init__(self):
        super().__init__()
        self.DEBUG = True
        self.TESTING = True

class ProductionConfig(Config):
    """Production configuration"""
    def __init__(self):
        super().__init__()
        self.DEBUG = False
        self.TESTING = False
        # Add stricter security settings
        self.PERMANENT_SESSION_LIFETIME = timedelta(days=1)
        self.RATELIMIT_DEFAULT = "100 per day;20 per hour;1 per second"
        self.JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=30)

class TestingConfig(Config):
    """Testing configuration"""
    def __init__(self):
        super().__init__()
        self.TESTING = True
        self.DEBUG = True
        self.SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
        self.WTF_CSRF_ENABLED = False

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Get configuration based on environment"""
    env = os.getenv('FLASK_ENV', 'default')
    return config.get(env, config['default'])()