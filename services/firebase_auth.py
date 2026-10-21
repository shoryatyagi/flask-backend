"""
Firebase Authentication Service
Handles Firebase Admin SDK initialization and token verification
"""

import os
import json
import firebase_admin
from firebase_admin import credentials, auth
from functools import wraps
from flask import request, jsonify, g


# Initialize Firebase Admin SDK
_firebase_app = None
_firebase_initialized = False


def init_firebase(credentials_path=None):
    """
    Initialize Firebase Admin SDK
    
    Args:
        credentials_path: Path to Firebase service account JSON file
    """
    global _firebase_app, _firebase_initialized
    
    if _firebase_initialized:
        return _firebase_app
    
    # Check if already initialized by firebase_admin
    try:
        existing_app = firebase_admin.get_app()
        if existing_app:
            _firebase_app = existing_app
            _firebase_initialized = True
            print("✅ Firebase Admin SDK already initialized")
            return _firebase_app
    except ValueError:
        # No default app exists, continue with initialization
        pass
    
    # In AWS, inject the service-account JSON from Secrets Manager so the
    # credential file never needs to be included in the container image.
    credentials_json = os.getenv('FIREBASE_CREDENTIALS_JSON')
    if credentials_json:
        try:
            service_account = json.loads(credentials_json)
            cred = credentials.Certificate(service_account)
            _firebase_app = firebase_admin.initialize_app(cred)
            _firebase_initialized = True
            print("✅ Firebase Admin SDK initialized with secret credentials")
            return _firebase_app
        except Exception:
            # Do not log the secret value. Let the app retain its existing
            # fallback behavior when credentials cannot be initialized.
            print("❌ Firebase initialization failed for secret credentials")
            _firebase_initialized = False
            raise

    # Get credentials path from env or use default
    cred_path = credentials_path or os.getenv('FIREBASE_CREDENTIALS_PATH', 'firebase-credentials.json')
    
    # If relative path, make it absolute relative to the flask-backend directory
    if not os.path.isabs(cred_path):
        # Remove ./ prefix if present
        if cred_path.startswith('./'):
            cred_path = cred_path[2:]
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cred_path = os.path.join(base_dir, cred_path)
    
    print(f"🔍 Looking for Firebase credentials at: {cred_path}")
    print(f"📁 File exists: {os.path.exists(cred_path)}")
    
    try:
        if os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            _firebase_app = firebase_admin.initialize_app(cred)
            _firebase_initialized = True
            print("✅ Firebase Admin SDK initialized with credentials file")
        else:
            print(f"⚠️ Firebase credentials file not found at: {cred_path}")
            # Try to initialize with default credentials (for cloud environments)
            try:
                _firebase_app = firebase_admin.initialize_app()
                _firebase_initialized = True
                print("✅ Firebase Admin SDK initialized with default credentials")
            except Exception as e:
                print(f"⚠️ Could not initialize with default credentials: {e}")
                _firebase_initialized = False
        
        return _firebase_app
    except Exception as e:
        print(f"❌ Firebase initialization error: {e}")
        import traceback
        traceback.print_exc()
        _firebase_initialized = False
        raise


def is_firebase_initialized():
    """Check if Firebase is properly initialized"""
    return _firebase_initialized and _firebase_app is not None


def verify_firebase_token(id_token):
    """
    Verify Firebase ID token
    
    Args:
        id_token: Firebase ID token from client
    
    Returns:
        dict: Decoded token with user info, or None if invalid
    """
    if not is_firebase_initialized():
        print("❌ Firebase not initialized, cannot verify token")
        return None
    
    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token
    except auth.InvalidIdTokenError:
        print("❌ Invalid Firebase ID token")
        return None
    except auth.ExpiredIdTokenError:
        print("❌ Firebase ID token expired")
        return None
    except Exception as e:
        print(f"❌ Firebase token verification error: {e}")
        return None


def get_user_by_email(email):
    """
    Get Firebase user by email
    
    Args:
        email: User's email address
    
    Returns:
        UserRecord or None
    """
    try:
        user = auth.get_user_by_email(email)
        return user
    except auth.UserNotFoundError:
        return None
    except Exception as e:
        print(f"❌ Error getting user by email: {e}")
        return None


def get_user_by_uid(uid):
    """
    Get Firebase user by UID
    
    Args:
        uid: User's Firebase UID
    
    Returns:
        UserRecord or None
    """
    try:
        user = auth.get_user(uid)
        return user
    except auth.UserNotFoundError:
        return None
    except Exception as e:
        print(f"❌ Error getting user by UID: {e}")
        return None


def firebase_auth_required(f):
    """
    Decorator to require Firebase authentication for a route
    
    Usage:
        @app.route('/protected')
        @firebase_auth_required
        def protected_route():
            user = g.firebase_user
            return jsonify({'user': user})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get token from Authorization header
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
        
        # Store user info in Flask's g object
        g.firebase_user = {
            'uid': decoded_token.get('uid'),
            'email': decoded_token.get('email'),
            'name': decoded_token.get('name', ''),
            'picture': decoded_token.get('picture', ''),
            'email_verified': decoded_token.get('email_verified', False),
        }
        
        return f(*args, **kwargs)
    
    return decorated_function


def firebase_auth_optional(f):
    """
    Decorator that optionally checks Firebase authentication
    Sets g.firebase_user to None if not authenticated
    
    Usage:
        @app.route('/optional-auth')
        @firebase_auth_optional
        def optional_auth_route():
            if g.firebase_user:
                return jsonify({'authenticated': True, 'user': g.firebase_user})
            return jsonify({'authenticated': False})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        g.firebase_user = None
        
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization', '')
        
        if auth_header.startswith('Bearer '):
            id_token = auth_header.split('Bearer ')[1]
            
            if id_token:
                decoded_token = verify_firebase_token(id_token)
                
                if decoded_token:
                    g.firebase_user = {
                        'uid': decoded_token.get('uid'),
                        'email': decoded_token.get('email'),
                        'name': decoded_token.get('name', ''),
                        'picture': decoded_token.get('picture', ''),
                        'email_verified': decoded_token.get('email_verified', False),
                    }
        
        return f(*args, **kwargs)
    
    return decorated_function


def create_custom_token(uid, additional_claims=None):
    """
    Create a custom Firebase token for a user
    
    Args:
        uid: User's Firebase UID
        additional_claims: Optional dict of additional claims
    
    Returns:
        str: Custom token
    """
    try:
        token = auth.create_custom_token(uid, additional_claims)
        return token.decode('utf-8') if isinstance(token, bytes) else token
    except Exception as e:
        print(f"❌ Error creating custom token: {e}")
        return None
