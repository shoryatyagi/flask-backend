"""
PDF Processing Routes
Handles PDF upload and text extraction
"""

from flask import Blueprint, request, jsonify, current_app
from services.pdf_processor import process_pdf_for_quiz, validate_pdf_file
from services.firebase_auth import firebase_auth_optional


pdf_bp = Blueprint('pdf', __name__, url_prefix='/api')


@pdf_bp.route('/process-pdf-chunks', methods=['POST'])
@firebase_auth_optional
def process_pdf_chunks():
    """
    Process PDF and extract text chunks
    
    FormData:
        file: PDF file
        numberOfQuestions: Number of questions to generate
    
    Returns:
        Text chunks and metadata
    """
    try:
        # Check if file is in request
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        
        if not file.filename:
            return jsonify({'error': 'No file selected'}), 400
        
        # Get number of questions
        number_of_questions = request.form.get('numberOfQuestions', '10')
        try:
            number_of_questions = int(number_of_questions)
        except ValueError:
            number_of_questions = 10

        maximum = current_app.config['MAX_QUESTIONS_PDF']
        if number_of_questions < 5 or number_of_questions > maximum:
            return jsonify({
                'error': f'Number of questions must be between 5 and {maximum}'
            }), 400
        
        # Read file bytes
        file_bytes = file.read()
        
        # Validate file
        validate_pdf_file(file_bytes, file.filename, max_size_mb=5)
        
        print(f"📄 Processing PDF: {file.filename} ({len(file_bytes) / 1024:.2f} KB)")
        
        # Process PDF
        chunks, metadata = process_pdf_for_quiz(file_bytes, number_of_questions)
        
        print(f"✂️ Created {len(chunks)} chunks for {number_of_questions} questions")
        
        return jsonify({
            'success': True,
            'chunks': chunks,
            'metadata': {
                'fileName': file.filename,
                'fileSize': len(file_bytes),
                'totalText': metadata['totalText'],
                'chunksCount': len(chunks)
            }
        })
        
    except ValueError as e:
        print(f"❌ Validation error: {e}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        print(f"❌ Error processing PDF: {e}")
        return jsonify({'error': str(e) or 'Failed to process PDF'}), 500
