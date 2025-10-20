from flask import Flask, request, jsonify, redirect, url_for, session
from flask_cors import CORS
import spacy
import openai
import os
from dotenv import load_dotenv
import json
import random
from datetime import datetime
import hashlib
import secrets
import uuid
import jwt
from authlib.integrations.flask_client import OAuth
from authlib.common.security import generate_token
import requests
from pathlib import Path
from database import get_db_connection, execute_query, execute_many, db_config, init_database_schema
from logging_config import setup_logging, get_logger, log_exception

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Setup logging
setup_logging('nosuvo_backend', log_level='DEBUG')
logger = get_logger(__name__)

# Load environment variables
# Load .env.local first (takes precedence), then .env
env_local_path = Path('.env.local')
env_path = Path('.env')

if env_local_path.exists():
    load_dotenv(dotenv_path=env_local_path, override=True)
    print("✅ Loaded configuration from .env.local")
elif env_path.exists():
    load_dotenv(dotenv_path=env_path)
    print("✅ Loaded configuration from .env")
else:
    load_dotenv()  # Try default locations
    print("⚠️  No .env or .env.local file found, using system environment variables")

# Set up session secret for OAuth
app.secret_key = os.getenv('FLASK_SECRET_KEY', secrets.token_hex(32))

# Initialize OAuth
oauth = OAuth(app)

# Configure OAuth providers
def configure_oauth_providers():
    """Configure OAuth providers for Google, Microsoft, and Apple"""
    
    # Google OAuth
    google_client_id = os.getenv('GOOGLE_CLIENT_ID')
    google_client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
    
    if google_client_id and google_client_secret:
        oauth.register(
            name='google',
            client_id=google_client_id,
            client_secret=google_client_secret,
            server_metadata_url='https://accounts.google.com/.well-known/openid_configuration',
            client_kwargs={'scope': 'openid email profile'}
        )
    
    # Microsoft OAuth
    microsoft_client_id = os.getenv('MICROSOFT_CLIENT_ID')
    microsoft_client_secret = os.getenv('MICROSOFT_CLIENT_SECRET')
    
    if microsoft_client_id and microsoft_client_secret:
        oauth.register(
            name='microsoft',
            client_id=microsoft_client_id,
            client_secret=microsoft_client_secret,
            server_metadata_url='https://login.microsoftonline.com/common/v2.0/.well-known/openid_configuration',
            client_kwargs={'scope': 'openid email profile'}
        )
    
    # Apple OAuth (requires special handling due to JWT client secret)
    apple_client_id = os.getenv('APPLE_CLIENT_ID')
    
    if apple_client_id:
        oauth.register(
            name='apple',
            client_id=apple_client_id,
            server_metadata_url='https://appleid.apple.com/.well-known/openid_configuration',
            client_kwargs={'scope': 'openid email name'}
        )

# Load English model
nlp = spacy.load("en_core_web_sm")

# Configure OAuth providers
configure_oauth_providers()

# Simple session storage (in production, use Redis or database sessions)
user_sessions = {}

def hash_password(password: str) -> str:
    """Hash password with salt"""
    salt = secrets.token_hex(16)
    password_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
    return f"{salt}:{password_hash.hex()}"

def verify_password(password: str, stored_hash: str) -> bool:
    """Verify password against stored hash"""
    try:
        salt, password_hash = stored_hash.split(':')
        new_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
        return password_hash == new_hash.hex()
    except:
        return False

def generate_session_token() -> str:
    """Generate a secure session token"""
    return secrets.token_urlsafe(32)

