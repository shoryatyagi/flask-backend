"""
Quiz Routes
Handles quiz generation and related endpoints
"""

from flask import Blueprint, request, jsonify, g
from services.groq_ai import generate_quiz_from_prompt, generate_quiz_from_text
from services.firebase_auth import firebase_auth_optional
from datetime import datetime


quiz_bp = Blueprint('quiz', __name__, url_prefix='/api')


@quiz_bp.route('/generate-quiz', methods=['POST'])
@firebase_auth_optional
def generate_quiz():
    """
    Generate quiz from a topic using AI
    
    Body:
        quizName: Optional quiz name
        topic: Topic to generate questions about
        numberOfQuestions: Number of questions to generate
        difficulty: Difficulty level (easy, medium, hard)
    
    Returns:
        Generated quiz with metadata
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
        
        quiz_name = data.get('quizName', '').strip()
        topic = data.get('topic', '').strip()
        number_of_questions = data.get('numberOfQuestions', 10)
        difficulty = data.get('difficulty', 'medium').lower()
        
        # Validate inputs
        if not topic:
            return jsonify({'error': 'Topic is required'}), 400
        
        # Validate number of questions
        if not isinstance(number_of_questions, int) or number_of_questions < 5:
            return jsonify({'error': 'Number of questions must be at least 5'}), 400
        
        if difficulty not in ['easy', 'medium', 'hard']:
            return jsonify({'error': 'Invalid difficulty level'}), 400
        
        print(f"🚀 Generating quiz using Groq AI")
        print(f"📝 Topic: {topic}, Questions: {number_of_questions}, Difficulty: {difficulty}")
        
        # Generate quiz
        quiz = generate_quiz_from_prompt(topic, number_of_questions, difficulty)
        
        return jsonify({
            'quiz': quiz,
            'metadata': {
                'quizName': quiz_name or topic,
                'topic': topic,
                'numberOfQuestions': len(quiz),
                'difficulty': difficulty,
                'generatedAt': datetime.utcnow().isoformat(),
                'source': 'ai'
            }
        })
        
    except ValueError as e:
        print(f"❌ Validation error: {e}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        print(f"❌ Error generating quiz: {e}")
        return jsonify({'error': 'Failed to generate quiz. Please try again.'}), 500


@quiz_bp.route('/generate-quiz-from-chunks', methods=['POST'])
@firebase_auth_optional
def generate_quiz_from_chunks():
    """
    Generate quiz from text chunks (used for PDF processing)
    
    Body:
        chunks: Array of text chunks
        numberOfQuestions: Number of questions to generate
        quizName: Optional quiz name
    
    Returns:
        Generated quiz with metadata
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
        
        chunks = data.get('chunks', [])
        number_of_questions = data.get('numberOfQuestions', 10)
        quiz_name = data.get('quizName', 'PDF Quiz')
        
        # Validate chunks
        if not isinstance(chunks, list) or len(chunks) == 0:
            return jsonify({'error': 'Chunks array is required and must not be empty'}), 400
        
        # Validate number of questions
        if not isinstance(number_of_questions, int) or number_of_questions < 5:
            return jsonify({'error': 'Number of questions must be at least 5'}), 400
        
        print(f"🚀 Generating {number_of_questions} questions from {len(chunks)} PDF chunks...")
        
        # Select chunks equal to number of questions
        selected_chunks = chunks[:number_of_questions]
        
        # Combine selected chunks with clear separation
        combined_text = '\n\n---\n\n'.join([
            f"[Section {i + 1}]\n{chunk}" for i, chunk in enumerate(selected_chunks)
        ])
        
        print(f"📊 Using {len(selected_chunks)} chunks ({len(combined_text)} characters total)")
        
        # Generate quiz
        quiz = generate_quiz_from_text(combined_text, number_of_questions)
        
        print(f"✅ Quiz generated successfully: {len(quiz)} questions")
        
        return jsonify({
            'success': True,
            'quiz': quiz,
            'metadata': {
                'quizName': quiz_name,
                'numberOfQuestions': len(quiz),
                'chunksUsed': len(selected_chunks),
                'source': 'pdf-chunks',
                'generatedAt': datetime.utcnow().isoformat()
            }
        })
        
    except ValueError as e:
        print(f"❌ Validation error: {e}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        print(f"❌ Error generating quiz from chunks: {e}")
        
        # Specific error messages
        error_message = str(e)
        if 'Groq API' in error_message:
            return jsonify({
                'error': 'Groq API error. Please check your API key and try again.',
                'details': error_message
            }), 500
        
        if 'Invalid API key' in error_message:
            return jsonify({
                'error': 'Invalid Groq API key. Please check GROQ_API_KEY environment variable.',
                'details': error_message
            }), 500
        
        return jsonify({
            'error': error_message or 'Failed to generate quiz from PDF chunks',
            'details': 'An unexpected error occurred during quiz generation'
        }), 500


@quiz_bp.route('/generate-quiz-from-pdf-chunks', methods=['POST'])
@firebase_auth_optional
def generate_quiz_from_pdf_chunks():
    """
    Alias for generate-quiz-from-chunks (for frontend compatibility)
    """
    return generate_quiz_from_chunks()
