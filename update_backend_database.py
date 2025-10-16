"""
Database migration script to update backend.py to use PostgreSQL/SQLite abstraction
This script updates all database calls in backend.py to use our new database configuration
"""

import re
import os

def update_backend_database_calls():
    """Update backend.py to use the new database configuration"""
    
    backend_file = '/Users/dile/labs/nosuvo/backend.py'
    
    # Read the current file
    with open(backend_file, 'r') as f:
        content = f.read()
    
    # Replace sqlite3.connect calls with our database abstraction
    # Pattern 1: Direct sqlite3.connect calls
    sqlite_pattern = r'conn = sqlite3\.connect\([^)]+\)'
    sqlite_replacement = 'with get_db_connection() as conn:'
    
    # Pattern 2: cursor = conn.cursor()
    cursor_pattern = r'cursor = conn\.cursor\(\)'
    cursor_replacement = 'cursor = conn.cursor()'
    
    # Pattern 3: conn.commit()
    commit_pattern = r'conn\.commit\(\)'
    commit_replacement = 'conn.commit()'
    
    # Pattern 4: conn.close()
    close_pattern = r'conn\.close\(\)'
    close_replacement = '# conn.close() - handled by context manager'
    
    # Pattern 5: cursor.execute with parameters
    execute_pattern = r'cursor\.execute\(([^)]+)\)'
    
    # Apply replacements
    content = re.sub(sqlite_pattern, sqlite_replacement, content)
    content = re.sub(close_pattern, close_replacement, content)
    
    # Update specific functions that need special handling
    content = update_specific_functions(content)
    
    # Write the updated content
    with open(backend_file, 'w') as f:
        f.write(content)
    
    print("✅ Updated backend.py to use new database configuration")

def update_specific_functions(content):
    """Update specific functions that need special handling"""
    
    # Update insert_sample_exercises function
    insert_pattern = r'(def insert_sample_exercises\(\):.*?)(conn = sqlite3\.connect.*?conn\.close\(\))'
    
    def replace_insert_function(match):
        func_start = match.group(1)
        old_db_code = match.group(2)
        
        new_code = '''def insert_sample_exercises():
    """Insert sample exercises into the database"""
    # Check if exercises already exist
    count_result = execute_query('SELECT COUNT(*) FROM exercises', fetch=True)
    count = count_result[0]['count'] if count_result else 0
    
    # Always add English exercises if they don't exist
    en_result = execute_query('SELECT COUNT(*) FROM exercises WHERE language = ?', ('en',), fetch=True)
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
                VALUES (?, ?, ?, ?, ?, ?)
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
        print("📚 Database initialized with sample exercises")'''
        
        return new_code
    
    content = re.sub(insert_pattern, replace_insert_function, content, flags=re.DOTALL)
    
    return content

if __name__ == "__main__":
    update_backend_database_calls()
