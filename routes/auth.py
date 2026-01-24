"""
Authentication Routes
Handles Firebase authentication endpoints
"""

from flask import Blueprint, request, jsonify, g
from services.firebase_auth import (
    firebase_auth_required,
    firebase_auth_optional,
    verify_firebase_token
)
from services.database import find_or_create_user, get_user_by_firebase_uid


auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/session', methods=['POST'])
def create_session():
    """
    Create or refresh user session
    Verifies Firebase token and creates/updates user in database
    
    Headers:
        Authorization: Bearer <firebase_id_token>
    
    Returns:
        User session data
    """
    auth_header = request.headers.get('Authorization', '')
    
    if not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Missing or invalid Authorization header'}), 401
    
    id_token = auth_header.split('Bearer ')[1]
    
    if not id_token:
        return jsonify({'error': 'No token provided'}), 401
    
    # Verify token
    decoded_token = verify_firebase_token(id_token)
    
    if not decoded_token:
        return jsonify({'error': 'Invalid or expired token'}), 401
    
    # Create Firebase user dict
    firebase_user = {
        'uid': decoded_token.get('uid'),
        'email': decoded_token.get('email'),
        'name': decoded_token.get('name', ''),
        'picture': decoded_token.get('picture', ''),
        'email_verified': decoded_token.get('email_verified', False),
    }
    
    # Find or create user in database
    try:
        user = find_or_create_user(firebase_user)
        
        return jsonify({
            'success': True,
            'user': {
                'id': str(user.get('_id')),
                'email': user.get('email'),
                'name': user.get('name'),
                'image': user.get('image'),
                'emailVerified': user.get('emailVerified', False),
            }
        })
    except Exception as e:
        print(f"❌ Error creating session: {e}")
        return jsonify({'error': 'Failed to create session'}), 500


@auth_bp.route('/session', methods=['GET'])
@firebase_auth_optional
def get_session():
    """
    Get current user session
    
    Headers:
        Authorization: Bearer <firebase_id_token> (optional)
    
    Returns:
        User session data or null
    """
    if g.firebase_user:
        # Get full user data from database
        user = get_user_by_firebase_uid(g.firebase_user['uid'])
        
        if user:
            return jsonify({
                'authenticated': True,
                'user': {
                    'id': str(user.get('_id')),
                    'email': user.get('email'),
                    'name': user.get('name'),
                    'image': user.get('image'),
                    'emailVerified': user.get('emailVerified', False),
                }
            })
    
    return jsonify({
        'authenticated': False,
        'user': None
    })


@auth_bp.route('/verify', methods=['POST'])
def verify_token():
    """
    Verify Firebase ID token
    
    Body:
        idToken: Firebase ID token
    
    Returns:
        Token validity and user info
    """
    data = request.get_json()
    
    if not data or not data.get('idToken'):
        return jsonify({'error': 'idToken is required'}), 400
    
    decoded_token = verify_firebase_token(data['idToken'])
    
    if not decoded_token:
        return jsonify({
            'valid': False,
            'error': 'Invalid or expired token'
        }), 401
    
    return jsonify({
        'valid': True,
        'user': {
            'uid': decoded_token.get('uid'),
            'email': decoded_token.get('email'),
            'name': decoded_token.get('name', ''),
            'picture': decoded_token.get('picture', ''),
            'emailVerified': decoded_token.get('email_verified', False),
        }
    })


@auth_bp.route('/user', methods=['GET'])
@firebase_auth_required
def get_user():
    """
    Get current authenticated user details
    
    Headers:
        Authorization: Bearer <firebase_id_token>
    
    Returns:
        User details from database
    """
    user = get_user_by_firebase_uid(g.firebase_user['uid'])
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({
        'success': True,
        'user': {
            'id': str(user.get('_id')),
            'firebaseUid': user.get('firebaseUid'),
            'email': user.get('email'),
            'name': user.get('name'),
            'image': user.get('image'),
            'emailVerified': user.get('emailVerified', False),
            'createdAt': user.get('createdAt').isoformat() if user.get('createdAt') else None,
            'lastLogin': user.get('lastLogin').isoformat() if user.get('lastLogin') else None,
        }
    })
