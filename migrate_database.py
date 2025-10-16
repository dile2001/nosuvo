"""
Database migration scripts for NoSubvo
Handles migration from SQLite to PostgreSQL
"""

import os
import sys
import sqlite3
import psycopg2
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging
from dotenv import load_dotenv

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import db_config, get_db_connection, execute_query, test_connection

load_dotenv()
logger = logging.getLogger(__name__)

class DatabaseMigrator:
    """Handles database migrations between SQLite and PostgreSQL"""
    
    def __init__(self):
        self.sqlite_path = 'exercises.db'
        self.backup_path = f'exercises_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
    
    def create_backup(self) -> bool:
        """Create a backup of the SQLite database"""
        try:
            import shutil
            shutil.copy2(self.sqlite_path, self.backup_path)
            logger.info(f"Backup created: {self.backup_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return False
    
    def get_sqlite_data(self) -> Dict[str, List[Dict[str, Any]]]:
        """Extract all data from SQLite database"""
        data = {}
        
        try:
            conn = sqlite3.connect(self.sqlite_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get all table names
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            for table in tables:
                cursor.execute(f"SELECT * FROM {table}")
                rows = cursor.fetchall()
                data[table] = [dict(row) for row in rows]
                logger.info(f"Extracted {len(rows)} rows from {table}")
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to extract SQLite data: {e}")
            raise
        
        return data
    
    def create_postgresql_schema(self) -> bool:
        """Create PostgreSQL schema"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Create exercises table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS exercises (
                        id SERIAL PRIMARY KEY,
                        title TEXT NOT NULL,
                        content TEXT NOT NULL,
                        language TEXT NOT NULL,
                        difficulty_level INTEGER DEFAULT 1,
                        word_count INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create users table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        username TEXT UNIQUE NOT NULL,
                        email TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        preferred_language TEXT DEFAULT 'en',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create user_progress table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS user_progress (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        exercise_id INTEGER NOT NULL,
                        status TEXT NOT NULL DEFAULT 'pending',
                        comprehension_score REAL DEFAULT 0.0,
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
                """)
                
                # Create user_queue table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS user_queue (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        exercise_id INTEGER NOT NULL,
                        queue_position INTEGER NOT NULL,
                        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (id),
                        FOREIGN KEY (exercise_id) REFERENCES exercises (id),
                        UNIQUE(user_id, exercise_id)
                    )
                """)
                
                # Create indexes for better performance
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_exercises_language ON exercises(language)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_exercises_difficulty ON exercises(difficulty_level)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_progress_user_id ON user_progress(user_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_progress_exercise_id ON user_progress(exercise_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_progress_status ON user_progress(status)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_queue_user_id ON user_queue(user_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_queue_position ON user_queue(queue_position)")
                
                conn.commit()
                cursor.close()
                
                logger.info("PostgreSQL schema created successfully")
                return True
                
        except Exception as e:
            logger.error(f"Failed to create PostgreSQL schema: {e}")
            return False
    
    def migrate_data(self, data: Dict[str, List[Dict[str, Any]]]) -> bool:
        """Migrate data from SQLite to PostgreSQL"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Migrate exercises
                if 'exercises' in data and data['exercises']:
                    logger.info(f"Migrating {len(data['exercises'])} exercises...")
                    for exercise in data['exercises']:
                        cursor.execute("""
                            INSERT INTO exercises (id, title, content, language, difficulty_level, word_count, created_at, updated_at)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (id) DO NOTHING
                        """, (
                            exercise['id'],
                            exercise['title'],
                            exercise['content'],
                            exercise['language'],
                            exercise.get('difficulty_level', 1),
                            exercise.get('word_count', 0),
                            exercise.get('created_at'),
                            exercise.get('updated_at')
                        ))
                
                # Migrate users
                if 'users' in data and data['users']:
                    logger.info(f"Migrating {len(data['users'])} users...")
                    for user in data['users']:
                        cursor.execute("""
                            INSERT INTO users (id, username, email, password_hash, preferred_language, created_at, last_login)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (id) DO NOTHING
                        """, (
                            user['id'],
                            user['username'],
                            user['email'],
                            user['password_hash'],
                            user.get('preferred_language', 'en'),
                            user.get('created_at'),
                            user.get('last_login')
                        ))
                
                # Migrate user_progress
                if 'user_progress' in data and data['user_progress']:
                    logger.info(f"Migrating {len(data['user_progress'])} user progress records...")
                    for progress in data['user_progress']:
                        cursor.execute("""
                            INSERT INTO user_progress (id, user_id, exercise_id, status, comprehension_score, 
                                                     questions_answered, questions_correct, reading_speed_wpm, 
                                                     session_duration_seconds, created_at, completed_at)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (id) DO NOTHING
                        """, (
                            progress['id'],
                            progress['user_id'],
                            progress['exercise_id'],
                            progress.get('status', 'pending'),
                            progress.get('comprehension_score', 0.0),
                            progress.get('questions_answered', 0),
                            progress.get('questions_correct', 0),
                            progress.get('reading_speed_wpm', 0.0),
                            progress.get('session_duration_seconds', 0),
                            progress.get('created_at'),
                            progress.get('completed_at')
                        ))
                
                # Migrate user_queue
                if 'user_queue' in data and data['user_queue']:
                    logger.info(f"Migrating {len(data['user_queue'])} user queue records...")
                    for queue_item in data['user_queue']:
                        cursor.execute("""
                            INSERT INTO user_queue (id, user_id, exercise_id, queue_position, added_at)
                            VALUES (%s, %s, %s, %s, %s)
                            ON CONFLICT (id) DO NOTHING
                        """, (
                            queue_item['id'],
                            queue_item['user_id'],
                            queue_item['exercise_id'],
                            queue_item['queue_position'],
                            queue_item.get('added_at')
                        ))
                
                conn.commit()
                cursor.close()
                
                logger.info("Data migration completed successfully")
                return True
                
        except Exception as e:
            logger.error(f"Failed to migrate data: {e}")
            return False
    
    def verify_migration(self) -> bool:
        """Verify that the migration was successful"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Check table counts
                tables = ['exercises', 'users', 'user_progress', 'user_queue']
                for table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    logger.info(f"Table {table}: {count} records")
                
                cursor.close()
                return True
                
        except Exception as e:
            logger.error(f"Failed to verify migration: {e}")
            return False
    
    def run_migration(self) -> bool:
        """Run the complete migration process"""
        logger.info("Starting database migration...")
        
        # Step 1: Create backup
        if not self.create_backup():
            logger.error("Failed to create backup. Aborting migration.")
            return False
        
        # Step 2: Test PostgreSQL connection
        if not test_connection():
            logger.error("PostgreSQL connection failed. Aborting migration.")
            return False
        
        # Step 3: Extract SQLite data
        try:
            data = self.get_sqlite_data()
        except Exception as e:
            logger.error(f"Failed to extract SQLite data: {e}")
            return False
        
        # Step 4: Create PostgreSQL schema
        if not self.create_postgresql_schema():
            logger.error("Failed to create PostgreSQL schema. Aborting migration.")
            return False
        
        # Step 5: Migrate data
        if not self.migrate_data(data):
            logger.error("Failed to migrate data. Aborting migration.")
            return False
        
        # Step 6: Verify migration
        if not self.verify_migration():
            logger.error("Migration verification failed.")
            return False
        
        logger.info("Database migration completed successfully!")
        logger.info(f"Backup created at: {self.backup_path}")
        return True

def main():
    """Main migration function"""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    migrator = DatabaseMigrator()
    
    print("NoSubvo Database Migration Tool")
    print("=" * 40)
    print(f"Source: SQLite ({migrator.sqlite_path})")
    print(f"Target: PostgreSQL ({db_config.get_connection_string()})")
    print()
    
    # Check if SQLite database exists
    if not os.path.exists(migrator.sqlite_path):
        print(f"❌ SQLite database not found: {migrator.sqlite_path}")
        return False
    
    # Confirm migration
    response = input("Do you want to proceed with the migration? (y/N): ")
    if response.lower() != 'y':
        print("Migration cancelled.")
        return False
    
    # Run migration
    success = migrator.run_migration()
    
    if success:
        print("✅ Migration completed successfully!")
        print(f"📁 Backup created: {migrator.backup_path}")
        print("🔄 Update your .env file to use PostgreSQL")
    else:
        print("❌ Migration failed. Check the logs for details.")
    
    return success

if __name__ == "__main__":
    main()
