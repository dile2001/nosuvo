"""
Database configuration and connection management for NoSubvo
PostgreSQL only - Production-ready configuration
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from dotenv import load_dotenv
from typing import Optional, Dict, Any, List, Tuple
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Load environment variables
# Load .env.local first (takes precedence), then .env
env_local_path = Path('.env.local')
env_path = Path('.env')

if env_local_path.exists():
    load_dotenv(dotenv_path=env_local_path, override=True)
    logger.info("Loaded configuration from .env.local")
elif env_path.exists():
    load_dotenv(dotenv_path=env_path)
    logger.info("Loaded configuration from .env")
else:
    load_dotenv()  # Try default locations
    logger.warning("No .env or .env.local file found, using system environment variables")

class DatabaseConfig:
    """PostgreSQL database configuration manager"""
    
    def __init__(self):
        # PostgreSQL settings
        self.db_host = os.getenv('DB_HOST', 'localhost')
        self.db_port = int(os.getenv('DB_PORT', 5432))
        self.db_name = os.getenv('DB_NAME', 'nosuvo_db')
        self.db_user = os.getenv('DB_USER', 'postgres')
        self.db_password = os.getenv('DB_PASSWORD', '')
        
        # Connection string (optional, for compatibility)
        self.database_url = os.getenv('DATABASE_URL')
        
    def get_connection_params(self) -> Dict[str, Any]:
        """Get PostgreSQL connection parameters"""
        if self.database_url:
            # Parse DATABASE_URL if provided
            return {'dsn': self.database_url}
        else:
            return {
                'host': self.db_host,
                'port': self.db_port,
                'database': self.db_name,
                'user': self.db_user,
                'password': self.db_password
            }

# Global database configuration
db_config = DatabaseConfig()

@contextmanager
def get_db_connection():
    """
    Context manager for PostgreSQL database connections
    Automatically handles connection and cleanup
    """
    connection = None
    try:
        connection = psycopg2.connect(
            **db_config.get_connection_params(),
            cursor_factory=RealDictCursor
        )
        connection.autocommit = False
        
        yield connection
        
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        if connection:
            connection.rollback()
        raise
    finally:
        if connection:
            connection.close()

@contextmanager
def get_db_cursor():
    """
    Context manager for database cursors
    Automatically handles connection and cursor lifecycle
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            yield cursor, conn
        except Exception as e:
            logger.error(f"Database cursor error: {e}")
            conn.rollback()
            raise
        finally:
            cursor.close()

def execute_query(query: str, params: Optional[Tuple] = None, fetch: bool = False) -> Optional[List[Dict[str, Any]]]:
    """
    Execute a PostgreSQL query with automatic connection management
    
    Args:
        query: SQL query string (using %s for parameters)
        params: Query parameters tuple
        fetch: Whether to fetch results
    
    Returns:
        Query results if fetch=True, otherwise None
    """
    with get_db_cursor() as (cursor, conn):
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            if fetch:
                results = cursor.fetchall()
                # RealDictCursor returns dict-like objects
                return [dict(row) for row in results]
            else:
                conn.commit()
                return None
                
        except Exception as e:
            logger.error(f"Query execution error: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Params: {params}")
            conn.rollback()
            raise

def execute_many(query: str, params_list: List[Tuple]) -> None:
    """
    Execute a query multiple times with different parameters
    
    Args:
        query: SQL query string
        params_list: List of parameter tuples
    """
    with get_db_cursor() as (cursor, conn):
        try:
            cursor.executemany(query, params_list)
            conn.commit()
        except Exception as e:
            logger.error(f"Batch execution error: {e}")
            conn.rollback()
            raise

def test_connection() -> bool:
    """
    Test PostgreSQL connection
    
    Returns:
        True if connection successful, False otherwise
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT version()")
            version = cursor.fetchone()
            cursor.close()
            logger.info(f"PostgreSQL connection successful: {version['version']}")
        return True
    except Exception as e:
        logger.error(f"PostgreSQL connection test failed: {e}")
        return False

def get_database_info() -> Dict[str, Any]:
    """
    Get information about the current database configuration
    
    Returns:
        Dictionary with database information
    """
    return {
        'type': 'postgresql',
        'host': db_config.db_host,
        'port': db_config.db_port,
        'database': db_config.db_name,
        'user': db_config.db_user,
        'connection_params': db_config.get_connection_params()
    }

def init_database_schema():
    """
    Initialize the PostgreSQL database schema
    Creates all necessary tables and indexes
    """
    with get_db_cursor() as (cursor, conn):
        try:
            # Create exercises table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS exercises (
                    id SERIAL PRIMARY KEY,
                    title TEXT NOT NULL,
                    text TEXT NOT NULL,
                    language TEXT DEFAULT 'en',
                    difficulty TEXT DEFAULT 'intermediate',
                    topic TEXT DEFAULT 'general',
                    questions TEXT NOT NULL,
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
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                    FOREIGN KEY (exercise_id) REFERENCES exercises (id) ON DELETE CASCADE,
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
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                    FOREIGN KEY (exercise_id) REFERENCES exercises (id) ON DELETE CASCADE,
                    UNIQUE(user_id, exercise_id)
                )
            """)
            
            # Create indexes for better performance
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_exercises_language ON exercises(language)",
                "CREATE INDEX IF NOT EXISTS idx_exercises_difficulty ON exercises(difficulty)",
                "CREATE INDEX IF NOT EXISTS idx_exercises_topic ON exercises(topic)",
                "CREATE INDEX IF NOT EXISTS idx_user_progress_user_id ON user_progress(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_user_progress_exercise_id ON user_progress(exercise_id)",
                "CREATE INDEX IF NOT EXISTS idx_user_progress_status ON user_progress(status)",
                "CREATE INDEX IF NOT EXISTS idx_user_queue_user_id ON user_queue(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_user_queue_position ON user_queue(queue_position)"
            ]
            
            for index_sql in indexes:
                cursor.execute(index_sql)
            
            conn.commit()
            logger.info("Database schema initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database schema: {e}")
            conn.rollback()
            raise

if __name__ == "__main__":
    # Test the database configuration
    logging.basicConfig(level=logging.INFO)
    
    print("PostgreSQL Database Configuration:")
    print("=" * 50)
    info = get_database_info()
    print(f"Host: {info['host']}")
    print(f"Port: {info['port']}")
    print(f"Database: {info['database']}")
    print(f"User: {info['user']}")
    print()
    
    # Test connection
    if test_connection():
        print("✅ PostgreSQL connection successful")
        
        # Try to get version
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT version()")
                version = cursor.fetchone()
                print(f"PostgreSQL Version: {version['version'].split(',')[0]}")
                cursor.close()
        except Exception as e:
            print(f"⚠️  Could not get version: {e}")
    else:
        print("❌ PostgreSQL connection failed")
        print("\nPlease ensure:")
        print("1. PostgreSQL is installed and running")
        print("2. Database 'nosuvo_db' exists (or create it with: createdb nosuvo_db)")
        print("3. .env.local has correct DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD")
