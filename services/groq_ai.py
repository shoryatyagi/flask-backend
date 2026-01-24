"""
Groq AI Service for Quiz Generation
Uses Groq API (OpenAI-compatible) for generating quiz questions
"""

import os
import re
import json
import random
import httpx
from openai import OpenAI


# Lazy initialization
_groq_client = None


def get_groq_client():
    """Get or create Groq client"""
    global _groq_client
    
    if _groq_client is None:
        api_key = os.getenv('GROQ_API_KEY')
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable not set")
        
        # Create client without proxy settings to avoid compatibility issues
        _groq_client = OpenAI(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1",
            http_client=httpx.Client()
        )
    
    return _groq_client


def get_groq_model():
    """Get the Groq model name from environment"""
    return os.getenv('GROQ_MODEL', 'groq/compound')


async def generate_with_groq(prompt, max_retries=2):
    """
    Generate response using Groq API
    
    Args:
        prompt: The prompt to send to the AI
        max_retries: Maximum retry attempts
    
    Returns:
        Response text from AI
    """
    client = get_groq_client()
    model = get_groq_model()
    
    retry_count = 0
    while retry_count <= max_retries:
        try:
            print(f"🚀 Using Groq model: {model}")
            
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            
            response_text = response.choices[0].message.content
            
            if not response_text:
                raise ValueError("No response from Groq")
            
            return response_text
            
        except Exception as e:
            print(f"❌ Groq API Error (attempt {retry_count + 1}/{max_retries + 1}): {e}")
            
            if retry_count < max_retries:
                retry_count += 1
                print(f"⏳ Retrying... (attempt {retry_count + 1}/{max_retries + 1})")
                import time
                time.sleep(2)
                continue
            else:
                raise ValueError(f"Groq API Error: {str(e)}")


def generate_with_groq_sync(prompt, max_retries=2):
    """Synchronous version of generate_with_groq"""
    client = get_groq_client()
    model = get_groq_model()
    
    retry_count = 0
    while retry_count <= max_retries:
        try:
            print(f"🚀 Using Groq model: {model}")
            
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            
            response_text = response.choices[0].message.content
            
            if not response_text:
                raise ValueError("No response from Groq")
            
            return response_text
            
        except Exception as e:
            print(f"❌ Groq API Error (attempt {retry_count + 1}/{max_retries + 1}): {e}")
            
            if retry_count < max_retries:
                retry_count += 1
                print(f"⏳ Retrying... (attempt {retry_count + 1}/{max_retries + 1})")
                import time
                time.sleep(2)
                continue
            else:
                raise ValueError(f"Groq API Error: {str(e)}")


def parse_quiz_json(response_text):
    """
    Parse and clean JSON response from AI
    
    Args:
        response_text: Raw response from AI
    
    Returns:
        Parsed JSON array of questions
    """
    json_text = response_text
    
    # Extract JSON from markdown code blocks if present
    if "```json" in response_text:
        json_text = response_text.split("```json")[1].split("```")[0].strip()
    elif "```" in response_text:
        json_text = response_text.split("```")[1].split("```")[0].strip()
    
    # Remove special tokens or garbage
    json_text = re.sub(r'<[^>]*>', '', json_text)  # Remove HTML-like tags
    json_text = re.sub(r'｜[^｜]*｜', '', json_text)  # Remove special token patterns
    json_text = re.sub(r'\s*<｜.*$', '', json_text)  # Remove anything starting with <｜
    json_text = json_text.strip()
    
    # Clean up common JSON issues
    json_text = re.sub(r',(\s*[}\]])', r'\1', json_text)  # Remove trailing commas
    json_text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', json_text)  # Remove control characters
    json_text = json_text.strip()
    
    print(f"Cleaned JSON (first 500 chars): {json_text[:500]}")
    
    try:
        questions = json.loads(json_text)
        return questions
    except json.JSONDecodeError as e:
        print(f"❌ JSON Parse Error: {e}")
        
        # Try to extract JSON array
        try:
            print("🔧 Attempting to extract JSON array...")
            
            first_bracket = json_text.find('[')
            last_bracket = json_text.rfind(']')
            
            if first_bracket == -1 or last_bracket == -1:
                raise ValueError("No JSON array found in response")
            
            extracted_json = json_text[first_bracket:last_bracket + 1]
            
            # Minimal cleanup
            extracted_json = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', extracted_json)
            extracted_json = extracted_json.replace('\r', ' ').replace('\n', ' ').replace('\t', ' ')
            extracted_json = re.sub(r',(\s*[}\]])', r'\1', extracted_json)
            extracted_json = extracted_json.strip()
            
            questions = json.loads(extracted_json)
            print("✅ Successfully parsed after extraction!")
            return questions
            
        except Exception as second_error:
            print(f"❌ Second parse attempt failed: {second_error}")
            raise ValueError(
                f"Failed to parse AI response as JSON.\n"
                f"Original error: {e}\n"
                f"Response preview: {response_text[:300]}..."
            )


