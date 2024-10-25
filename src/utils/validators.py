# src/utils/validators.py
from functools import wraps
from typing import Dict, Optional

import jwt
from firebase_admin import auth
from flask import current_app, jsonify, request


def token_required(f):
    """Decorator to protect routes with JWT authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Get token from headers
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                return jsonify({
                    'message': 'Invalid token format',
                    'status': 'error'
                }), 401
        
        if not token:
            return jsonify({
                'message': 'Token is missing',
                'status': 'error'
            }), 401
        
        try:
            # Verify JWT token
            payload = jwt.decode(
                token,
                current_app.config['JWT_SECRET_KEY'],
                algorithms=["HS256"]
            )
            current_user = payload['sub']
            
            # Verify user exists in Firebase
            try:
                user = auth.get_user(current_user)
                if user.disabled:
                    return jsonify({
                        'message': 'User account is disabled',
                        'status': 'error'
                    }), 401
            except auth.UserNotFoundError:
                return jsonify({
                    'message': 'User not found',
                    'status': 'error'
                }), 401
            except Exception as e:
                current_app.logger.error(f"Error verifying user: {str(e)}")
                return jsonify({
                    'message': 'Error verifying user',
                    'status': 'error'
                }), 401
            
        except jwt.ExpiredSignatureError:
            return jsonify({
                'message': 'Token has expired',
                'status': 'error'
            }), 401
        except jwt.InvalidTokenError:
            return jsonify({
                'message': 'Invalid token',
                'status': 'error'
            }), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated

def admin_required(f):
    """Decorator to protect routes with admin authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                return jsonify({
                    'message': 'Invalid token format',
                    'status': 'error'
                }), 401
        
        if not token:
            return jsonify({
                'message': 'Token is missing',
                'status': 'error'
            }), 401
        
        try:
            # Verify JWT token
            payload = jwt.decode(
                token,
                current_app.config['JWT_SECRET_KEY'],
                algorithms=["HS256"]
            )
            current_user = payload['sub']
            
            # Verify user is admin in Firebase
            try:
                user = auth.get_user(current_user)
                custom_claims = user.custom_claims or {}
                
                if not custom_claims.get('admin', False):
                    return jsonify({
                        'message': 'Admin privileges required',
                        'status': 'error'
                    }), 403
                    
            except auth.UserNotFoundError:
                return jsonify({
                    'message': 'User not found',
                    'status': 'error'
                }), 401
            except Exception as e:
                current_app.logger.error(f"Error verifying admin: {str(e)}")
                return jsonify({
                    'message': 'Error verifying admin privileges',
                    'status': 'error'
                }), 401
            
        except jwt.ExpiredSignatureError:
            return jsonify({
                'message': 'Token has expired',
                'status': 'error'
            }), 401
        except jwt.InvalidTokenError:
            return jsonify({
                'message': 'Invalid token',
                'status': 'error'
            }), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated

def validate_user_data(data: Dict) -> Optional[str]:
    """
    Validate user registration/update data
    Args:
        data: User data dictionary
    Returns: Error message if validation fails, None otherwise
    """
    if not data:
        return "No data provided"
    
    if 'email' in data:
        email = data['email']
        if not isinstance(email, str) or '@' not in email:
            return "Invalid email format"
    
    if 'password' in data:
        password = data['password']
        if not isinstance(password, str) or len(password) < 6:
            return "Password must be at least 6 characters"
    
    return None

def validate_stock_data(data: Dict) -> Optional[str]:
    """
    Validate stock data
    Args:
        data: Stock data dictionary
    Returns: Error message if validation fails, None otherwise
    """
    if not data:
        return "No data provided"
    
    required_fields = ['symbol', 'name', 'price']
    missing_fields = [field for field in required_fields if field not in data]
    
    if missing_fields:
        return f"Missing required fields: {', '.join(missing_fields)}"
    
    if not isinstance(data['symbol'], str) or not data['symbol']:
        return "Invalid symbol"
    
    if not isinstance(data['name'], str) or not data['name']:
        return "Invalid name"
    
    try:
        price = float(data['price'])
        if price <= 0:
            return "Price must be greater than 0"
    except (ValueError, TypeError):
        return "Invalid price"
    
    return None