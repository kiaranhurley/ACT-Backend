# src/services/firebase_service.py
import os
from pathlib import Path

import firebase_admin
from firebase_admin import auth, credentials, firestore


class FirebaseService:
    """Service for handling Firebase operations"""
    
    def __init__(self, app=None):
        """Initialize Firebase service"""
        self.app = app
        self.db = None
        self.auth = None
        
    def init_app(self, app, config):
        """Initialize Firebase Admin SDK"""
        self.app = app
        if not firebase_admin._apps:
            try:
                # Initialize Firebase Admin SDK
                cred_path = Path(app.root_path) / config.FIREBASE_CREDS_PATH
                if not cred_path.exists():
                    app.logger.error(f"Firebase credentials not found at {cred_path}")
                    return False
                
                cred = credentials.Certificate(str(cred_path))
                firebase_admin.initialize_app(cred)
                self.db = firestore.client()
                
                app.logger.info("Firebase initialized successfully!")
                return True
            except Exception as e:
                app.logger.error(f"Firebase initialization error: {str(e)}")
                return False
        return True
    
    def get_user_by_email(self, email):
        """Get user by email"""
        try:
            return auth.get_user_by_email(email)
        except auth.UserNotFoundError:
            return None
        except Exception as e:
            self.app.logger.error(f"Error getting user by email: {str(e)}")
            return None
    
    def create_user(self, email, password):
        """Create new user"""
        try:
            return auth.create_user(
                email=email,
                password=password
            )
        except Exception as e:
            self.app.logger.error(f"Error creating user: {str(e)}")
            return None
    
    def verify_id_token(self, id_token):
        """Verify Firebase ID token"""
        try:
            return auth.verify_id_token(id_token)
        except Exception as e:
            self.app.logger.error(f"Error verifying token: {str(e)}")
            return None
            
    def delete_user(self, uid):
        """Delete a user"""
        try:
            auth.delete_user(uid)
            return True
        except Exception as e:
            self.app.logger.error(f"Error deleting user: {str(e)}")
            return False
            
    def update_user(self, uid, **kwargs):
        """Update user properties"""
        try:
            auth.update_user(uid, **kwargs)
            return True
        except Exception as e:
            self.app.logger.error(f"Error updating user: {str(e)}")
            return False
            
    def disable_user(self, uid):
        """Disable a user account"""
        try:
            auth.update_user(uid, disabled=True)
            return True
        except Exception as e:
            self.app.logger.error(f"Error disabling user: {str(e)}")
            return False
            
    def enable_user(self, uid):
        """Enable a user account"""
        try:
            auth.update_user(uid, disabled=False)
            return True
        except Exception as e:
            self.app.logger.error(f"Error enabling user: {str(e)}")
            return False
    
    def set_custom_claims(self, uid, claims):
        """Set custom claims for a user"""
        try:
            auth.set_custom_user_claims(uid, claims)
            return True
        except Exception as e:
            self.app.logger.error(f"Error setting custom claims: {str(e)}")
            return False