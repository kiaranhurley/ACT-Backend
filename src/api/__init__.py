# src/api/__init__.py

def init_app(app):
    # Import blueprints
    from . import auth, crypto, stocks, users

    # Register blueprints
    app.register_blueprint(auth.bp)
    app.register_blueprint(crypto.bp)
    app.register_blueprint(stocks.bp)
    app.register_blueprint(users.bp)
    
    return app