def get_current_user():
    """Get current user from session token"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if token in user_sessions:
        return user_sessions[token]
    return None

def create_apple_client_secret():
    """Create Apple client secret JWT"""
    team_id = os.getenv('APPLE_TEAM_ID')
    key_id = os.getenv('APPLE_KEY_ID')
    client_id = os.getenv('APPLE_CLIENT_ID')
    private_key_path = os.getenv('APPLE_PRIVATE_KEY_PATH')
    
    if not all([team_id, key_id, client_id, private_key_path]):
        return None
    
    try:
        with open(private_key_path, 'r') as key_file:
            private_key = key_file.read()
        
        headers = {
            'kid': key_id,
            'alg': 'ES256'
        }
        
        payload = {
            'iss': team_id,
            'iat': datetime.utcnow().timestamp(),
            'exp': datetime.utcnow().timestamp() + 86400 * 180,  # 6 months
            'aud': 'https://appleid.apple.com',
            'sub': client_id
        }
        
        return jwt.encode(payload, private_key, algorithm='ES256', headers=headers)
    except Exception as e:
        print(f"Error creating Apple client secret: {e}")
        return None

def create_or_get_oauth_user(provider: str, user_info: dict, preferred_language: str = 'en'):
    """Create or get user from OAuth provider info"""
    # Extract user information based on provider
    if provider == 'google':
        email = user_info.get('email', '')
        username = user_info.get('name', email.split('@')[0])
        display_name = user_info.get('name', '')
    elif provider == 'microsoft':
        email = user_info.get('email', '')
        username = user_info.get('name', email.split('@')[0])
        display_name = user_info.get('name', '')
    elif provider == 'apple':
        email = user_info.get('email', '')
        username = email.split('@')[0] if email else f"apple_user_{secrets.token_hex(4)}"
        display_name = user_info.get('name', {}).get('fullName', '') if user_info.get('name') else ''
    else:
        raise ValueError(f"Unsupported OAuth provider: {provider}")
    
    if not email:
        raise ValueError("Email is required for OAuth authentication")
    
    # Check if user already exists
    existing_user = execute_query('SELECT id FROM users WHERE email = %s', (email,), fetch=True)
    
    if existing_user:
        user_id = existing_user[0]['id']
        # Update last login
        execute_query('UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = %s', (user_id,))
    else:
        # Create new user
        execute_query('''
            INSERT INTO users (username, email, password_hash, preferred_language, created_at, last_login)
            VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ''', (username, email, f"oauth_{provider}", preferred_language))
        
        # Get the new user ID
        new_user = execute_query('SELECT id FROM users WHERE email = %s', (email,), fetch=True)
        user_id = new_user[0]['id'] if new_user else None
        
        if user_id:
            # Initialize user queue
            initialize_user_queue(user_id, preferred_language)
    
    # Get user details
    user_data = execute_query('SELECT username, email, preferred_language FROM users WHERE id = %s', (user_id,), fetch=True)
    
    if not user_data:
        raise ValueError("Failed to retrieve user data")
    
    return {
        "user_id": user_id,
        "username": user_data[0]['username'],
        "email": user_data[0]['email'],
        "preferred_language": user_data[0]['preferred_language']
    }

def initialize_user_queue(user_id: int, preferred_language: str = 'en'):
    """Initialize user queue with all available exercises in their preferred language"""
    # Get all exercises in user's preferred language
    exercises = execute_query('''
        SELECT id FROM exercises 
        WHERE language = %s 
        AND id NOT IN (SELECT exercise_id FROM user_progress WHERE user_id = %s AND status = 'completed')
        ORDER BY difficulty, RANDOM()
    ''', (preferred_language, user_id), fetch=True)
    
    # Add exercises to user queue
    for position, exercise in enumerate(exercises, 1):
        execute_query('''
            INSERT INTO user_queue (user_id, exercise_id, queue_position)
            VALUES (%s, %s, %s)
            ON CONFLICT (user_id, exercise_id) DO NOTHING
        ''', (user_id, exercise['id'], position))

def get_next_exercise_for_user(user_id: int):
    """Get the next exercise in user's queue"""
    # Get the first exercise in queue
    exercise_result = execute_query('''
        SELECT e.id, e.title, e.text, e.language, e.difficulty, e.topic, e.questions
        FROM exercises e
        JOIN user_queue uq ON e.id = uq.exercise_id
        WHERE uq.user_id = %s AND uq.queue_position = 1
    ''', (user_id,), fetch=True)
    
    if exercise_result:
        exercise = exercise_result[0]
        return {
            "id": exercise['id'],
            "title": exercise['title'],
            "text": exercise['text'],
            "language": exercise['language'],
            "difficulty": exercise['difficulty'],
            "topic": exercise['topic'],
            "questions": json.loads(exercise['questions'])
        }
    return None

