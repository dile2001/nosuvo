#!/bin/bash
# NoSubvo PostgreSQL Migration Setup Script

echo "🚀 NoSubvo PostgreSQL Migration Setup"
echo "====================================="

# Check if we're in the right directory
if [ ! -f "backend.py" ]; then
    echo "❌ Error: Please run this script from the NoSubvo project root directory"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    cp env_template.txt .env
    echo "✅ .env file created. Please edit it with your PostgreSQL credentials."
    echo ""
    echo "Required PostgreSQL settings:"
    echo "  DB_TYPE=postgresql"
    echo "  DB_HOST=localhost"
    echo "  DB_PORT=5432"
    echo "  DB_NAME=nosuvo_db"
    echo "  DB_USER=your_username"
    echo "  DB_PASSWORD=your_password"
    echo ""
    echo "Please edit .env file and run this script again."
    exit 0
fi

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo "❌ PostgreSQL is not installed. Please install PostgreSQL first."
    echo ""
    echo "Installation instructions:"
    echo "  macOS: brew install postgresql@17"
    echo "  Ubuntu: sudo apt-get install postgresql-17 postgresql-client-17 postgresql-contrib-17"
    echo "  Windows: Download from https://www.postgresql.org/download/"
    echo ""
    echo "Version Requirements:"
    echo "  Minimum: PostgreSQL 9.6+"
    echo "  Recommended: PostgreSQL 17.x"
    echo "  Latest: PostgreSQL 18.x"
    exit 1
fi

# Check PostgreSQL version
echo "🔍 Checking PostgreSQL version..."
POSTGRES_VERSION=$(psql --version | grep -oE '[0-9]+\.[0-9]+' | head -1)
echo "📊 PostgreSQL version: $POSTGRES_VERSION"

# Check if version meets minimum requirements
REQUIRED_VERSION="9.6"
if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$POSTGRES_VERSION" | sort -V | head -n1)" = "$REQUIRED_VERSION" ]; then
    echo "✅ PostgreSQL version meets requirements"
else
    echo "❌ PostgreSQL version $POSTGRES_VERSION is too old. Minimum required: $REQUIRED_VERSION"
    exit 1
fi

# Check if Python dependencies are installed
echo "📦 Installing Python dependencies..."
source venv/bin/activate
pip install psycopg2-binary sqlalchemy alembic

# Test PostgreSQL connection
echo "🔍 Testing PostgreSQL connection..."
python3 -c "
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

try:
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', 5432)),
        database=os.getenv('DB_NAME', 'nosuvo_db'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', '')
    )
    conn.close()
    print('✅ PostgreSQL connection successful')
except Exception as e:
    print(f'❌ PostgreSQL connection failed: {e}')
    print('Please check your .env file settings')
    exit(1)
"

if [ $? -ne 0 ]; then
    exit 1
fi

# Run the migration
echo "🔄 Starting database migration..."
python3 migrate_to_postgresql.py

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Migration completed successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Update your .env file to set DB_TYPE=postgresql"
    echo "2. Restart your backend: python backend.py"
    echo "3. Test the application"
else
    echo "❌ Migration failed. Please check the error messages above."
fi
