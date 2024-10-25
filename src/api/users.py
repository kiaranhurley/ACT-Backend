# src/api/users.py
from firebase_admin import auth, firestore
from flask import Blueprint, jsonify, request

from utils.validators import admin_required, token_required, validate_user_data

bp = Blueprint('users', __name__)
db = firestore.client()

@bp.route('/<user_id>', methods=['GET'])
@token_required
def get_user(current_user, user_id):
    """Read user profile"""
    try:
        # Check if user is requesting their own data or is admin
        if current_user != user_id:
            try:
                user = auth.get_user(current_user)
                custom_claims = user.custom_claims or {}
                if not custom_claims.get('admin', False):
                    return jsonify({'error': 'Unauthorized access'}), 403
            except Exception as e:
                return jsonify({'error': 'Error verifying permissions'}), 500
        
        # Get Firebase auth user
        user = auth.get_user(user_id)
        
        # Get additional user data from Firestore
        user_doc = db.collection('users').document(user_id).get()
        user_data = user_doc.to_dict() if user_doc.exists else {}
        
        return jsonify({
            'uid': user.uid,
            'email': user.email,
            'display_name': user.display_name,
            'email_verified': user.email_verified,
            'disabled': user.disabled,
            'created_at': user.user_metadata.creation_timestamp,
            'profile_data': user_data
        })
    except auth.UserNotFoundError:
        return jsonify({'error': 'User not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/<user_id>', methods=['PUT'])
@token_required
def update_user(current_user, user_id):
    """Update user profile"""
    try:
        # Check if user is updating their own data or is admin
        if current_user != user_id:
            try:
                user = auth.get_user(current_user)
                custom_claims = user.custom_claims or {}
                if not custom_claims.get('admin', False):
                    return jsonify({'error': 'Unauthorized access'}), 403
            except Exception as e:
                return jsonify({'error': 'Error verifying permissions'}), 500
        
        data = request.get_json()
        
        # Validate user data
        error = validate_user_data(data)
        if error:
            return jsonify({'error': error}), 400
        
        # Update Firebase auth user
        update_args = {}
        if 'display_name' in data:
            update_args['display_name'] = data['display_name']
        if 'email' in data:
            update_args['email'] = data['email']
        if update_args:
            auth.update_user(user_id, **update_args)
        
        # Update additional user data in Firestore
        user_ref = db.collection('users').document(user_id)
        profile_data = {
            k: v for k, v in data.items() 
            if k not in ['email', 'display_name', 'password']
        }
        if profile_data:
            profile_data['updated_at'] = firestore.SERVER_TIMESTAMP
            user_ref.set(profile_data, merge=True)
        
        return jsonify({
            'message': 'User updated successfully',
            'updated_fields': list(update_args.keys()) + list(profile_data.keys())
        })
    except auth.UserNotFoundError:
        return jsonify({'error': 'User not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/<user_id>', methods=['DELETE'])
@admin_required
def delete_user(current_user, user_id):
    """Delete user account"""
    try:
        # Delete from Firebase Auth
        auth.delete_user(user_id)
        
        # Delete from Firestore
        db.collection('users').document(user_id).delete()
        
        # Delete user's portfolio
        db.collection('portfolios').document(user_id).delete()
        
        return jsonify({
            'message': 'User and associated data deleted successfully',
            'deleted_user_id': user_id
        })
    except auth.UserNotFoundError:
        return jsonify({'error': 'User not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/admin/all', methods=['GET'])
@admin_required
def get_all_users(current_user):
    """Get all users (admin only)"""
    try:
        users_list = []
        page = auth.list_users()
        
        for user in page.users:
            # Get additional user data from Firestore
            user_doc = db.collection('users').document(user.uid).get()
            user_data = user_doc.to_dict() if user_doc.exists else {}
            
            users_list.append({
                'uid': user.uid,
                'email': user.email,
                'display_name': user.display_name,
                'email_verified': user.email_verified,
                'disabled': user.disabled,
                'created_at': user.user_metadata.creation_timestamp,
                'profile_data': user_data
            })
        
        return jsonify({
            'users': users_list,
            'count': len(users_list)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500