def update_user_progress(user_id: int, exercise_id: int, comprehension_score: float, 
                        questions_answered: int, questions_correct: int, 
                        reading_speed_wpm: float, session_duration_seconds: int):
    """Update user progress and manage queue based on comprehension score"""
    # Determine status based on comprehension score
    status = 'completed' if comprehension_score >= 0.7 else 'failed'
    
    # Update or insert progress
    execute_query('''
        INSERT INTO user_progress 
        (user_id, exercise_id, status, comprehension_score, questions_answered, 
         questions_correct, reading_speed_wpm, session_duration_seconds, completed_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
        ON CONFLICT (user_id, exercise_id) 
        DO UPDATE SET 
            status = EXCLUDED.status,
            comprehension_score = EXCLUDED.comprehension_score,
            questions_answered = EXCLUDED.questions_answered,
            questions_correct = EXCLUDED.questions_correct,
            reading_speed_wpm = EXCLUDED.reading_speed_wpm,
            session_duration_seconds = EXCLUDED.session_duration_seconds,
            completed_at = EXCLUDED.completed_at
    ''', (user_id, exercise_id, status, comprehension_score, questions_answered, 
          questions_correct, reading_speed_wpm, session_duration_seconds))
    
    # Remove from queue if completed successfully
    if status == 'completed':
        execute_query('DELETE FROM user_queue WHERE user_id = %s AND exercise_id = %s', 
                      (user_id, exercise_id))
        
        # Reorder remaining queue items
        execute_query('''
            UPDATE user_queue 
            SET queue_position = queue_position - 1 
            WHERE user_id = %s AND queue_position > 1
        ''', (user_id,))
    else:
        # Move failed exercise to bottom of queue
        execute_query('''
            UPDATE user_queue 
            SET queue_position = (SELECT MAX(queue_position) + 1 FROM user_queue WHERE user_id = %s)
            WHERE user_id = %s AND exercise_id = %s
        ''', (user_id, user_id, exercise_id))
    
    return status

# Initialize OpenAI client (optional)
openai_api_key = os.getenv("OPENAI_API_KEY")
if openai_api_key:
    openai_client = openai.OpenAI(api_key=openai_api_key)
else:
    openai_client = None
    print("⚠️  OpenAI API key not found. Question generation will use fallback questions.")

def init_database():
    """Initialize the PostgreSQL database with all tables and indexes"""
    init_database_schema()