def validate_and_clean_questions(questions, number_of_questions):
    """
    Validate and clean quiz questions
    
    Args:
        questions: List of question objects
        number_of_questions: Expected number of questions
    
    Returns:
        List of validated questions
    """
    if not isinstance(questions, list) or len(questions) == 0:
        raise ValueError("Invalid quiz format: Expected an array of questions")
    
    print(f"✅ Parsed {len(questions)} questions successfully")
    
    # Handle question count mismatch
    if len(questions) > number_of_questions:
        print(f"🔧 Trimming {len(questions) - number_of_questions} extra questions")
        questions = questions[:number_of_questions]
    
    # Validate and clean each question
    valid_questions = []
    
    for i, q in enumerate(questions):
        # Check required fields
        if not q.get('question') or not isinstance(q.get('options'), list):
            print(f"⚠️ Skipping invalid question at index {i}: Missing question or options")
            continue
        
        # Clean up options
        options = []
        for opt in q['options']:
            if isinstance(opt, str):
                cleaned = re.sub(r'^Option [A-D]:\s*', '', opt, flags=re.IGNORECASE).strip()
                options.append(cleaned)
            else:
                options.append(str(opt))
        
        q['options'] = options
        
        # Check if options are valid
        if len(options) != 4 or any(not opt or not isinstance(opt, str) or not opt.strip() for opt in options):
            print(f"⚠️ Skipping question with invalid options at index {i}")
            continue
        
        # Convert correctAnswer to number if it's a letter
        correct_answer = q.get('correctAnswer')
        
        if isinstance(correct_answer, str):
            letter_to_index = {'A': 0, 'B': 1, 'C': 2, 'D': 3, 'a': 0, 'b': 1, 'c': 2, 'd': 3}
            if correct_answer in letter_to_index:
                q['correctAnswer'] = letter_to_index[correct_answer]
            else:
                try:
                    q['correctAnswer'] = int(correct_answer)
                except ValueError:
                    print(f"⚠️ Skipping question with invalid correctAnswer at index {i}: {correct_answer}")
                    continue
        
        # Check if correctAnswer is valid
        if not isinstance(q['correctAnswer'], int) or q['correctAnswer'] < 0 or q['correctAnswer'] >= len(options):
            print(f"⚠️ Skipping question with invalid correctAnswer at index {i}: {q['correctAnswer']}")
            continue
        
        valid_questions.append(q)
    
    if len(valid_questions) == 0:
        raise ValueError("No valid questions generated. Please try again.")
    
    return valid_questions


def shuffle_question_options(questions):
    """
    Shuffle options for each question and update correct answer index
    
    Args:
        questions: List of question objects
    
    Returns:
        List of questions with shuffled options
    """
    shuffled = []
    
    for q in questions:
        correct_answer_text = q['options'][q['correctAnswer']]
        
        # Shuffle options
        shuffled_options = q['options'].copy()
        random.shuffle(shuffled_options)
        
        # Find new index of correct answer
        new_correct_index = shuffled_options.index(correct_answer_text)
        
        shuffled.append({
            'question': q['question'],
            'options': shuffled_options,
            'correctAnswer': new_correct_index,
            'explanation': q.get('explanation', 'No explanation provided.')
        })
    
    return shuffled


def generate_quiz_from_text(text, number_of_questions=10):
    """
    Generate quiz questions from text content
    
    Args:
        text: Text content to generate questions from
        number_of_questions: Number of questions to generate
    
    Returns:
        List of quiz questions
    """
    print(f"🚀 Using Groq AI for quiz generation")
    
    prompt = f"""Analyze the following content and create EXACTLY {number_of_questions} multiple-choice quiz questions based on the key concepts and facts in the text.

🎯 CRITICAL: You MUST generate EXACTLY {number_of_questions} questions. NOT {number_of_questions - 1}, NOT {number_of_questions + 1}, but EXACTLY {number_of_questions} questions.

CONTENT TO ANALYZE:
{text[:8000]}

YOUR TASK:
Generate {number_of_questions} questions that test understanding of the content above. Each question must have 4 options and 1 correct answer.

KEY RULES:
- Questions must be based ONLY on the actual content provided above
- If content is about a sport (soccer, football, basketball, etc.), ask about the sport itself - rules, players, teams, tournaments, tactics, history
- If content is about a programming language, ask about syntax, concepts, libraries, features
- Focus on the SUBJECT MATTER in the content, not meta topics
- Do NOT ask "Which country..." if the content is about a sport - focus on the sport aspects

OUTPUT FORMAT:
Return a JSON array with this structure:
[
  {{
    "question": "Your question text here based on the content",
    "options": ["First option text", "Second option text", "Third option text", "Fourth option text"],
    "correctAnswer": 0,
    "explanation": "Why this answer is correct"
  }}
]

RULES:
- Generate EXACTLY {number_of_questions} questions - count them before submitting
- correctAnswer is a number: 0 for first option, 1 for second, 2 for third, 3 for fourth
- Do NOT use letters like "A", "B", "C", "D" - use numbers 0, 1, 2, 3
- Do NOT add "Option A:" or similar prefixes to the options
- Questions must be based on the actual content provided, not generic examples
- Return ONLY the JSON array, no other text or explanations"""
    
    response_text = generate_with_groq_sync(prompt)
    questions = parse_quiz_json(response_text)
    valid_questions = validate_and_clean_questions(questions, number_of_questions)
    shuffled_questions = shuffle_question_options(valid_questions)
    
    print(f"✅ Successfully generated {len(shuffled_questions)} valid questions")
    return shuffled_questions


