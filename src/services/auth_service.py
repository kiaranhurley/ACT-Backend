# src/services/auth_service.py
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

import jwt
from firebase_admin import auth
from flask import current_app


class AuthService:
    """Service for handling authentication operations"""
    
    def __init__(self, firebase_service=None, config=None):
        """Initialize auth service"""
        self.firebase_service = firebase_service
        self.config = config
        
    def generate_token(self, user_id: str) -> Optional[str]:
        """Generate JWT token"""
        try:
            payload = {
                'exp': datetime.utcnow() + timedelta(seconds=self.config.JWT_ACCESS_TOKEN_EXPIRES),
                'iat': datetime.utcnow(),
                'sub': user_id
            }
            return jwt.encode(
                payload,
                self.config.JWT_SECRET_KEY,
                algorithm='HS256'
            )
        except Exception as e:
            current_app.logger.error(f"Error generating token: {str(e)}")
            return None
    
    def register_user(self, data: Dict) -> Tuple[Dict, int]:
        """Register a new user"""
        try:
            email = data.get('email')
            password = data.get('password')
            
            # Validate input
            if not email or not password:
                return {
                    'message': 'Missing email or password',
                    'status': 'error'
                }, 400
                
            if len(password) < 6:
                return {
                    'message': 'Password must be at least 6 characters',
                    'status': 'error'
                }, 400
            
            # Check if user exists
            existing_user = self.firebase_service.get_user_by_email(email)
            if existing_user:
                return {
                    'message': 'User already exists',
                    'status': 'error'
                }, 409
            
            # Create user in Firebase
            try:
                user = self.firebase_service.create_user(email, password)
                if not user:
                    raise Exception("Failed to create user")
                
                # Generate token
                token = self.generate_token(user.uid)
                if not token:
                    raise Exception("Failed to generate token")
                
                return {
                    'message': 'User registered successfully',
                    'token': token,
                    'user': {
                        'id': user.uid,
                        'email': user.email,
                        'emailVerified': user.email_verified
                    },
                    'status': 'success'
                }, 201
                
            except Exception as e:
                return {
                    'message': f'Registration failed: {str(e)}',
                    'status': 'error'
                }, 500
            
        except Exception as e:
            current_app.logger.error(f"Error registering user: {str(e)}")
            return {
                'message': f"Error registering user: {str(e)}",
                'status': 'error'
            }, 500
    
    def login_user(self, data: Dict) -> Tuple[Dict, int]:
        """Login user"""
        try:
            email = data.get('email')
            password = data.get('password')
            
            # Validate input
            if not email or not password:
                return {
                    'message': 'Missing email or password',
                    'status': 'error'
                }, 400
            
            try:
                # Get user from Firebase
                user = self.firebase_service.get_user_by_email(email)
                if not user:
                    return {
                        'message': 'Invalid email or password',
                        'status': 'error'
                    }, 401
                
                # Generate custom token
                custom_token = auth.create_custom_token(user.uid)
                
                # Generate session token
                token = self.generate_token(user.uid)
                if not token:
                    raise Exception("Failed to generate token")
                
                return {
                    'message': 'Login successful',
                    'token': token,
                    'user': {
                        'id': user.uid,
                        'email': user.email,
                        'emailVerified': user.email_verified
                    },
                    'status': 'success'
                }, 200
                
            except Exception as e:
                return {
                    'message': 'Invalid email or password',
                    'status': 'error'
                }, 401
            
        except Exception as e:
            current_app.logger.error(f"Error logging in user: {str(e)}")
            return {
                'message': f"Error logging in user: {str(e)}",
                'status': 'error'
            }, 500
    
    def verify_token(self, token: str) -> Tuple[Optional[str], Optional[str]]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(
                token,
                self.config.JWT_SECRET_KEY,
                algorithms=['HS256']
            )
            return payload['sub'], None
        except jwt.ExpiredSignatureError:
            return None, 'Token has expired'
        except jwt.InvalidTokenError:
            return None, 'Invalid token'