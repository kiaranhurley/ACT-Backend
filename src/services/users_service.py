# src/services/users_service.py
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from firebase_admin import auth, firestore
from flask import current_app


class UsersService:
    """Service for handling user-related operations"""
    
    def __init__(self, firebase_service=None):
        """Initialize users service"""
        self.firebase_service = firebase_service
        self.db = firebase_service.db if firebase_service else None
    
    def get_all_users(self) -> Tuple[Dict, int]:
        """Get all users"""
        try:
            if not self.db:
                current_app.logger.error("Database connection not initialized")
                return {
                    'message': 'Database connection error',
                    'status': 'error'
                }, 500
            
            # Get users from Firebase Auth
            users_list = []
            page = auth.list_users()
            
            for user in page.users:
                # Get additional user data from Firestore if it exists
                user_data = {
                    'uid': user.uid,
                    'email': user.email,
                    'emailVerified': user.email_verified,
                    'disabled': user.disabled,
                    'createdAt': user.user_metadata.creation_timestamp,
                    'lastSignIn': user.user_metadata.last_sign_in_timestamp
                }
                
                # Try to get additional user data from Firestore
                try:
                    doc = self.db.collection('users').document(user.uid).get()
                    if doc.exists:
                        user_data.update(doc.to_dict())
                except Exception as e:
                    current_app.logger.warning(f"Error fetching Firestore data for user {user.uid}: {str(e)}")
                
                users_list.append(user_data)
            
            return {
                'users': users_list,
                'count': len(users_list),
                'status': 'success'
            }, 200
            
        except Exception as e:
            current_app.logger.error(f"Error fetching users: {str(e)}")
            return {
                'message': f"Error fetching users: {str(e)}",
                'status': 'error'
            }, 500
    
    def get_user_by_id(self, user_id: str) -> Tuple[Dict, int]:
        """
        Get user by ID
        Args:
            user_id: Firebase user ID
        Returns: Tuple of (response_dict, status_code)
        """
        try:
            if not self.db:
                current_app.logger.error("Database connection not initialized")
                return {
                    'message': 'Database connection error',
                    'status': 'error'
                }, 500
            
            # Get user from Firebase Auth
            try:
                user = auth.get_user(user_id)
            except auth.UserNotFoundError:
                return {
                    'message': f'User with ID {user_id} not found',
                    'status': 'error'
                }, 404
            
            # Create base user data
            user_data = {
                'uid': user.uid,
                'email': user.email,
                'emailVerified': user.email_verified,
                'disabled': user.disabled,
                'createdAt': user.user_metadata.creation_timestamp,
                'lastSignIn': user.user_metadata.last_sign_in_timestamp
            }
            
            # Try to get additional user data from Firestore
            try:
                doc = self.db.collection('users').document(user_id).get()
                if doc.exists:
                    user_data.update(doc.to_dict())
            except Exception as e:
                current_app.logger.warning(f"Error fetching Firestore data for user {user_id}: {str(e)}")
            
            return {
                'user': user_data,
                'status': 'success'
            }, 200
            
        except Exception as e:
            current_app.logger.error(f"Error fetching user {user_id}: {str(e)}")
            return {
                'message': f"Error fetching user: {str(e)}",
                'status': 'error'
            }, 500
    
    def update_user(self, user_id: str, data: Dict) -> Tuple[Dict, int]:
        """
        Update user profile
        Args:
            user_id: Firebase user ID
            data: Updated user data
        Returns: Tuple of (response_dict, status_code)
        """
        try:
            if not self.db:
                current_app.logger.error("Database connection not initialized")
                return {
                    'message': 'Database connection error',
                    'status': 'error'
                }, 500
            
            # Check if user exists
            try:
                user = auth.get_user(user_id)
            except auth.UserNotFoundError:
                return {
                    'message': f'User with ID {user_id} not found',
                    'status': 'error'
                }, 404
            
            # Update user data in Firestore
            try:
                # Add timestamp
                data['updated_at'] = datetime.utcnow()
                
                user_ref = self.db.collection('users').document(user_id)
                user_ref.set(data, merge=True)
                
                # Get updated user data
                updated_data = user_ref.get().to_dict()
                
                return {
                    'message': 'User updated successfully',
                    'user': {
                        'uid': user_id,
                        'email': user.email,
                        'emailVerified': user.email_verified,
                        **updated_data
                    },
                    'status': 'success'
                }, 200
                
            except Exception as e:
                return {
                    'message': f'Error updating user data: {str(e)}',
                    'status': 'error'
                }, 500
            
        except Exception as e:
            current_app.logger.error(f"Error updating user {user_id}: {str(e)}")
            return {
                'message': f"Error updating user: {str(e)}",
                'status': 'error'
            }, 500
    
    def delete_user(self, user_id: str) -> Tuple[Dict, int]:
        """
        Delete user
        Args:
            user_id: Firebase user ID
        Returns: Tuple of (response_dict, status_code)
        """
        try:
            if not self.db:
                current_app.logger.error("Database connection not initialized")
                return {
                    'message': 'Database connection error',
                    'status': 'error'
                }, 500
            
            # Delete user from Firebase Auth
            try:
                auth.delete_user(user_id)
            except auth.UserNotFoundError:
                return {
                    'message': f'User with ID {user_id} not found',
                    'status': 'error'
                }, 404
            
            # Delete user data from Firestore
            try:
                user_ref = self.db.collection('users').document(user_id)
                user_ref.delete()
                
                return {
                    'message': 'User deleted successfully',
                    'status': 'success'
                }, 200
                
            except Exception as e:
                return {
                    'message': f'Error deleting user data: {str(e)}',
                    'status': 'error'
                }, 500
            
        except Exception as e:
            current_app.logger.error(f"Error deleting user {user_id}: {str(e)}")
            return {
                'message': f"Error deleting user: {str(e)}",
                'status': 'error'
            }, 500
    
    def get_user_by_email(self, email: str) -> Tuple[Dict, int]:
        """
        Get user by email
        Args:
            email: User email address
        Returns: Tuple of (response_dict, status_code)
        """
        try:
            if not self.db:
                current_app.logger.error("Database connection not initialized")
                return {
                    'message': 'Database connection error',
                    'status': 'error'
                }, 500
            
            # Get user from Firebase Auth
            try:
                user = auth.get_user_by_email(email)
            except auth.UserNotFoundError:
                return {
                    'message': f'User with email {email} not found',
                    'status': 'error'
                }, 404
            
            # Create base user data
            user_data = {
                'uid': user.uid,
                'email': user.email,
                'emailVerified': user.email_verified,
                'disabled': user.disabled,
                'createdAt': user.user_metadata.creation_timestamp,
                'lastSignIn': user.user_metadata.last_sign_in_timestamp
            }
            
            # Try to get additional user data from Firestore
            try:
                doc = self.db.collection('users').document(user.uid).get()
                if doc.exists:
                    user_data.update(doc.to_dict())
            except Exception as e:
                current_app.logger.warning(f"Error fetching Firestore data for user {user.uid}: {str(e)}")
            
            return {
                'user': user_data,
                'status': 'success'
            }, 200
            
        except Exception as e:
            current_app.logger.error(f"Error fetching user by email {email}: {str(e)}")
            return {
                'message': f"Error fetching user: {str(e)}",
                'status': 'error'
            }, 500