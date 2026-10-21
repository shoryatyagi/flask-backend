"""
MongoDB Database Service
Handles MongoDB connection and collections
"""

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import os
from datetime import datetime


# Global database instance
_client = None
_db = None


def init_database(uri=None, db_name=None):
    """
    Initialize MongoDB connection
    
    Args:
        uri: MongoDB connection URI
        db_name: Database name
    
    Returns:
        MongoDB database instance
    """
    global _client, _db
    
    if _db is not None:
        return _db
    
    if uri is None:
        uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017')
    if db_name is None:
        db_name = os.getenv('MONGODB_DB_NAME', 'quizapp')
    
    try:
        _client = MongoClient(uri)
        # Test connection
        _client.admin.command('ping')
        _db = _client[db_name]
        
        # Create indexes
        _create_indexes()
        
        print(f"✅ Connected to MongoDB: {db_name}")
        return _db
    except ConnectionFailure as e:
        print(f"❌ MongoDB connection failed: {e}")
        raise


def _create_indexes():
    """Create database indexes for better performance"""
    global _db
    
    if _db is None:
        return
    
    try:
        # Room indexes
        _db.rooms.create_index('roomCode', unique=True)
        _db.rooms.create_index('createdAt', expireAfterSeconds=86400)  # Auto-delete after 24 hours
        _db.rooms.create_index('host')
        _db.rooms.create_index('players.socketId')
        
        # Quiz history indexes
        _db.quizHistory.create_index([('userId', 1), ('completedAt', -1)])
        _db.quizHistory.create_index('metadata.source')
        
        # User indexes
        _db.users.create_index('email', unique=True)
        _db.users.create_index('firebaseUid', unique=True, sparse=True)
        
        print("✅ Database indexes created")
    except Exception as e:
        print(f"⚠️ Error creating indexes: {e}")


def get_database():
    """Get the database instance"""
    global _db
    if _db is None:
        init_database()
    return _db


def get_rooms_collection():
    """Get the rooms collection"""
    db = get_database()
    return db.rooms


def get_quiz_history_collection():
    """Get the quiz history collection"""
    db = get_database()
    return db.quizHistory


def get_users_collection():
    """Get the users collection"""
    db = get_database()
    return db.users


def close_database():
    """Close the database connection"""
    global _client, _db
    if _client:
        _client.close()
        _client = None
        _db = None
        print("✅ MongoDB connection closed")


# ============================================
# User Operations
# ============================================

def find_or_create_user(firebase_user):
    """
    Find existing user or create a new one from Firebase data
    
    Args:
        firebase_user: Dict with Firebase user info (uid, email, name, picture)
    
    Returns:
        User document
    """
    users = get_users_collection()
    
    # Try to find by Firebase UID
    user = users.find_one({'firebaseUid': firebase_user['uid']})
    
    if user:
        # Update last login
        users.update_one(
            {'_id': user['_id']},
            {'$set': {'lastLogin': datetime.utcnow()}}
        )
        return user
    
    # Try to find by email
    user = users.find_one({'email': firebase_user['email']})
    
    if user:
        # Link Firebase UID to existing user
        users.update_one(
            {'_id': user['_id']},
            {
                '$set': {
                    'firebaseUid': firebase_user['uid'],
                    'lastLogin': datetime.utcnow()
                }
            }
        )
        return users.find_one({'_id': user['_id']})
    
    # Create new user
    new_user = {
        'firebaseUid': firebase_user['uid'],
        'email': firebase_user['email'],
        'name': firebase_user.get('name', ''),
        'image': firebase_user.get('picture', ''),
        'emailVerified': firebase_user.get('email_verified', False),
        'createdAt': datetime.utcnow(),
        'lastLogin': datetime.utcnow(),
    }
    
    result = users.insert_one(new_user)
    new_user['_id'] = result.inserted_id
    
    return new_user


def get_user_by_email(email):
    """Get user by email"""
    users = get_users_collection()
    return users.find_one({'email': email})


def get_user_by_firebase_uid(firebase_uid):
    """Get user by Firebase UID"""
    users = get_users_collection()
    return users.find_one({'firebaseUid': firebase_uid})


# ============================================
# Quiz History Operations
# ============================================

