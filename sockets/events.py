"""
Socket.IO Multiplayer Events Handler
Handles real-time multiplayer quiz functionality
"""

from flask_socketio import emit, join_room, leave_room
from services.database import (
    create_room,
    get_room,
    update_room,
    delete_room,
    add_player_to_room,
    remove_player_from_room,
    remove_player_by_socket,
    get_rooms_collection,
    find_room_by_socket_id,
)
from datetime import datetime
import time


# Rate limiting
connection_attempts = {}
MAX_CONNECTIONS_PER_IP = 10
CONNECTION_WINDOW_MS = 60000  # 1 minute


def check_rate_limit(ip):
    """Check if IP has exceeded rate limit"""
    now = time.time() * 1000  # Convert to milliseconds
    attempts = connection_attempts.get(ip, [])
    
    # Clean old attempts
    recent_attempts = [t for t in attempts if now - t < CONNECTION_WINDOW_MS]
    
    if len(recent_attempts) >= MAX_CONNECTIONS_PER_IP:
        return False
    
    recent_attempts.append(now)
    connection_attempts[ip] = recent_attempts
    return True


def register_socket_events(socketio):
    """Register all Socket.IO event handlers"""
    
    @socketio.on('connect')
    def handle_connect():
        from flask import request
        client_ip = request.remote_addr or 'unknown'
        
        if not check_rate_limit(client_ip):
            print(f"⚠️ Rate limit exceeded for IP: {client_ip}")
            return False
        
        print(f"User connected: {request.sid}")
        return True
    
    @socketio.on('disconnect')
    def handle_disconnect():
        from flask import request
        sid = request.sid
        print(f"User disconnected: {sid}")
        
        try:
            room = find_room_by_socket_id(sid)
            if not room:
                return
            room_code = room['roomCode']
            
            if room:
                player = next((p for p in room['players'] if p['socketId'] == sid), None)
                
                if room['host'] == sid:
                    # Host disconnected - notify and delete room
                    emit('host-disconnected', room=room_code)
                    delete_room(room_code)
                    print(f"🗑️ Room {room_code} closed (host disconnected)")
                elif player:
                    # Regular player disconnected
                    remove_player_by_socket(room_code, sid)
                    
                    updated_room = get_room(room_code)
                    if updated_room:
                        emit('player-left', {
                            'playerName': player['name'],
                            'totalPlayers': len(updated_room['players'])
                        }, room=room_code)
                        
                        # Delete room if empty
                        if len(updated_room['players']) == 0:
                            delete_room(room_code)
                            print(f"🗑️ Room {room_code} deleted (all players left)")
            
        except Exception as e:
            print(f"❌ Error handling disconnect: {e}")
    
    @socketio.on('create-room')
    def handle_create_room(data):
        from flask import request
        sid = request.sid
        
        try:
            room_code = data.get('roomCode')
            quiz = data.get('quiz')
            metadata = data.get('metadata', {})
            host_name = data.get('hostName')
            
            # Check if room already exists
            existing_room = get_room(room_code)
            if existing_room:
                emit('error', {'message': 'Room code already exists'})
                return
            
            # Create room in database
            room = create_room(room_code, quiz, metadata, sid, host_name)
            
            if not room:
                emit('error', {'message': 'Failed to create room'})
                return
            
            join_room(room_code)
            
            # Send room-created with initial players list
            player_list = [p['name'] for p in room['players']]
            emit('room-created', {
                'roomCode': room_code,
                'players': player_list
            })
            
            print(f"Room created: {room_code}")
            
        except Exception as e:
            print(f"❌ Error creating room: {e}")
            emit('error', {'message': 'Failed to create room'})
    
    @socketio.on('join-room')
    def handle_join_room(data):
        from flask import request
        sid = request.sid
        
        try:
            room_code = data.get('roomCode')
            player_name = data.get('playerName')
            
            print(f"🔄 Player \"{player_name}\" attempting to join room: {room_code}")
            
            room = get_room(room_code)
            
            if not room:
                print(f"❌ Room not found: {room_code}")
                emit('error', {'message': 'Room not found'})
                return
            
            if room.get('started'):
                print(f"❌ Room {room_code} already started")
                emit('error', {'message': 'Quiz already started'})
                return
            
            # Add player to room
            add_player_to_room(room_code, sid, player_name)
            
            join_room(room_code)
            
            updated_room = get_room(room_code)
            player_list = [p['name'] for p in updated_room['players']]
            
            print(f"✅ {player_name} joined room: {room_code}. Players: {player_list}")
            
            # Emit to the joining player
            emit('joined-room', {
                'roomCode': room_code,
                'players': player_list
            })
            
            # Notify all other players in the room
            emit('player-joined', {
                'playerName': player_name,
                'players': player_list,
                'totalPlayers': len(updated_room['players'])
            }, room=room_code, include_self=False)
            
        except Exception as e:
            print(f"❌ Error joining room: {e}")
            emit('error', {'message': 'Failed to join room'})
    
    @socketio.on('remove-player')
    def handle_remove_player(data):
        from flask import request
        sid = request.sid
        
        try:
            room_code = data.get('roomCode')
            player_name = data.get('playerName')
            
            print(f"🚫 Host requesting to remove player: {player_name} from room: {room_code}")
            
            room = get_room(room_code)
            
            if not room:
                emit('error', {'message': 'Room not found'})
                return
            
            # Verify requester is host
            if room['host'] != sid:
                emit('error', {'message': 'Only host can remove players'})
                return
            
            # Find player to remove
            player_to_remove = next((p for p in room['players'] if p['name'] == player_name), None)
            
            if not player_to_remove:
                emit('error', {'message': 'Player not found in room'})
                return
            
            # Prevent host from removing themselves
            if player_to_remove['socketId'] == sid:
                emit('error', {'message': 'Host cannot remove themselves'})
                return
            
            # Remove player from database
            remove_player_from_room(room_code, player_name)
            
            # Get updated room
            updated_room = get_room(room_code)
            player_list = [p['name'] for p in updated_room['players']]
            
            # Notify the kicked player
            emit('player-kicked', {
                'message': 'You have been removed from the quiz by the host'
            }, room=player_to_remove['socketId'])
            
            # Remove from socket room
            leave_room(room_code, sid=player_to_remove['socketId'])
            
            # Notify remaining players
            emit('player-removed', {
                'playerName': player_name,
                'players': player_list,
                'totalPlayers': len(updated_room['players'])
            }, room=room_code)
            
            print(f"✅ Removed {player_name} from room {room_code}. Remaining players: {player_list}")
            
        except Exception as e:
            print(f"❌ Error removing player: {e}")
            emit('error', {'message': 'Failed to remove player'})
    
    @socketio.on('start-quiz')
    def handle_start_quiz(data):
        from flask import request
        sid = request.sid
        
        try:
            room_code = data.get('roomCode')
            
            room = get_room(room_code)
            
            if not room or room['host'] != sid:
                emit('error', {'message': 'Only host can start the quiz'})
                return
            
            # Update room state
            rooms = get_rooms_collection()
            rooms.update_one(
                {'roomCode': room_code},
                {'$set': {'started': True, 'currentQuestion': 0}}
            )
            
            emit('quiz-started', {
                'currentQuestion': 0,
                'question': room['quiz'][0],
                'totalQuestions': len(room['quiz']),
                'quiz': room['quiz'],
                'metadata': room.get('metadata', {})
            }, room=room_code)
            
            print(f"Quiz started in room: {room_code}")
            
        except Exception as e:
            print(f"❌ Error starting quiz: {e}")
            emit('error', {'message': 'Failed to start quiz'})
    
    @socketio.on('submit-answer')
    def handle_submit_answer(data):
        from flask import request
        sid = request.sid
        
        try:
            room_code = data.get('roomCode')
            question_index = data.get('questionIndex')
            question_text = data.get('questionText')
            answer_index = data.get('answerIndex')
            selected_answer_text = data.get('selectedAnswerText')
            time_spent = data.get('timeSpent', 0)
            
            print(f"📝 Answer submitted - Room: {room_code}, Q{question_index + 1}: \"{selected_answer_text}\"")
            
            room = get_room(room_code)
            
            if not room:
                print(f"❌ Room not found: {room_code}")
                return
            
            # Find player
            player_index = next((i for i, p in enumerate(room['players']) if p['socketId'] == sid), None)
            
            if player_index is None:
                print(f"❌ Player not found in room: {sid}")
                return
            
            # Find question by matching text
            question = next((q for q in room['quiz'] if q['question'] == question_text), None)
            
            if not question:
                print(f"❌ Question not found: \"{question_text}\"")
                return
            
            # Compare answer text
            correct_answer_text = question['options'][question['correctAnswer']]
            is_correct = selected_answer_text == correct_answer_text
            
            print(f"""Player answer check:
            Question: {question_text[:50]}...
            Selected: "{selected_answer_text}"
            Correct: "{correct_answer_text}"
            Result: {"✅ CORRECT" if is_correct else "❌ WRONG"}
            """)
            
            answer = {
                'questionIndex': question_index,
                'questionText': question_text,
                'answerIndex': answer_index,
                'selectedAnswerText': selected_answer_text,
                'correctAnswerText': correct_answer_text,
                'isCorrect': is_correct,
                'timeSpent': time_spent
            }
            
            # Update player's answers
            rooms = get_rooms_collection()
            rooms.update_one(
                {'roomCode': room_code},
                {
                    '$inc': {f'players.{player_index}.totalTime': time_spent},
                    '$push': {f'players.{player_index}.answers': answer}
                }
            )
            
            # Send result back
            emit('answer-submitted', {
                'isCorrect': is_correct,
                'correctAnswer': question['correctAnswer'],
                'explanation': question.get('explanation', '')
            })
            
            # Check if player finished
            updated_room = get_room(room_code)
            player = updated_room['players'][player_index]
            
            print(f"📊 Player progress: {len(player['answers'])}/{len(room['quiz'])} questions")
            
            if len(player['answers']) == len(room['quiz']):
                # Player finished
                correct_answers = sum(1 for a in player['answers'] if a['isCorrect'])
                total_time = player['totalTime']
                avg_time = total_time / len(room['quiz'])
                
                print(f"🏁 Player finished! Score: {correct_answers}/{len(room['quiz'])}")
                
                emit('player-finished', {
                    'correctAnswers': correct_answers,
                    'totalQuestions': len(room['quiz']),
                    'totalTime': total_time,
                    'avgTime': avg_time
                })
                
                # Check if all players finished
                all_finished = all(
                    len(p['answers']) == len(room['quiz']) 
                    for p in updated_room['players']
                )
                
                if all_finished:
                    print(f"🎉 All players finished in room {room_code}!")
                    
                    # Calculate leaderboard
                    leaderboard = []
                    for p in updated_room['players']:
                        correct = sum(1 for a in p['answers'] if a['isCorrect'])
                        p_total_time = p.get('totalTime', 0)
                        p_avg_time = p_total_time / len(room['quiz'])
                        
                        leaderboard.append({
                            'name': p['name'],
                            'correctAnswers': correct,
                            'totalTime': p_total_time,
                            'avgTime': p_avg_time,
                            'answers': p['answers']
                        })
                    
                    # Sort by correct answers (desc) then by time (asc)
                    leaderboard.sort(key=lambda x: (-x['correctAnswers'], x['totalTime']))
                    
                    # Add ranks
                    for i, player in enumerate(leaderboard):
                        player['rank'] = i + 1
                    
                    print(f"🏆 Leaderboard: {[(p['name'], p['rank'], p['correctAnswers']) for p in leaderboard]}")
                    
                    emit('quiz-finished', {
                        'leaderboard': leaderboard,
                        'quiz': room['quiz']
                    }, room=room_code)
                    
                    print(f"Quiz finished in room: {room_code}")
                    
                    # Schedule room deletion
                    def delete_room_later():
                        import time
                        time.sleep(60)
                        try:
                            delete_room(room_code)
                            print(f"🗑️ Room {room_code} auto-deleted 60s after quiz completion")
                        except Exception as e:
                            print(f"❌ Error auto-deleting room: {e}")
                    
                    import threading
                    threading.Thread(target=delete_room_later, daemon=True).start()
                else:
                    finished_count = sum(
                        1 for p in updated_room['players'] 
                        if len(p['answers']) == len(room['quiz'])
                    )
                    print(f"⏳ {finished_count}/{len(updated_room['players'])} players finished")
            
        except Exception as e:
            print(f"❌ Error submitting answer: {e}")
            import traceback
            traceback.print_exc()
    
    @socketio.on('get-leaderboard')
    def handle_get_leaderboard(data):
        try:
            room_code = data.get('roomCode')
            room = get_room(room_code)
            
            if not room:
                return
            
            leaderboard = []
            for p in room['players']:
                leaderboard.append({
                    'name': p['name'],
                    'score': sum(1 for a in p.get('answers', []) if a.get('isCorrect', False))
                })
            
            leaderboard.sort(key=lambda x: x['score'], reverse=True)
            
            emit('leaderboard-update', {'leaderboard': leaderboard})
            
        except Exception as e:
            print(f"❌ Error getting leaderboard: {e}")
