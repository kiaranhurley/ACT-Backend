# src/api/auth.py
from firebase_admin import auth, firestore
from flask import Blueprint, jsonify, request

from utils.validators import token_required, validate_user_data

bp = Blueprint('auth', __name__)

@bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        
        # Validate user data
        error = validate_user_data(data)
        if error:
            return jsonify({'error': error}), 400
        
        # Create user in Firebase
        user = auth.create_user(
            email=data['email'],
            password=data['password']
        )
        
        # Create user profile in Firestore
        db = firestore.client()
        db.collection('users').document(user.uid).set({
            'email': data['email'],
            'created_at': firestore.SERVER_TIMESTAMP,
            'updated_at': firestore.SERVER_TIMESTAMP,
            'role': 'user'
        })
        
        return jsonify({
            'message': 'User created successfully',
            'uid': user.uid,
            'email': user.email
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@bp.route('/login', methods=['POST'])
def login():
    """Login user"""
    try:
        data = request.get_json()
        
        # Validate user data
        error = validate_user_data(data)
        if error:
            return jsonify({'error': error}), 400
        
        # Get user from Firebase
        user = auth.get_user_by_email(data['email'])
        
        # Create custom token
        custom_token = auth.create_custom_token(user.uid)
        
        return jsonify({
            'message': 'Login successful',
            'uid': user.uid,
            'email': user.email,
            'token': custom_token.decode()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 401

@bp.route('/profile', methods=['GET'])
@token_required
def get_profile(current_user):
    """Get current user profile"""
    try:
        user = auth.get_user(current_user)
        
        # Get additional profile data from Firestore
        db = firestore.client()
        profile_doc = db.collection('users').document(current_user).get()
        profile_data = profile_doc.to_dict() if profile_doc.exists else {}
        
        return jsonify({
            'uid': user.uid,
            'email': user.email,
            'email_verified': user.email_verified,
            'created_at': user.user_metadata.creation_timestamp,
            'profile': profile_data
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400