def generate_quiz_from_prompt(topic, number_of_questions=10, difficulty='medium'):
    """
    Generate quiz questions from a topic prompt
    
    Args:
        topic: Topic to generate questions about
        number_of_questions: Number of questions to generate
        difficulty: Difficulty level (easy, medium, hard)
    
    Returns:
        List of quiz questions
    """
    print(f"🚀 Using Groq AI for quiz generation")
    
    # Clean the topic
    cleaned_topic = re.sub(
        r'^\s*(make|generate|create)\s+(a\s+)?(quiz|test)\s+(on|about|for|regarding)\s*',
        '',
        topic,
        flags=re.IGNORECASE
    )
    cleaned_topic = re.sub(
        r'^\s*(quiz|test)\s+(on|about|for|regarding)\s*',
        '',
        cleaned_topic,
        flags=re.IGNORECASE
    ).strip()
    
    if not cleaned_topic:
        cleaned_topic = topic
    
    print(f"📝 Original topic: \"{topic}\"")
    print(f"🎯 Cleaned topic: \"{cleaned_topic}\"")
    print(f"📊 Generating {number_of_questions} questions at {difficulty} difficulty")
    
    difficulty_instructions = {
        'easy': "Create basic, fundamental questions suitable for beginners. Focus on definitions, simple facts, and core concepts.",
        'medium': "Create moderate difficulty questions that require understanding and application of concepts. Mix recall and reasoning.",
        'hard': "Create advanced, challenging questions that require deep understanding, analysis, and critical thinking. Include complex scenarios."
    }
    
    prompt = f"""You are an expert quiz generator. Create EXACTLY {number_of_questions} multiple-choice questions about the topic: "{cleaned_topic}"

🎯 CRITICAL: You MUST generate EXACTLY {number_of_questions} questions. NOT {number_of_questions - 1}, NOT {number_of_questions + 1}, but EXACTLY {number_of_questions} questions.

TOPIC FOCUS AND INTERPRETATION:
- If topic is "soccer" or "football": Create questions about the SPORT itself - rules, gameplay, famous players, clubs/teams, leagues, tournaments (World Cup, Champions League, etc.), tactics, positions, equipment, history of the sport
- If topic is "Python": Create questions about the Python programming language - syntax, libraries, concepts, functions
- If topic is "History": Create questions about historical events, dates, figures, civilizations
- If topic is "Science": Create questions about scientific concepts, discoveries, principles, theories
- If topic is a subject/field: Create questions testing knowledge OF that subject/field

KEY RULES:
- ALL questions must be DIRECTLY RELATED to the subject matter of "{cleaned_topic}"
- Questions should test knowledge ABOUT "{cleaned_topic}" as a subject/topic/field
- DO NOT create meta questions about quizzes, AI, or question generation itself
- DO NOT ask "Which country..." when the topic is a sport - instead ask about teams, players, tournaments, rules, etc.
- Focus ONLY on factual knowledge about "{cleaned_topic}"

CRITICAL REQUIREMENTS:
1. Generate EXACTLY {number_of_questions} questions - count them before submitting
2. Create questions SPECIFICALLY about the subject matter of "{cleaned_topic}" itself
3. Questions should test knowledge OF "{cleaned_topic}", not ABOUT how to create quizzes on it
4. EVERY question MUST have exactly 4 options - NO MORE, NO LESS
5. EVERY option MUST be a non-empty string with at least 2 characters
6. The correct answer must be one of the 4 options (index 0-3)
7. Return ONLY a valid JSON array - NO markdown, NO explanations, NO extra text

Difficulty Level: {difficulty.upper()}
{difficulty_instructions.get(difficulty, difficulty_instructions['medium'])}

For EACH question:
- Write a clear, specific question testing knowledge about "{cleaned_topic}"
- Provide exactly 4 plausible answer options (all must be non-empty strings)
- Mark which option (0, 1, 2, or 3) is correct
- Provide a 2-3 sentence explanation

OUTPUT FORMAT:
[
  {{
    "question": "Your question text here",
    "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
    "correctAnswer": 0,
    "explanation": "Why this answer is correct"
  }}
]

DO NOT include any prefixes like "A.", "B.", "C.", "D." or "Option A:", "Option B:" in the options.
Just provide the plain answer text.

Return ONLY the JSON array, nothing else."""
    
    response_text = generate_with_groq_sync(prompt)
    questions = parse_quiz_json(response_text)
    valid_questions = validate_and_clean_questions(questions, number_of_questions)
    shuffled_questions = shuffle_question_options(valid_questions)
    
    print(f"✅ Successfully generated {len(shuffled_questions)} valid questions")
    return shuffled_questions
