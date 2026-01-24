"""
Health Check Routes
"""

from flask import Blueprint, jsonify
import time

health_bp = Blueprint('health', __name__, url_prefix='/api')

_start_time = time.time()


@health_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint
    
    Returns:
        Server health status
    """
    return jsonify({
        'status': 'healthy',
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime()),
        'uptime': time.time() - _start_time
    })
