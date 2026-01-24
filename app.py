"""
Flask Quiz Application - Main Entry Point
A Python Flask backend for the Quiz App with Firebase authentication
"""

import os

# Only use eventlet in production or when explicitly enabled
use_eventlet = os.getenv('USE_EVENTLET', 'false').lower() == 'true'

if use_eventlet:
    import eventlet
    eventlet.monkey_patch()
    ASYNC_MODE = 'eventlet'
else:
    ASYNC_MODE = 'threading'

from flask import Flask, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import configurations
from config import get_config

# Import services
from services.database import init_database, close_database
from services.firebase_auth import init_firebase

# Import routes
from routes.auth import auth_bp
from routes.quiz import quiz_bp
from routes.pdf import pdf_bp
from routes.history import history_bp
from routes.health import health_bp

# Import socket events
from sockets.events import register_socket_events


def create_app(config_class=None):
    """
    Application factory function
    
    Args:
        config_class: Configuration class to use
    
    Returns:
        Flask application instance
    """
    app = Flask(__name__)
    
    # Load configuration
    if config_class is None:
        config_class = get_config()
    
    app.config.from_object(config_class)
    
    # Setup CORS
    allowed_origins = app.config.get('ALLOWED_ORIGINS', ['http://localhost:3000'])
    frontend_url = app.config.get('FRONTEND_URL', 'http://localhost:3000')
    
    if frontend_url not in allowed_origins:
        allowed_origins.append(frontend_url)
    
    CORS(app, 
         origins=allowed_origins,
         supports_credentials=True,
         allow_headers=['Content-Type', 'Authorization'],
         methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
    
    # Initialize SocketIO
    socketio = SocketIO(
        app,
        cors_allowed_origins=allowed_origins if not app.debug else "*",
        async_mode=ASYNC_MODE,
        ping_timeout=60,
        ping_interval=25,
        max_http_buffer_size=1000000,  # 1MB
    )
    
    # Store socketio on app for access in other modules
    app.socketio = socketio
    
    # Initialize database
    try:
        init_database()
        print("✅ Database initialized")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
    
    # Initialize Firebase (optional - will log warning if credentials not found)
    try:
        init_firebase()
        print("✅ Firebase initialized")
    except Exception as e:
        print(f"⚠️ Firebase initialization warning: {e}")
        print("⚠️ Authentication may not work without Firebase credentials")
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(quiz_bp)
    app.register_blueprint(pdf_bp)
    app.register_blueprint(history_bp)
    app.register_blueprint(health_bp)
    
    # Register Socket.IO events
    register_socket_events(socketio)
    
    # Root endpoint
    @app.route('/')
    def index():
        return jsonify({
            'name': 'Quiz App Flask Backend',
            'version': '1.0.0',
            'status': 'running',
            'endpoints': {
                'health': '/api/health',
                'auth': '/api/auth/*',
                'quiz': '/api/generate-quiz',
                'pdf': '/api/process-pdf-chunks',
                'history': '/api/quiz-history'
            }
        })
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error'}), 500
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({'error': 'Bad request'}), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({'error': 'Unauthorized'}), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({'error': 'Forbidden'}), 403
    
    # Cleanup on shutdown
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        pass  # Database connection is handled globally
    
    return app, socketio


# Create application instance
app, socketio = create_app()


if __name__ == '__main__':
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'true').lower() == 'true'
    
    print(f"\n{'='*50}")
    print(f"🚀 Starting Flask Quiz Backend")
    print(f"{'='*50}")
    print(f"📍 Host: {host}")
    print(f"📍 Port: {port}")
    print(f"📍 Debug: {debug}")
    print(f"📍 Environment: {os.getenv('FLASK_ENV', 'development')}")
    print(f"{'='*50}\n")
    
    # Run with SocketIO
    socketio.run(app, host=host, port=port, debug=debug)
