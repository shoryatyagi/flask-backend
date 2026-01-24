"""
PDF Processing Service
Extracts text from PDF files and creates chunks for quiz generation
"""

import io
import re
import random
from typing import List, Tuple


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Extract text from PDF file
    
    Args:
        file_bytes: PDF file as bytes
    
    Returns:
        Extracted text content
    """
    try:
        # Try pdfplumber first (better text extraction)
        import pdfplumber
        
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            text_parts = []
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
            
            full_text = '\n'.join(text_parts)
            
            if full_text.strip():
                print(f"✅ Extracted {len(full_text)} characters using pdfplumber")
                return full_text
    except Exception as e:
        print(f"⚠️ pdfplumber failed: {e}")
    
    # Fallback to PyPDF2
    try:
        from PyPDF2 import PdfReader
        
        reader = PdfReader(io.BytesIO(file_bytes))
        text_parts = []
        
        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)
        
        full_text = '\n'.join(text_parts)
        
        if full_text.strip():
            print(f"✅ Extracted {len(full_text)} characters using PyPDF2")
            return full_text
            
    except Exception as e:
        print(f"⚠️ PyPDF2 failed: {e}")
    
    raise ValueError("Failed to extract text from PDF. The PDF might be corrupted or contain only images.")


def create_chunks(text: str, number_of_questions: int) -> List[str]:
    """
    Split text into random chunks from the entire PDF
    Creates many small chunks then randomly selects the needed number
    
    Args:
        text: Full text content
        number_of_questions: Number of chunks to create
    
    Returns:
        List of text chunks
    """
    # Clean the text
    cleaned_text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
    cleaned_text = re.sub(r'\n+', '\n', cleaned_text)  # Normalize newlines
    cleaned_text = cleaned_text.strip()
    
    # Split into sentences first
    sentences = re.findall(r'[^.!?]+[.!?]+', cleaned_text)
    
    if not sentences:
        sentences = [cleaned_text]
    
    # Create many small chunks (3-5 sentences each)
    all_chunks = []
    sentences_per_chunk = 4  # Average chunk size
    
    for i in range(0, len(sentences), sentences_per_chunk):
        chunk_sentences = sentences[i:i + sentences_per_chunk]
        chunk = ' '.join(chunk_sentences).strip()
        if len(chunk) > 50:  # Only include meaningful chunks
            all_chunks.append(chunk)
    
    # If we don't have enough chunks, split larger
    if len(all_chunks) < number_of_questions:
        min_chunk_size = 200  # Minimum characters per chunk
        temp_chunks = []
        
        for i in range(0, len(cleaned_text), min_chunk_size):
            chunk = cleaned_text[i:i + min_chunk_size].strip()
            if len(chunk) > 50:
                temp_chunks.append(chunk)
        
        if len(temp_chunks) > len(all_chunks):
            all_chunks = temp_chunks
    
    # Randomly select numberOfQuestions chunks
    available_indices = list(range(len(all_chunks)))
    random.shuffle(available_indices)
    
    # Select the first numberOfQuestions indices
    selected_indices = available_indices[:min(number_of_questions, len(all_chunks))]
    
    # Get chunks in their original order for better context
    selected_indices.sort()
    
    selected_chunks = [all_chunks[i] for i in selected_indices]
    
    # If we still don't have enough, pad with the entire text
    while len(selected_chunks) < number_of_questions:
        selected_chunks.append(cleaned_text)
    
    print(f"📊 Created {len(all_chunks)} total chunks, randomly selected {len(selected_chunks)}")
    
    return selected_chunks


def process_pdf_for_quiz(file_bytes: bytes, number_of_questions: int) -> Tuple[List[str], dict]:
    """
    Process PDF and create chunks for quiz generation
    
    Args:
        file_bytes: PDF file as bytes
        number_of_questions: Number of questions to generate
    
    Returns:
        Tuple of (chunks list, metadata dict)
    """
    # Extract text
    full_text = extract_text_from_pdf(file_bytes)
    
    if not full_text or not full_text.strip():
        raise ValueError("No text found in PDF. The PDF might be empty or contain only images.")
    
    print(f"📝 Extracted {len(full_text)} characters from PDF")
    
    # Create chunks
    chunks = create_chunks(full_text, number_of_questions)
    
    print(f"✂️ Created {len(chunks)} chunks for {number_of_questions} questions")
    
    metadata = {
        'totalText': len(full_text),
        'chunksCount': len(chunks),
    }
    
    return chunks, metadata


def validate_pdf_file(file_bytes: bytes, filename: str, max_size_mb: int = 5) -> None:
    """
    Validate PDF file
    
    Args:
        file_bytes: PDF file as bytes
        filename: Original filename
        max_size_mb: Maximum file size in MB
    
    Raises:
        ValueError: If validation fails
    """
    # Check file size
    max_size = max_size_mb * 1024 * 1024
    if len(file_bytes) > max_size:
        raise ValueError(f"File size must be less than {max_size_mb}MB")
    
    # Check file extension
    if not filename.lower().endswith('.pdf'):
        raise ValueError("Please upload a valid PDF file")
    
    # Check PDF header
    if not file_bytes[:4] == b'%PDF':
        raise ValueError("Invalid PDF file format")
