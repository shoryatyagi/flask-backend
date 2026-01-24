"""
Quiz History Routes
Handles quiz history storage and retrieval
"""

from flask import Blueprint, request, jsonify, g
from services.firebase_auth import firebase_auth_required
from services.database import (
    save_quiz_history,
    get_user_quiz_history,
    get_quiz_history_by_id
)
from bson import ObjectId


history_bp = Blueprint('history', __name__, url_prefix='/api')


@history_bp.route('/quiz-history', methods=['POST'])
@firebase_auth_required
def create_quiz_history():
    """
    Save quiz history for authenticated user
    
    Headers:
        Authorization: Bearer <firebase_id_token>
    
    Body:
        quizTitle: Quiz title
        mode: solo or multiplayer
        roomCode: Room code (for multiplayer)
        score: User's score
        totalQuestions: Total number of questions
        percentage: Score percentage
        totalTime: Total time taken
        metadata: Additional quiz metadata
        questions: Array of questions with user answers
        leaderboard: Multiplayer leaderboard (optional)
    
    Returns:
        Created history ID
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
        
        # Add user info to quiz data
        data['userName'] = g.firebase_user.get('name', '')
        data['userEmail'] = g.firebase_user.get('email')
        data['userImage'] = g.firebase_user.get('picture', '')
        
        # Use email as user ID (consistent with frontend)
        user_id = g.firebase_user.get('email')
        
        # Get quiz title from metadata if not provided directly
        if not data.get('quizTitle'):
            data['quizTitle'] = data.get('metadata', {}).get('quizName', 'Untitled Quiz')
        
        # Save to database
        history_id = save_quiz_history(user_id, data)
        
        return jsonify({
            'success': True,
            'historyId': history_id
        })
        
    except Exception as e:
        print(f"❌ Error saving quiz history: {e}")
        return jsonify({'error': 'Failed to save quiz history'}), 500


@history_bp.route('/quiz-history', methods=['GET'])
@firebase_auth_required
def get_quiz_history():
    """
    Get quiz history for authenticated user
    
    Headers:
        Authorization: Bearer <firebase_id_token>
    
    Query params:
        id: Optional specific history ID
    
    Returns:
        Quiz history list or specific history details
    """
    try:
        user_id = g.firebase_user.get('email')
        
        # Check if requesting specific history
        history_id = request.args.get('id')
        
        if history_id:
            # Get specific quiz history with full details
            history = get_quiz_history_by_id(history_id, user_id)
            
            if not history:
                return jsonify({'error': 'Quiz history not found'}), 404
            
            # Convert ObjectId to string
            history['_id'] = str(history['_id'])
            
            return jsonify({
                'success': True,
                'history': history
            })
        else:
            # Get all quiz history for user
            histories = get_user_quiz_history(user_id, limit=100)
            
            # Convert ObjectIds to strings
            for h in histories:
                h['_id'] = str(h['_id'])
            
            return jsonify({
                'success': True,
                'history': histories
            })
            
    except Exception as e:
        print(f"❌ Error fetching quiz history: {e}")
        return jsonify({'error': 'Failed to fetch quiz history'}), 500


@history_bp.route('/quiz-history/<history_id>', methods=['GET'])
@firebase_auth_required
def get_specific_quiz_history(history_id):
    """
    Get specific quiz history by ID
    
    Headers:
        Authorization: Bearer <firebase_id_token>
    
    Path params:
        history_id: Quiz history ID
    
    Returns:
        Quiz history details
    """
    try:
        user_id = g.firebase_user.get('email')
        
        history = get_quiz_history_by_id(history_id, user_id)
        
        if not history:
            return jsonify({'error': 'Quiz history not found'}), 404
        
        # Convert ObjectId to string
        history['_id'] = str(history['_id'])
        
        return jsonify({
            'success': True,
            'history': history
        })
        
    except Exception as e:
        print(f"❌ Error fetching quiz history: {e}")
        return jsonify({'error': 'Failed to fetch quiz history'}), 500


@history_bp.route('/quiz-history/<history_id>', methods=['DELETE'])
@firebase_auth_required
def delete_quiz_history(history_id):
    """
    Delete specific quiz history by ID
    
    Headers:
        Authorization: Bearer <firebase_id_token>
    
    Path params:
        history_id: Quiz history ID
    
    Returns:
        Success status
    """
    try:
        from services.database import get_quiz_history_collection
        
        user_id = g.firebase_user.get('email')
        collection = get_quiz_history_collection()
        
        # Delete only if it belongs to the user
        result = collection.delete_one({
            '_id': ObjectId(history_id),
            'userId': user_id
        })
        
        if result.deleted_count == 0:
            return jsonify({'error': 'Quiz history not found'}), 404
        
        return jsonify({
            'success': True,
            'message': 'Quiz history deleted'
        })
        
    except Exception as e:
        print(f"❌ Error deleting quiz history: {e}")
        return jsonify({'error': 'Failed to delete quiz history'}), 500