def save_quiz_history(user_id, quiz_data):
    """
    Save quiz history for a user
    
    Args:
        user_id: User's email or ID
        quiz_data: Quiz result data
    
    Returns:
        Inserted ID
    """
    history = get_quiz_history_collection()
    
    doc = {
        'userId': user_id,
        'userName': quiz_data.get('userName', ''),
        'userEmail': quiz_data.get('userEmail', user_id),
        'userImage': quiz_data.get('userImage', ''),
        'quizTitle': quiz_data.get('quizTitle', 'Untitled Quiz'),
        'mode': quiz_data.get('mode', 'solo'),
        'roomCode': quiz_data.get('roomCode'),
        'score': quiz_data.get('score', 0),
        'totalQuestions': quiz_data.get('totalQuestions', 0),
        'percentage': quiz_data.get('percentage', 0),
        'totalTime': quiz_data.get('totalTime', 0),
        'metadata': quiz_data.get('metadata', {}),
        'questions': quiz_data.get('questions', []),
        'leaderboard': quiz_data.get('leaderboard'),
        'completedAt': datetime.utcnow(),
        'createdAt': datetime.utcnow(),
    }
    
    result = history.insert_one(doc)
    return str(result.inserted_id)


def get_user_quiz_history(user_id, limit=100):
    """
    Get quiz history for a user
    
    Args:
        user_id: User's email or ID
        limit: Maximum number of results
    
    Returns:
        List of quiz history documents
    """
    history = get_quiz_history_collection()
    
    cursor = history.find(
        {'userId': user_id},
        {
            'quizTitle': 1,
            'mode': 1,
            'roomCode': 1,
            'score': 1,
            'totalQuestions': 1,
            'percentage': 1,
            'totalTime': 1,
            'metadata.source': 1,
            'metadata.topic': 1,
            'metadata.difficulty': 1,
            'completedAt': 1,
        }
    ).sort('completedAt', -1).limit(limit)
    
    return list(cursor)


def get_quiz_history_by_id(history_id, user_id):
    """
    Get specific quiz history by ID
    
    Args:
        history_id: Quiz history ID
        user_id: User's email or ID (for authorization)
    
    Returns:
        Quiz history document or None
    """
    from bson import ObjectId
    
    history = get_quiz_history_collection()
    
    try:
        return history.find_one({
            '_id': ObjectId(history_id),
            'userId': user_id
        })
    except Exception:
        return None


# ============================================
# Room Operations
# ============================================

def create_room(room_code, quiz, metadata, host_socket_id, host_name):
    """Create a new quiz room"""
    rooms = get_rooms_collection()
    
    room = {
        'roomCode': room_code,
        'quiz': quiz,
        'metadata': metadata,
        'host': host_socket_id,
        'hostName': host_name,
        'players': [{
            'socketId': host_socket_id,
            'name': host_name,
            'totalTime': 0,
            'answers': []
        }],
        'currentQuestion': -1,
        'started': False,
        'createdAt': datetime.utcnow()
    }
    
    try:
        rooms.insert_one(room)
        return room
    except Exception as e:
        print(f"❌ Error creating room: {e}")
        return None


def get_room(room_code):
    """Get room by code"""
    rooms = get_rooms_collection()
    return rooms.find_one({'roomCode': room_code})


def find_room_by_socket_id(socket_id):
    """Find a room containing a socket across backend instances."""
    rooms = get_rooms_collection()
    return rooms.find_one({
        '$or': [
            {'host': socket_id},
            {'players.socketId': socket_id},
        ]
    })


def update_room(room_code, update_data):
    """Update room data"""
    rooms = get_rooms_collection()
    return rooms.update_one({'roomCode': room_code}, {'$set': update_data})


def delete_room(room_code):
    """Delete a room"""
    rooms = get_rooms_collection()
    return rooms.delete_one({'roomCode': room_code})


def add_player_to_room(room_code, socket_id, player_name):
    """Add a player to a room"""
    rooms = get_rooms_collection()
    
    player = {
        'socketId': socket_id,
        'name': player_name,
        'totalTime': 0,
        'answers': []
    }
    
    return rooms.update_one(
        {'roomCode': room_code},
        {'$push': {'players': player}}
    )


def remove_player_from_room(room_code, player_name):
    """Remove a player from a room by name"""
    rooms = get_rooms_collection()
    return rooms.update_one(
        {'roomCode': room_code},
        {'$pull': {'players': {'name': player_name}}}
    )


def remove_player_by_socket(room_code, socket_id):
    """Remove a player from a room by socket ID"""
    rooms = get_rooms_collection()
    return rooms.update_one(
        {'roomCode': room_code},
        {'$pull': {'players': {'socketId': socket_id}}}
    )
