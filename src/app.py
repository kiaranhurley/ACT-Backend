import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path

from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix

from config.config import get_config
from services.auth_service import AuthService
from services.firebase_service import FirebaseService
from services.stocks_service import StocksService
from services.users_service import UsersService
from utils.validators import token_required


def setup_logging(app, config):
    """Configure logging"""
    if not app.debug:
        # Ensure log directory exists
        log_dir = Path(app.root_path) / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        # Create file handler
        file_handler = RotatingFileHandler(
            config.LOG_FILE,
            maxBytes=10240000,
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(config.LOG_FORMAT))
        file_handler.setLevel(logging.INFO)
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(config.LOG_FORMAT))
        console_handler.setLevel(logging.DEBUG)
        
        # Add handlers to app logger
        app.logger.addHandler(file_handler)
        app.logger.addHandler(console_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('ACT backend startup')

def register_error_handlers(app):
    """Register error handlers"""
    @app.errorhandler(400)
    def bad_request_error(error):
        return jsonify({
            'error': 'Bad Request',
            'message': str(error),
            'status_code': 400
        }), 400

    @app.errorhandler(401)
    def unauthorized_error(error):
        return jsonify({
            'error': 'Unauthorized',
            'message': 'Authentication is required to access this resource',
            'status_code': 401
        }), 401

    @app.errorhandler(403)
    def forbidden_error(error):
        return jsonify({
            'error': 'Forbidden',
            'message': 'You do not have permission to access this resource',
            'status_code': 403
        }), 403

    @app.errorhandler(404)
    def not_found_error(error):
        return jsonify({
            'error': 'Not Found',
            'message': 'The requested resource was not found on the server',
            'status_code': 404,
            'documentation': f"{request.url_root}api/docs"
        }), 404

    @app.errorhandler(405)
    def method_not_allowed_error(error):
        return jsonify({
            'error': 'Method Not Allowed',
            'message': f'The {request.method} method is not allowed for this endpoint',
            'status_code': 405
        }), 405

    @app.errorhandler(429)
    def ratelimit_error(error):
        return jsonify({
            'error': 'Too Many Requests',
            'message': 'Rate limit exceeded',
            'status_code': 429
        }), 429

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f'Server Error: {str(error)}')
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred',
            'status_code': 500
        }), 500

def register_blueprints(app, services):
    """Register Flask blueprints"""
    try:
        from api.auth import bp as auth_bp
        from api.stocks import bp as stocks_bp
        from api.users import bp as users_bp

        # Pass services to blueprints
        auth_bp.services = services
        stocks_bp.services = services
        users_bp.services = services
        
        # Register blueprints with versioning
        api_prefix = app.config['API_PREFIX']
        blueprints = [
            (auth_bp, '/auth'),
            (stocks_bp, '/stocks'),
            (users_bp, '/users')
        ]
        
        for blueprint, prefix in blueprints:
            app.register_blueprint(blueprint, url_prefix=f"{api_prefix}{prefix}")
            app.logger.info(f"Registered blueprint: {blueprint.name} at {api_prefix}{prefix}")
    
    except Exception as e:
        app.logger.error(f"Error registering blueprints: {str(e)}")
        raise

def create_app(config_class=None):
    """Application factory function"""
    # Initialize Flask app
    app = Flask(__name__)
    
    # Load configuration
    config = config_class or get_config()
    app.config.from_object(config)
    
    # Setup logging
    setup_logging(app, config)
    
    # Initialize extensions
    CORS(app, resources={r"/api/*": {"origins": config.CORS_ORIGINS}})
    app.wsgi_app = ProxyFix(app.wsgi_app)
    
    # Initialize services
    services = {
        'firebase': FirebaseService(),
        'auth': AuthService(),
        'stocks': StocksService(),
        'users': UsersService()
    }
    
    # Initialize Firebase
    firebase_initialized = services['firebase'].init_app(app, config)
    if not firebase_initialized:
        app.logger.error("Failed to initialize Firebase")
    
    # Pass config to services that need it
    services['auth'].config = config
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register blueprints
    register_blueprints(app, services)
    
    # Root route
    @app.route('/')
    def index():
        return jsonify({
            'message': 'Welcome to ACT Backend API',
            'status': 'running',
            'version': config.API_VERSION,
            'firebase_status': 'connected' if firebase_initialized else 'disconnected',
            'documentation': f"{request.url_root}api/docs",
            'endpoints': {
                'auth': f"{request.url_root}{config.API_PREFIX}/auth",
                'stocks': f"{request.url_root}{config.API_PREFIX}/stocks",
                'users': f"{request.url_root}{config.API_PREFIX}/users"
            }
        })
    
    # Health check route
    @app.route('/health')
    def health_check():
        return jsonify({
            'status': 'healthy',
            'version': config.API_VERSION,
            'environment': app.config['FLASK_ENV'],
            'firebase_status': 'connected' if firebase_initialized else 'disconnected',
            'database_status': 'connected',  # Add actual DB check if needed
            'timestamp': datetime.utcnow().isoformat(),
            'uptime': 'unknown'  # Add actual uptime tracking if needed
        })
    
    # Protected test route
    @app.route('/protected')
    @token_required
    def protected(current_user):
        return jsonify({
            'message': 'This is a protected route',
            'user_id': current_user
        })
    
    return app

# Create the application instance
app = create_app()

if __name__ == "__main__":
    config = get_config()
    
    # Print available routes when starting the server
    print("\nAvailable routes:")
    for rule in app.url_map.iter_rules():
        print(f"  * {rule.rule} - {', '.join(rule.methods)}")
    
    # Run the application
    app.run(
        debug=config.DEBUG,
        host=config.HOST,
        port=config.PORT
    )