#!/usr/bin/env python3
"""
NoSubvo Database Migration Script
Migrates data from SQLite to PostgreSQL
"""

import os
import sys
import sqlite3
import psycopg2
from datetime import datetime
import logging
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class DatabaseMigrator:
    """Handles migration from SQLite to PostgreSQL"""
    
    def __init__(self):
        self.sqlite_path = 'exercises.db'
        self.backup_path = f'exercises_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
        
        # PostgreSQL connection details
        self.pg_host = os.getenv('DB_HOST', 'localhost')
        self.pg_port = int(os.getenv('DB_PORT', 5432))
        self.pg_name = os.getenv('DB_NAME', 'nosuvo_db')
        self.pg_user = os.getenv('DB_USER', 'postgres')
        self.pg_password = os.getenv('DB_PASSWORD', '')
        
    def create_backup(self):
        """Create a backup of the SQLite database"""
        try:
            import shutil
            shutil.copy2(self.sqlite_path, self.backup_path)
            logger.info(f"✅ Backup created: {self.backup_path}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to create backup: {e}")
            return False
    
    def test_postgresql_connection(self):
        """Test PostgreSQL connection"""
        try:
            conn = psycopg2.connect(
                host=self.pg_host,
                port=self.pg_port,
                database=self.pg_name,
                user=self.pg_user,
                password=self.pg_password
            )
            conn.close()
            logger.info("✅ PostgreSQL connection successful")
            return True
        except Exception as e:
            logger.error(f"❌ PostgreSQL connection failed: {e}")
            return False
    
    def create_postgresql_schema(self):
        """Create PostgreSQL schema"""
        try:
            conn = psycopg2.connect(
                host=self.pg_host,
                port=self.pg_port,
                database=self.pg_name,
                user=self.pg_user,
                password=self.pg_password
            )
            cursor = conn.cursor()
            
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
            
            # Create indexes
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_language ON exercises(language)",
                "CREATE INDEX IF NOT EXISTS idx_difficulty ON exercises(difficulty)",
                "CREATE INDEX IF NOT EXISTS idx_topic ON exercises(topic)",
                "CREATE INDEX IF NOT EXISTS idx_user_progress_user_id ON user_progress(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_user_progress_status ON user_progress(status)",
                "CREATE INDEX IF NOT EXISTS idx_user_queue_user_id ON user_queue(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_user_queue_position ON user_queue(queue_position)"
            ]
            
            for index_sql in indexes:
                cursor.execute(index_sql)
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info("✅ PostgreSQL schema created successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create PostgreSQL schema: {e}")
            return False
    
    def migrate_data(self):
        """Migrate data from SQLite to PostgreSQL"""
        try:
            # Connect to SQLite
            sqlite_conn = sqlite3.connect(self.sqlite_path)
            sqlite_conn.row_factory = sqlite3.Row
            sqlite_cursor = sqlite_conn.cursor()
            
            # Connect to PostgreSQL
            pg_conn = psycopg2.connect(
                host=self.pg_host,
                port=self.pg_port,
                database=self.pg_name,
                user=self.pg_user,
                password=self.pg_password
            )
            pg_cursor = pg_conn.cursor()
            
            # Get all table names from SQLite
            sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in sqlite_cursor.fetchall()]
            
            logger.info(f"📋 Found tables: {tables}")
            
            # Migrate each table
            for table in tables:
                if table == 'sqlite_sequence':
                    continue
                    
                logger.info(f"🔄 Migrating table: {table}")
                
                # Get all data from SQLite table
                sqlite_cursor.execute(f"SELECT * FROM {table}")
                rows = sqlite_cursor.fetchall()
                
                if not rows:
                    logger.info(f"⚠️  Table {table} is empty, skipping")
                    continue
                
                # Get column names
                columns = [description[0] for description in sqlite_cursor.description]
                
                # Create INSERT statement for PostgreSQL
                placeholders = ', '.join(['%s'] * len(columns))
                insert_sql = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders}) ON CONFLICT DO NOTHING"
                
                # Convert rows to tuples and insert
                for row in rows:
                    pg_cursor.execute(insert_sql, tuple(row))
                
                logger.info(f"✅ Migrated {len(rows)} rows from {table}")
            
            pg_conn.commit()
            sqlite_cursor.close()
            sqlite_conn.close()
            pg_cursor.close()
            pg_conn.close()
            
            logger.info("✅ Data migration completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to migrate data: {e}")
            return False
    
    def verify_migration(self):
        """Verify that the migration was successful"""
        try:
            pg_conn = psycopg2.connect(
                host=self.pg_host,
                port=self.pg_port,
                database=self.pg_name,
                user=self.pg_user,
                password=self.pg_password
            )
            cursor = pg_conn.cursor()
            
            # Check table counts
            tables = ['exercises', 'users', 'user_progress', 'user_queue']
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                logger.info(f"📊 Table {table}: {count} records")
            
            cursor.close()
            pg_conn.close()
            
            logger.info("✅ Migration verification completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to verify migration: {e}")
            return False
    
    def run_migration(self):
        """Run the complete migration process"""
        logger.info("🚀 Starting NoSubvo database migration...")
        logger.info(f"📁 Source: SQLite ({self.sqlite_path})")
        logger.info(f"🎯 Target: PostgreSQL ({self.pg_host}:{self.pg_port}/{self.pg_name})")
        
        # Step 1: Create backup
        if not self.create_backup():
            logger.error("❌ Failed to create backup. Aborting migration.")
            return False
        
        # Step 2: Test PostgreSQL connection
        if not self.test_postgresql_connection():
            logger.error("❌ PostgreSQL connection failed. Aborting migration.")
            return False
        
        # Step 3: Create PostgreSQL schema
        if not self.create_postgresql_schema():
            logger.error("❌ Failed to create PostgreSQL schema. Aborting migration.")
            return False
        
        # Step 4: Migrate data
        if not self.migrate_data():
            logger.error("❌ Failed to migrate data. Aborting migration.")
            return False
        
        # Step 5: Verify migration
        if not self.verify_migration():
            logger.error("❌ Migration verification failed.")
            return False
        
        logger.info("🎉 Database migration completed successfully!")
        logger.info(f"📁 Backup created at: {self.backup_path}")
        logger.info("🔄 Next steps:")
        logger.info("   1. Update your .env file to use PostgreSQL")
        logger.info("   2. Set DB_TYPE=postgresql in your .env")
        logger.info("   3. Restart your application")
        
        return True

def main():
    """Main migration function"""
    print("NoSubvo Database Migration Tool")
    print("=" * 50)
    
    # Check if SQLite database exists
    if not os.path.exists('exercises.db'):
        print("❌ SQLite database not found: exercises.db")
        print("   Make sure you're running this from the project root directory.")
        return False
    
    # Check environment variables
    required_vars = ['DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASSWORD']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("   Please set these in your .env file before running the migration.")
        return False
    
    # Confirm migration
    print("\n⚠️  This will migrate your data from SQLite to PostgreSQL.")
    print("   A backup will be created automatically.")
    response = input("\nDo you want to proceed? (y/N): ")
    
    if response.lower() != 'y':
        print("Migration cancelled.")
        return False
    
    # Run migration
    migrator = DatabaseMigrator()
    success = migrator.run_migration()
    
    if success:
        print("\n🎉 Migration completed successfully!")
        print(f"📁 Backup created: {migrator.backup_path}")
        print("\n🔄 Next steps:")
        print("   1. Update your .env file:")
        print("      DB_TYPE=postgresql")
        print("   2. Restart your application")
        print("   3. Test all functionality")
    else:
        print("\n❌ Migration failed. Check the logs above for details.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
