from flask import Flask, request, jsonify, redirect, url_for, session
from flask_cors import CORS
import spacy
import openai
import os
from dotenv import load_dotenv
import json
import sqlite3
import random
from datetime import datetime
import hashlib
import secrets
import uuid
import jwt
from authlib.integrations.flask_client import OAuth
from authlib.common.security import generate_token
import requests

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Load environment variables
load_dotenv()

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
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
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
    cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
    existing_user = cursor.fetchone()
    
    if existing_user:
        user_id = existing_user[0]
        # Update last login
        cursor.execute('UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?', (user_id,))
    else:
        # Create new user
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, preferred_language, created_at, last_login)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ''', (username, email, f"oauth_{provider}", preferred_language))
        
        user_id = cursor.lastrowid
        
        # Initialize user queue
        initialize_user_queue(user_id, preferred_language)
    
    # Get user details
    cursor.execute('SELECT username, email, preferred_language FROM users WHERE id = ?', (user_id,))
    user_data = cursor.fetchone()
    
    conn.commit()
    conn.close()
    
    return {
        "user_id": user_id,
        "username": user_data[0],
        "email": user_data[1],
        "preferred_language": user_data[2]
    }

def initialize_user_queue(user_id: int, preferred_language: str = 'en'):
    """Initialize user queue with all available exercises in their preferred language"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Get all exercises in user's preferred language
    cursor.execute('''
        SELECT id FROM exercises 
        WHERE language = ? 
        AND id NOT IN (SELECT exercise_id FROM user_progress WHERE user_id = ? AND status = 'completed')
        ORDER BY difficulty, RANDOM()
    ''', (preferred_language, user_id))
    
    exercises = cursor.fetchall()
    
    # Add exercises to user queue
    for position, (exercise_id,) in enumerate(exercises, 1):
        cursor.execute('''
            INSERT OR IGNORE INTO user_queue (user_id, exercise_id, queue_position)
            VALUES (?, ?, ?)
        ''', (user_id, exercise_id, position))
    
    conn.commit()
    conn.close()

def get_next_exercise_for_user(user_id: int):
    """Get the next exercise in user's queue"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Get the first exercise in queue
    cursor.execute('''
        SELECT e.id, e.title, e.text, e.language, e.difficulty, e.topic, e.questions
        FROM exercises e
        JOIN user_queue uq ON e.id = uq.exercise_id
        WHERE uq.user_id = ? AND uq.queue_position = 1
    ''', (user_id,))
    
    exercise = cursor.fetchone()
    conn.close()
    
    if exercise:
        exercise_id, title, text, lang, diff, topic, questions_json = exercise
        return {
            "id": exercise_id,
            "title": title,
            "text": text,
            "language": lang,
            "difficulty": diff,
            "topic": topic,
            "questions": json.loads(questions_json)
        }
    return None

def update_user_progress(user_id: int, exercise_id: int, comprehension_score: float, 
                        questions_answered: int, questions_correct: int, 
                        reading_speed_wpm: float, session_duration_seconds: int):
    """Update user progress and manage queue based on comprehension score"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Determine status based on comprehension score
    status = 'completed' if comprehension_score >= 0.7 else 'failed'
    
    # Update or insert progress
    cursor.execute('''
        INSERT OR REPLACE INTO user_progress 
        (user_id, exercise_id, status, comprehension_score, questions_answered, 
         questions_correct, reading_speed_wpm, session_duration_seconds, completed_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    ''', (user_id, exercise_id, status, comprehension_score, questions_answered, 
          questions_correct, reading_speed_wpm, session_duration_seconds))
    
    # Remove from queue if completed successfully
    if status == 'completed':
        cursor.execute('DELETE FROM user_queue WHERE user_id = ? AND exercise_id = ?', 
                      (user_id, exercise_id))
        
        # Reorder remaining queue items
        cursor.execute('''
            UPDATE user_queue 
            SET queue_position = queue_position - 1 
            WHERE user_id = ? AND queue_position > 1
        ''', (user_id,))
    else:
        # Move failed exercise to bottom of queue
        cursor.execute('''
            UPDATE user_queue 
            SET queue_position = (SELECT MAX(queue_position) + 1 FROM user_queue WHERE user_id = ?)
            WHERE user_id = ? AND exercise_id = ?
        ''', (user_id, user_id, exercise_id))
    
    conn.commit()
    conn.close()
    
    return status

# Initialize OpenAI client (optional)
openai_api_key = os.getenv("OPENAI_API_KEY")
if openai_api_key:
    openai_client = openai.OpenAI(api_key=openai_api_key)
else:
    openai_client = None
    print("⚠️  OpenAI API key not found. Question generation will use fallback questions.")

# Database configuration
DATABASE_PATH = 'exercises.db'

def init_database():
    """Initialize the SQLite database with exercises and user tables"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Create exercises table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS exercises (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            text TEXT NOT NULL,
            language TEXT DEFAULT 'en',
            difficulty TEXT DEFAULT 'intermediate',
            topic TEXT DEFAULT 'general',
            questions TEXT NOT NULL,  -- JSON string of questions
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            preferred_language TEXT DEFAULT 'en',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create user_progress table to track reading sessions and comprehension
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            exercise_id INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending', -- pending, completed, failed
            comprehension_score REAL DEFAULT 0.0, -- 0.0 to 1.0
            questions_answered INTEGER DEFAULT 0,
            questions_correct INTEGER DEFAULT 0,
            reading_speed_wpm REAL DEFAULT 0.0,
            session_duration_seconds INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (exercise_id) REFERENCES exercises (id),
            UNIQUE(user_id, exercise_id)
        )
    ''')
    
    # Create user_queue table to manage text queue for each user
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            exercise_id INTEGER NOT NULL,
            queue_position INTEGER NOT NULL,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (exercise_id) REFERENCES exercises (id),
            UNIQUE(user_id, exercise_id)
        )
    ''')
    
    # Create indexes for better performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_language ON exercises(language)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_difficulty ON exercises(difficulty)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_topic ON exercises(topic)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_progress_user_id ON user_progress(user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_progress_status ON user_progress(status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_queue_user_id ON user_queue(user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_queue_position ON user_queue(queue_position)')
    
    conn.commit()
    conn.close()

def insert_sample_exercises():
    """Insert sample exercises into the database"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Check if exercises already exist
    cursor.execute('SELECT COUNT(*) FROM exercises')
    count = cursor.fetchone()[0]
    
    # Always add English exercises if they don't exist
    cursor.execute('SELECT COUNT(*) FROM exercises WHERE language = ?', ('en',))
    en_count = cursor.fetchone()[0]
    
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
            },
            {
                'title': 'Human Brain and Neural Plasticity',
                'text': 'The human brain contains approximately 86 billion neurons, each capable of forming thousands of connections with other neurons. This creates a complex network that processes information at incredible speeds. Neural plasticity, the brain\'s ability to reorganize itself, allows us to learn new skills throughout our lives. Recent research shows that reading regularly can increase neural connectivity and even help prevent cognitive decline as we age.',
                'language': 'en',
                'difficulty': 'intermediate',
                'topic': 'science',
                'questions': json.dumps([
                    {
                        "question": "How many neurons does the human brain contain?",
                        "options": {
                            "A": "86 million",
                            "B": "86 billion",
                            "C": "860 billion",
                            "D": "8.6 billion"
                        },
                        "answer": "B"
                    },
                    {
                        "question": "What is neural plasticity?",
                        "options": {
                            "A": "The brain's ability to reorganize itself",
                            "B": "The speed of neural connections",
                            "C": "The number of neurons in the brain",
                            "D": "The brain's processing power"
                        },
                        "answer": "A"
                    },
                    {
                        "question": "What benefit does regular reading provide according to recent research?",
                        "options": {
                            "A": "It increases brain size",
                            "B": "It increases neural connectivity and helps prevent cognitive decline",
                            "C": "It reduces the need for sleep",
                            "D": "It improves physical strength"
                        },
                        "answer": "B"
                    }
                ])
            },
            {
                'title': 'Climate Change and Global Impact',
                'text': 'Climate change is one of the most pressing challenges of our time, affecting ecosystems, weather patterns, and human societies worldwide. Rising global temperatures lead to melting ice caps, rising sea levels, and more frequent extreme weather events. Scientists agree that human activities, particularly the burning of fossil fuels, are the primary driver of current climate change. Transitioning to renewable energy sources and implementing sustainable practices are crucial steps in addressing this global crisis.',
                'language': 'en',
                'difficulty': 'advanced',
                'topic': 'environment',
                'questions': json.dumps([
                    {
                        "question": "What is identified as the primary driver of current climate change?",
                        "options": {
                            "A": "Natural weather cycles",
                            "B": "Solar radiation changes",
                            "C": "Human activities, particularly burning fossil fuels",
                            "D": "Volcanic activity"
                        },
                        "answer": "C"
                    },
                    {
                        "question": "Which of the following is NOT mentioned as a consequence of rising global temperatures?",
                        "options": {
                            "A": "Melting ice caps",
                            "B": "Rising sea levels",
                            "C": "More frequent extreme weather events",
                            "D": "Increased rainfall everywhere"
                        },
                        "answer": "D"
                    },
                    {
                        "question": "What are mentioned as crucial steps in addressing climate change?",
                        "options": {
                            "A": "Building more factories",
                            "B": "Transitioning to renewable energy and implementing sustainable practices",
                            "C": "Increasing fossil fuel use",
                            "D": "Ignoring the problem"
                        },
                        "answer": "B"
                    }
                ])
            }
        ]
        
        for exercise in english_exercises:
            cursor.execute('''
                INSERT INTO exercises (title, text, language, difficulty, topic, questions)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                exercise['title'],
                exercise['text'],
                exercise['language'],
                exercise['difficulty'],
                exercise['topic'],
                exercise['questions']
            ))
    
    if count == 0:
        sample_exercises = [
            {
                'title': 'Artificial Intelligence in Healthcare',
                'text': 'Artificial intelligence is revolutionizing healthcare by providing faster and more accurate diagnoses. Machine learning algorithms can analyze medical images, predict patient outcomes, and assist doctors in treatment decisions. This technology has the potential to improve patient care while reducing costs and medical errors.',
                'language': 'es',
                'difficulty': 'intermediate',
                'topic': 'technology',
                'questions': json.dumps([
                    {
                        "question": "¿Cómo está revolucionando la inteligencia artificial la atención médica?",
                        "options": {
                            "A": "Reduciendo el personal médico",
                            "B": "Proporcionando diagnósticos más rápidos y precisos",
                            "C": "Eliminando la necesidad de doctores",
                            "D": "Aumentando los costos médicos"
                        },
                        "answer": "B"
                    }
                ])
            }
        ]
        
        for exercise in sample_exercises:
            cursor.execute('''
                INSERT INTO exercises (title, text, language, difficulty, topic, questions)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                exercise['title'],
                exercise['text'],
                exercise['language'],
                exercise['difficulty'],
                exercise['topic'],
                exercise['questions']
            ))
        
        conn.commit()
    
    conn.close()

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
        
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Build query with optional filters
        query = "SELECT id, title, text, language, difficulty, topic, questions FROM exercises WHERE language = ?"
        params = [language]
        
        if difficulty:
            query += " AND difficulty = ?"
            params.append(difficulty)
        
        if topic:
            query += " AND topic = ?"
            params.append(topic)
        
        cursor.execute(query, params)
        exercises = cursor.fetchall()
        
        if not exercises:
            # Fallback to any language if no exercises found
            cursor.execute("SELECT id, title, text, language, difficulty, topic, questions FROM exercises")
            exercises = cursor.fetchall()
        
        if exercises:
            # Select random exercise
            selected_exercise = random.choice(exercises)
            exercise_id, title, text, lang, diff, top, questions_json = selected_exercise
            
            return jsonify({
                "success": True,
                "exercise": {
                    "id": exercise_id,
                    "title": title,
                    "text": text,
                    "language": lang,
                    "difficulty": diff,
                    "topic": top,
                    "questions": json.loads(questions_json)
                }
            })
        else:
            return jsonify({
                "success": False,
                "error": "No exercises found"
            }), 404
        
        conn.close()
    
    except Exception as e:
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
        
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Get user's progress statistics
        cursor.execute('''
            SELECT 
                COUNT(*) as total_exercises,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_exercises,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_exercises,
                AVG(CASE WHEN status = 'completed' THEN comprehension_score ELSE NULL END) as avg_comprehension,
                AVG(reading_speed_wpm) as avg_reading_speed,
                SUM(session_duration_seconds) as total_reading_time
            FROM user_progress 
            WHERE user_id = ?
        ''', (user["user_id"],))
        
        stats = cursor.fetchone()
        
        # Get queue information
        cursor.execute('''
            SELECT COUNT(*) FROM user_queue WHERE user_id = ?
        ''', (user["user_id"],))
        
        queue_count = cursor.fetchone()[0]
        
        conn.close()
        
        total_exercises, completed_exercises, failed_exercises, avg_comprehension, avg_reading_speed, total_reading_time = stats
        
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
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Get total count
        cursor.execute("SELECT COUNT(*) FROM exercises")
        total_count = cursor.fetchone()[0]
        
        # Get count by language
        cursor.execute("SELECT language, COUNT(*) FROM exercises GROUP BY language")
        by_language = dict(cursor.fetchall())
        
        # Get count by difficulty
        cursor.execute("SELECT difficulty, COUNT(*) FROM exercises GROUP BY difficulty")
        by_difficulty = dict(cursor.fetchall())
        
        # Get count by topic
        cursor.execute("SELECT topic, COUNT(*) FROM exercises GROUP BY topic")
        by_topic = dict(cursor.fetchall())
        
        conn.close()
        
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
        
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO exercises (title, text, language, difficulty, topic, questions)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            data['title'],
            data['text'],
            data.get('language', 'en'),
            data.get('difficulty', 'intermediate'),
            data.get('topic', 'general'),
            json.dumps(data['questions'])
        ))
        
        exercise_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
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
        
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Check if user already exists
        cursor.execute('SELECT id FROM users WHERE username = ? OR email = ?', (username, email))
        if cursor.fetchone():
            conn.close()
            return jsonify({
                "success": False,
                "error": "Username or email already exists"
            }), 400
        
        # Create user
        password_hash = hash_password(password)
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, preferred_language)
            VALUES (?, ?, ?, ?)
        ''', (username, email, password_hash, preferred_language))
        
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
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
        
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Find user by username or email
        cursor.execute('''
            SELECT id, username, email, password_hash, preferred_language 
            FROM users 
            WHERE username = ? OR email = ?
        ''', (username, username.lower()))
        
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            return jsonify({
                "success": False,
                "error": "Invalid username or password"
            }), 401
        
        user_id, db_username, email, password_hash, preferred_language = user
        
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
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?', (user_id,))
        conn.commit()
        conn.close()
        
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


