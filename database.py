"""
Database configuration and connection management for NoSubvo
Supports both SQLite (development) and PostgreSQL (production)
"""

import os
import psycopg2
import sqlite3
from contextlib import contextmanager
from dotenv import load_dotenv
from typing import Optional, Dict, Any, List, Tuple
import logging

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class DatabaseConfig:
    """Database configuration manager"""
    
    def __init__(self):
        self.db_type = os.getenv('DB_TYPE', 'sqlite')  # 'sqlite' or 'postgresql'
        self.database_url = os.getenv('DATABASE_URL')
        
        # PostgreSQL settings
        self.db_host = os.getenv('DB_HOST', 'localhost')
        self.db_port = int(os.getenv('DB_PORT', 5432))
        self.db_name = os.getenv('DB_NAME', 'nosuvo_db')
        self.db_user = os.getenv('DB_USER', 'postgres')
        self.db_password = os.getenv('DB_PASSWORD', '')
        
        # SQLite settings
        self.sqlite_path = os.getenv('SQLITE_PATH', 'exercises.db')
        
    def get_connection_string(self) -> str:
        """Get the appropriate connection string based on configuration"""
        if self.db_type == 'postgresql':
            if self.database_url:
                return self.database_url
            else:
                return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
        else:
            return self.sqlite_path
    
    def is_postgresql(self) -> bool:
        """Check if using PostgreSQL"""
        return self.db_type == 'postgresql'
    
    def is_sqlite(self) -> bool:
        """Check if using SQLite"""
        return self.db_type == 'sqlite'

# Global database configuration
db_config = DatabaseConfig()

@contextmanager
def get_db_connection():
    """
    Context manager for database connections
    Automatically handles both SQLite and PostgreSQL
    """
    connection = None
    try:
        if db_config.is_postgresql():
            connection = psycopg2.connect(
                host=db_config.db_host,
                port=db_config.db_port,
                database=db_config.db_name,
                user=db_config.db_user,
                password=db_config.db_password
            )
            connection.autocommit = False
        else:
            connection = sqlite3.connect(db_config.sqlite_path)
            connection.row_factory = sqlite3.Row
        
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
    Automatically handles both SQLite and PostgreSQL
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
    Execute a database query with automatic connection management
    
    Args:
        query: SQL query string
        params: Query parameters
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
                if db_config.is_postgresql():
                    # PostgreSQL returns tuples
                    columns = [desc[0] for desc in cursor.description]
                    results = cursor.fetchall()
                    return [dict(zip(columns, row)) for row in results]
                else:
                    # SQLite returns Row objects
                    return [dict(row) for row in cursor.fetchall()]
            else:
                conn.commit()
                return None
                
        except Exception as e:
            logger.error(f"Query execution error: {e}")
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
    Test database connection
    
    Returns:
        True if connection successful, False otherwise
    """
    try:
        with get_db_connection() as conn:
            if db_config.is_postgresql():
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                cursor.close()
            else:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                cursor.close()
        logger.info("Database connection test successful")
        return True
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False

def get_database_info() -> Dict[str, Any]:
    """
    Get information about the current database configuration
    
    Returns:
        Dictionary with database information
    """
    return {
        'type': db_config.db_type,
        'connection_string': db_config.get_connection_string() if not db_config.is_postgresql() else '***hidden***',
        'is_postgresql': db_config.is_postgresql(),
        'is_sqlite': db_config.is_sqlite(),
        'host': db_config.db_host if db_config.is_postgresql() else None,
        'port': db_config.db_port if db_config.is_postgresql() else None,
        'database': db_config.db_name if db_config.is_postgresql() else db_config.sqlite_path,
        'user': db_config.db_user if db_config.is_postgresql() else None
    }

# SQL compatibility helpers
def get_sql_dialect() -> str:
    """Get the SQL dialect for the current database"""
    return 'postgresql' if db_config.is_postgresql() else 'sqlite'

def adapt_sql_for_dialect(sql: str) -> str:
    """
    Adapt SQL queries for different database dialects
    
    Args:
        sql: SQL query string
    
    Returns:
        Adapted SQL query
    """
    if db_config.is_postgresql():
        # PostgreSQL specific adaptations
        sql = sql.replace('AUTOINCREMENT', 'SERIAL')
        sql = sql.replace('INTEGER PRIMARY KEY AUTOINCREMENT', 'SERIAL PRIMARY KEY')
        sql = sql.replace('TIMESTAMP DEFAULT CURRENT_TIMESTAMP', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
    else:
        # SQLite specific adaptations
        sql = sql.replace('SERIAL', 'INTEGER')
        sql = sql.replace('SERIAL PRIMARY KEY', 'INTEGER PRIMARY KEY AUTOINCREMENT')
    
    return sql

if __name__ == "__main__":
    # Test the database configuration
    print("Database Configuration:")
    print(f"Type: {db_config.db_type}")
    print(f"Connection String: {db_config.get_connection_string()}")
    print(f"Is PostgreSQL: {db_config.is_postgresql()}")
    print(f"Is SQLite: {db_config.is_sqlite()}")
    
    # Test connection
    if test_connection():
        print("✅ Database connection successful")
    else:
        print("❌ Database connection failed")