def insert_sample_exercises():
    """Insert sample exercises into the database"""
    # Check if exercises already exist
    count_result = execute_query('SELECT COUNT(*) as count FROM exercises', fetch=True)
    count = count_result[0]['count'] if count_result else 0
    
    # Always add English exercises if they don't exist
    en_result = execute_query('SELECT COUNT(*) as count FROM exercises WHERE language = %s', ('en',), fetch=True)
    en_count = en_result[0]['count'] if en_result else 0
    
    if en_count == 0:
        english_exercises = [
            {
                'title': 'Sea Water and Electroreception',
                'text': 'Open your eyes in sea water and it is difficult to see much more than a murky, bleary green colour. Sounds, too, are garbled and difficult to comprehend. Without specialised equipment humans would be lost in these deep sea habitats, so how do fish make it seem so easy? Much of this is due to a biological phenomenon known as electroreception – the ability to perceive and act upon electrical stimuli as part of the overall senses. This ability is only found in aquatic or amphibious species because water is an efficient conductor of electricity.',
                'language': 'en',
                'difficulty': 'intermediate',
                'topic': 'science',
                'questions': json.dumps([
                    {
                        "question": "What is the main biological phenomenon that allows fish to navigate in deep sea habitats?",
                        "options": {
                            "A": "Echolocation",
                            "B": "Electroreception", 
                            "C": "Bioluminescence",
                            "D": "Magnetic sensing"
                        },
                        "answer": "B"
                    },
                    {
                        "question": "Why is electroreception only found in aquatic or amphibious species?",
                        "options": {
                            "A": "Because they need to hunt in the dark",
                            "B": "Because water is an efficient conductor of electricity",
                            "C": "Because they have specialized brain structures",
                            "D": "Because they evolved from land animals"
                        },
                        "answer": "B"
                    },
                    {
                        "question": "What makes it difficult for humans to see in sea water without equipment?",
                        "options": {
                            "A": "The pressure affects vision",
                            "B": "The water appears as a murky, bleary green colour",
                            "C": "The salt content burns the eyes",
                            "D": "The temperature is too cold"
                        },
                        "answer": "B"
                    }
                ])
            }
        ]
        
        # Insert English exercises
        for exercise in english_exercises:
            execute_query('''
                INSERT INTO exercises (title, text, language, difficulty, topic, questions)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (
                exercise['title'],
                exercise['text'],
                exercise['language'],
                exercise['difficulty'],
                exercise['topic'],
                exercise['questions']
            ))
        
        print(f"✅ Added {len(english_exercises)} English exercises")
    
    # Only add other languages if no exercises exist at all
    if count == 0:
        # Add exercises for other languages here if needed
        print("📚 Database initialized with sample exercises")

# Initialize database on startup
init_database()
insert_sample_exercises()

def chunk_text_smart(text: str):
    """
    Intelligently chunk text into meaningful phrase-level units
    optimized for reducing subvocalization.
    """
    doc = nlp(text)
    chunks = []
    
    for sent in doc.sents:
        # Process sentence into meaningful chunks
        sent_chunks = []
        i = 0
        sent_tokens = list(sent)
        
        while i < len(sent_tokens):
            token = sent_tokens[i]
            chunk_tokens = []
            
            # Strategy 1: Capture noun chunks (noun phrases)
            if token.pos_ in ("NOUN", "PROPN", "PRON"):
                # Get full noun phrase
                for np in doc.noun_chunks:
                    if token in np:
                        chunk_tokens = [t.text for t in np]
                        i += len(chunk_tokens)
                        break
                
                if not chunk_tokens:
                    chunk_tokens = [token.text]
                    i += 1
            
            # Strategy 2: Capture verb phrases
            elif token.pos_ == "VERB":
                # Include auxiliaries and the main verb
                chunk_tokens = []
                
                # Add preceding auxiliaries
                for child in token.lefts:
                    if child.dep_ in ("aux", "auxpass", "neg"):
                        chunk_tokens.append(child.text)
                
                chunk_tokens.append(token.text)
                
                # Add direct objects or complements
                for child in token.rights:
                    if child.dep_ in ("dobj", "prt", "advmod") and len(chunk_tokens) < 4:
                        chunk_tokens.append(child.text)
                
                i += 1
            
            # Strategy 3: Capture prepositional phrases
            elif token.pos_ == "ADP":
                chunk_tokens = [token.text]
                
                # Add the object of preposition
                for child in token.children:
                    if child.dep_ == "pobj":
                        # Get the full noun phrase if it's part of one
                        for np in doc.noun_chunks:
                            if child in np:
                                chunk_tokens.extend([t.text for t in np])
                                break
                        else:
                            chunk_tokens.append(child.text)
                        break
                
                i += 1
            
            # Default: single token
            else:
                chunk_tokens = [token.text]
                i += 1
            
            if chunk_tokens:
                chunk = " ".join(chunk_tokens).strip()
                if chunk and not all(c in ".,!?;:" for c in chunk):
                    sent_chunks.append(chunk)
        
        chunks.extend(sent_chunks)
    
    # Clean up chunks
    cleaned_chunks = []
    for chunk in chunks:
        chunk = chunk.strip()
        if chunk and len(chunk) > 0:
            cleaned_chunks.append(chunk)
    
    return cleaned_chunks


def generate_comprehension_questions(text: str, num_questions: int = 3):
    """
    Generate comprehension questions from the given text using OpenAI.
    Returns questions with multiple choice answers.
    """
    if not openai_client:
        # Return fallback questions if OpenAI is not available
        return [
            {
                "question": "What is the main topic discussed in this text?",
                "options": ["The main topic", "A different topic", "Another topic", "Not mentioned"],
                "correct_answer": 0,
                "explanation": "This is a fallback question for testing purposes."
            }
        ]
    
    try:
        prompt = f"""
        Generate {num_questions} comprehension questions based on the following text. 
        Each question should test understanding of key concepts, facts, or details from the text.
        
        Text: "{text}"
        
        Return your response as a JSON array with this exact format:
        [
            {{
                "question": "Question text here?",
                "options": ["Option A", "Option B", "Option C", "Option D"],
                "correct_answer": 0,
                "explanation": "Brief explanation of why this answer is correct"
            }}
        ]
        
        Make sure:
        - Questions are clear and test comprehension
        - Options are plausible but only one is correct
        - correct_answer is the index (0-3) of the correct option
        - Include explanations for learning
        """
        
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        
        # Parse the JSON response
        questions_data = json.loads(response.choices[0].message.content)
        return questions_data
        
    except Exception as e:
        print(f"Error generating questions: {e}")
        # Return fallback questions if AI fails
        return [
            {
                "question": "What is the main topic discussed in this text?",
                "options": ["The main topic", "A different topic", "Another topic", "Not mentioned"],
                "correct_answer": 0,
                "explanation": "This is a fallback question for testing purposes."
            }
        ]




@app.route("/exercises", methods=["GET"])
def get_exercises():
    """
    Endpoint to get a random exercise with text and questions for reading comprehension.
    Supports filtering by language, difficulty, and topic.
    """
    try:
        # Get query parameters for filtering
        language = request.args.get('language', 'en')
        difficulty = request.args.get('difficulty')
        topic = request.args.get('topic')
        
        # Build query with optional filters
        query = "SELECT id, title, text, language, difficulty, topic, questions FROM exercises WHERE language = ?"
        params = [language]
        
        if difficulty:
            query += " AND difficulty = ?"
            params.append(difficulty)
        
        if topic:
            query += " AND topic = ?"
            params.append(topic)
        
        exercises = execute_query(query, tuple(params), fetch=True)
        
        if not exercises:
            # Fallback to any language if no exercises found
            exercises = execute_query("SELECT id, title, text, language, difficulty, topic, questions FROM exercises", fetch=True)
        
        if exercises:
            # Select random exercise
            selected_exercise = random.choice(exercises)
            
            return jsonify({
                "success": True,
                "exercise": {
                    "id": selected_exercise['id'],
                    "title": selected_exercise['title'],
                    "text": selected_exercise['text'],
                    "language": selected_exercise['language'],
                    "difficulty": selected_exercise['difficulty'],
                    "topic": selected_exercise['topic'],
                    "questions": json.loads(selected_exercise['questions'])
                }
            })
        else:
            return jsonify({
                "success": False,
                "error": "No exercises found"
            }), 404
    
    except Exception as e:
        log_exception(logger, f"Error in get_exercises endpoint: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route("/exercises/user", methods=["GET"])
def get_user_exercise():
    """
    Get the next exercise in the user's queue based on their progress.
    Requires authentication.
    """
    try:
        user = get_current_user()
        if not user:
            return jsonify({
                "success": False,
                "error": "Authentication required"
            }), 401
        
        exercise = get_next_exercise_for_user(user["user_id"])
        
        if exercise:
            return jsonify({
                "success": True,
                "exercise": exercise
            })
        else:
            return jsonify({
                "success": False,
                "error": "No more exercises in queue. All exercises completed!"
            }), 404
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route("/progress", methods=["POST"])
def submit_progress():
    """
    Submit reading progress and comprehension results.
    Updates user queue based on performance.
    """
    try:
        user = get_current_user()
        if not user:
            return jsonify({
                "success": False,
                "error": "Authentication required"
            }), 401
        
        data = request.json
        required_fields = ['exercise_id', 'comprehension_score', 'questions_answered', 'questions_correct']
        
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "success": False,
                    "error": f"Missing required field: {field}"
                }), 400
        
        exercise_id = data['exercise_id']
        comprehension_score = float(data['comprehension_score'])
        questions_answered = int(data['questions_answered'])
        questions_correct = int(data['questions_correct'])
        reading_speed_wpm = float(data.get('reading_speed_wpm', 0))
        session_duration_seconds = int(data.get('session_duration_seconds', 0))
        
        # Validate comprehension score
        if not 0.0 <= comprehension_score <= 1.0:
            return jsonify({
                "success": False,
                "error": "Comprehension score must be between 0.0 and 1.0"
            }), 400
        
        # Update progress and manage queue
        status = update_user_progress(
            user["user_id"], exercise_id, comprehension_score,
            questions_answered, questions_correct,
            reading_speed_wpm, session_duration_seconds
        )
        
        # Get next exercise for user
        next_exercise = get_next_exercise_for_user(user["user_id"])
        
        return jsonify({
            "success": True,
            "status": status,
            "comprehension_score": comprehension_score,
            "next_exercise": next_exercise,
            "message": "Progress updated successfully"
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route("/user/progress", methods=["GET"])
def get_user_progress():
    """
    Get user's reading progress and statistics.
    """
    try:
        user = get_current_user()
        if not user:
            return jsonify({
                "success": False,
                "error": "Authentication required"
            }), 401
        
        # Get user's progress statistics
        stats_result = execute_query('''
            SELECT 
                COUNT(*) as total_exercises,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_exercises,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_exercises,
                AVG(CASE WHEN status = 'completed' THEN comprehension_score ELSE NULL END) as avg_comprehension,
                AVG(reading_speed_wpm) as avg_reading_speed,
                SUM(session_duration_seconds) as total_reading_time
            FROM user_progress 
            WHERE user_id = ?
        ''', (user["user_id"],), fetch=True)
        
        stats = stats_result[0] if stats_result else {}
        
        # Get queue information
        queue_result = execute_query('''
            SELECT COUNT(*) as count FROM user_queue WHERE user_id = %s
        ''', (user["user_id"],), fetch=True)
        
        queue_count = queue_result[0]['count'] if queue_result else 0
        
        total_exercises = stats.get('total_exercises', 0)
        completed_exercises = stats.get('completed_exercises', 0)
        failed_exercises = stats.get('failed_exercises', 0)
        avg_comprehension = stats.get('avg_comprehension', 0.0)
        avg_reading_speed = stats.get('avg_reading_speed', 0.0)
        total_reading_time = stats.get('total_reading_time', 0)
        
        return jsonify({
            "success": True,
            "progress": {
                "total_exercises": total_exercises or 0,
                "completed_exercises": completed_exercises or 0,
                "failed_exercises": failed_exercises or 0,
                "queue_count": queue_count,
                "avg_comprehension": round(avg_comprehension or 0, 2),
                "avg_reading_speed": round(avg_reading_speed or 0, 1),
                "total_reading_time_seconds": total_reading_time or 0,
                "completion_rate": round((completed_exercises or 0) / max(total_exercises or 1, 1) * 100, 1)
            }
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/exercises/stats", methods=["GET"])
def get_exercise_stats():
    """Get statistics about available exercises"""
    try:
        # Get total count
        total_result = execute_query("SELECT COUNT(*) as count FROM exercises", fetch=True)
        total_count = total_result[0]['count'] if total_result else 0
        
        # Get count by language
        language_result = execute_query("SELECT language, COUNT(*) as count FROM exercises GROUP BY language", fetch=True)
        by_language = {row['language']: row['count'] for row in language_result} if language_result else {}
        
        # Get count by difficulty
        difficulty_result = execute_query("SELECT difficulty, COUNT(*) as count FROM exercises GROUP BY difficulty", fetch=True)
        by_difficulty = {row['difficulty']: row['count'] for row in difficulty_result} if difficulty_result else {}
        
        # Get count by topic
        topic_result = execute_query("SELECT topic, COUNT(*) as count FROM exercises GROUP BY topic", fetch=True)
        by_topic = {row['topic']: row['count'] for row in topic_result} if topic_result else {}
        
        return jsonify({
            "success": True,
            "stats": {
                "total": total_count,
                "by_language": by_language,
                "by_difficulty": by_difficulty,
                "by_topic": by_topic
            }
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/exercises/add", methods=["POST"])
def add_exercise():
    """Add a new exercise to the database"""
    try:
        data = request.json
        required_fields = ['title', 'text', 'questions']
        
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "success": False,
                    "error": f"Missing required field: {field}"
                }), 400
        
        execute_query('''
            INSERT INTO exercises (title, text, language, difficulty, topic, questions)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (
            data['title'],
            data['text'],
            data.get('language', 'en'),
            data.get('difficulty', 'intermediate'),
            data.get('topic', 'general'),
            json.dumps(data['questions'])
        ))
        
        # Get the new exercise ID
        new_exercise = execute_query('SELECT id FROM exercises WHERE title = %s AND text = %s', 
                                   (data['title'], data['text']), fetch=True)
        exercise_id = new_exercise[0]['id'] if new_exercise else None
        
        return jsonify({
            "success": True,
            "exercise_id": exercise_id,
            "message": "Exercise added successfully"
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/auth/register", methods=["POST"])
def register():
    """Register a new user"""
    try:
        data = request.json
        required_fields = ['username', 'email', 'password']
        
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "success": False,
                    "error": f"Missing required field: {field}"
                }), 400
        
        username = data['username'].strip()
        email = data['email'].strip().lower()
        password = data['password']
        preferred_language = data.get('preferred_language', 'en')
        
        # Validate input
        if len(username) < 3:
            return jsonify({
                "success": False,
                "error": "Username must be at least 3 characters long"
            }), 400
        
        if len(password) < 6:
            return jsonify({
                "success": False,
                "error": "Password must be at least 6 characters long"
            }), 400
        
        if '@' not in email:
            return jsonify({
                "success": False,
                "error": "Invalid email address"
            }), 400
        
        # Check if user already exists
        existing_user = execute_query('SELECT id FROM users WHERE username = %s OR email = %s', (username, email), fetch=True)
        if existing_user:
            return jsonify({
                "success": False,
                "error": "Username or email already exists"
            }), 400
        
        # Create user
        password_hash = hash_password(password)
        execute_query('''
            INSERT INTO users (username, email, password_hash, preferred_language)
            VALUES (%s, %s, %s, %s)
        ''', (username, email, password_hash, preferred_language))
        
        # Get the new user ID
        new_user = execute_query('SELECT id FROM users WHERE email = %s', (email,), fetch=True)
        user_id = new_user[0]['id'] if new_user else None
        
        if user_id:
            # Initialize user queue
            initialize_user_queue(user_id, preferred_language)
        
        # Generate session token
        session_token = generate_session_token()
        user_sessions[session_token] = {
            "user_id": user_id,
            "username": username,
            "email": email
        }
        
        return jsonify({
            "success": True,
            "message": "User registered successfully",
            "session_token": session_token,
            "user": {
                "id": user_id,
                "username": username,
                "email": email,
                "preferred_language": preferred_language
            }
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route("/auth/login", methods=["POST"])
def login():
    """Login user"""
    try:
        data = request.json
        required_fields = ['username', 'password']
        
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "success": False,
                    "error": f"Missing required field: {field}"
                }), 400
        
        username = data['username'].strip()
        password = data['password']
        
        # Find user by username or email
        user_result = execute_query('''
            SELECT id, username, email, password_hash, preferred_language 
            FROM users 
            WHERE username = %s OR email = %s
        ''', (username, username.lower()), fetch=True)
        
        if not user_result:
            return jsonify({
                "success": False,
                "error": "Invalid username or password"
            }), 401
        
        user = user_result[0]
        user_id = user['id']
        db_username = user['username']
        email = user['email']
        password_hash = user['password_hash']
        preferred_language = user['preferred_language']
        
        if not verify_password(password, password_hash):
            return jsonify({
                "success": False,
                "error": "Invalid username or password"
            }), 401
        
        # Generate session token
        session_token = generate_session_token()
        user_sessions[session_token] = {
            "user_id": user_id,
            "username": db_username,
            "email": email
        }
        
        # Update last login
        execute_query('UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = %s', (user_id,))
        
        return jsonify({
            "success": True,
            "message": "Login successful",
            "session_token": session_token,
            "user": {
                "id": user_id,
                "username": db_username,
                "email": email,
                "preferred_language": preferred_language
            }
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route("/auth/logout", methods=["POST"])
def logout():
    """Logout user"""
    try:
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if token in user_sessions:
            del user_sessions[token]
        
        return jsonify({
            "success": True,
            "message": "Logout successful"
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route("/auth/me", methods=["GET"])
def get_current_user_info():
    """Get current user information"""
    try:
        user = get_current_user()
        if not user:
            return jsonify({
                "success": False,
                "error": "Not authenticated"
            }), 401
        
        return jsonify({
            "success": True,
            "user": user
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# OAuth endpoints
@app.route("/auth/oauth/<provider>", methods=["GET"])
def oauth_login(provider):
    """Initiate OAuth login with specified provider"""
    try:
        if provider not in ['google', 'microsoft', 'apple']:
            return jsonify({
                "success": False,
                "error": "Unsupported OAuth provider"
            }), 400
        
        # Store preferred language in session
        preferred_language = request.args.get('language', 'en')
        session['preferred_language'] = preferred_language
        
        # Generate redirect URI
        redirect_uri = os.getenv('OAUTH_REDIRECT_URI', 'http://localhost:5001/auth/callback')
        
        if provider == 'apple':
            # Apple requires special handling
            client_secret = create_apple_client_secret()
            if not client_secret:
                return jsonify({
                    "success": False,
                    "error": "Apple OAuth not configured properly"
                }), 500
            
            # Use Authlib's Apple client
            client = oauth.apple
            return client.authorize_redirect(redirect_uri, client_secret=client_secret)
        else:
            # Standard OAuth flow for Google and Microsoft
            client = oauth.__getattr__(provider)
            return client.authorize_redirect(redirect_uri)
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route("/auth/callback", methods=["GET"])
def oauth_callback():
    """Handle OAuth callback from providers"""
    try:
        # Determine provider from request
        provider = None
        if 'google' in request.args.get('state', ''):
            provider = 'google'
        elif 'microsoft' in request.args.get('state', ''):
            provider = 'microsoft'
        elif 'apple' in request.args.get('state', ''):
            provider = 'apple'
        else:
            # Try to determine from the authorization response
            for p in ['google', 'microsoft', 'apple']:
                if hasattr(oauth, p):
                    try:
                        client = oauth.__getattr__(p)
                        token = client.authorize_access_token()
                        if token:
                            provider = p
                            break
                    except:
                        continue
        
        if not provider:
            return jsonify({
                "success": False,
                "error": "Could not determine OAuth provider"
            }), 400
        
        # Get user info from provider
        client = oauth.__getattr__(provider)
        
        if provider == 'apple':
            # Apple requires special handling
            client_secret = create_apple_client_secret()
            token = client.authorize_access_token(client_secret=client_secret)
        else:
            token = client.authorize_access_token()
        
        user_info = token.get('userinfo')
        if not user_info:
            return jsonify({
                "success": False,
                "error": "Could not retrieve user information"
            }), 400
        
        # Create or get user
        preferred_language = session.get('preferred_language', 'en')
        user_data = create_or_get_oauth_user(provider, user_info, preferred_language)
        
        # Generate session token
        session_token = generate_session_token()
        user_sessions[session_token] = user_data
        
        # Redirect to frontend with token
        frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
        return redirect(f"{frontend_url}/auth/callback?token={session_token}&success=true")
    
    except Exception as e:
        print(f"OAuth callback error: {e}")
        frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
        return redirect(f"{frontend_url}/auth/callback?success=false&error={str(e)}")

@app.route("/auth/oauth/providers", methods=["GET"])
def get_oauth_providers():
    """Get available OAuth providers"""
    providers = []
    
    if os.getenv('GOOGLE_CLIENT_ID') and os.getenv('GOOGLE_CLIENT_SECRET'):
        providers.append({
            "name": "google",
            "display_name": "Google",
            "icon": "🔍",
            "color": "#4285F4"
        })
    
    if os.getenv('MICROSOFT_CLIENT_ID') and os.getenv('MICROSOFT_CLIENT_SECRET'):
        providers.append({
            "name": "microsoft",
            "display_name": "Microsoft",
            "icon": "🏢",
            "color": "#00BCF2"
        })
    
    if os.getenv('APPLE_CLIENT_ID'):
        providers.append({
            "name": "apple",
            "display_name": "Apple",
            "icon": "🍎",
            "color": "#000000"
        })
    
    return jsonify({
        "success": True,
        "providers": providers
    })

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "service": "NoSubvo API",
        "version": "2.0",
        "endpoints": {
            "/auth/register": "POST - Register new user",
            "/auth/login": "POST - Login user",
            "/auth/logout": "POST - Logout user",
            "/auth/me": "GET - Get current user info",
            "/auth/oauth/<provider>": "GET - OAuth login (google, microsoft, apple)",
            "/auth/oauth/providers": "GET - Get available OAuth providers",
            "/auth/callback": "GET - OAuth callback handler",
            "/chunk": "POST - Process text into reading chunks",
            "/questions": "POST - Generate comprehension questions from text",
            "/exercises": "GET - Get random exercise (supports ?language=, ?difficulty=, ?topic=)",
            "/exercises/user": "GET - Get next exercise for authenticated user",
            "/exercises/stats": "GET - Get exercise statistics",
            "/exercises/add": "POST - Add new exercise to database",
            "/progress": "POST - Submit reading progress",
            "/health": "GET - Check service health"
        }
    })


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "message": "Service is running"})


@app.route("/chunk", methods=["POST"])
def chunk():
    """
    Endpoint to chunk text for subvocalization reduction.
    Accepts JSON with 'text' field or file upload.
    """
    try:
        if request.content_type and 'application/json' in request.content_type:
            data = request.json
            text = data.get("text", "")
        elif 'file' in request.files:
            text = request.files['file'].read().decode("utf-8")
        else:
            return jsonify({
                "error": "Send 'text' as JSON or 'file' as txt upload"
            }), 400

        if not text or not text.strip():
            return jsonify({"error": "Text cannot be empty"}), 400

        chunks = chunk_text_smart(text)
        
        return jsonify({
            "success": True,
            "chunks": chunks,
            "chunk_count": len(chunks),
            "original_length": len(text)
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/questions", methods=["POST"])
def generate_questions():
    """
    Generate comprehension questions from the provided text.
    """
    try:
        if request.content_type and 'application/json' in request.content_type:
            data = request.json
            text = data.get("text", "")
            num_questions = data.get("num_questions", 3)
        else:
            return jsonify({
                "error": "Send JSON with 'text' field"
            }), 400

        if not text or not text.strip():
            return jsonify({"error": "Text cannot be empty"}), 400

        questions = generate_comprehension_questions(text, num_questions)
        
        return jsonify({
            "success": True,
            "questions": questions,
            "question_count": len(questions)
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


if __name__ == "__main__":
    print("🚀 NoSubvo Backend API starting...")
    print("📚 Loading spaCy model...")
    print("✅ Ready! Access at http://localhost:5001")
    app.run(debug=True, host='0.0.0.0', port=5001)


