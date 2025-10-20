#!/bin/bash
# NoSubvo PostgreSQL Setup Script
# Simplified PostgreSQL-only setup

set -e

echo "🚀 NoSubvo PostgreSQL Setup"
echo "=========================="
echo ""

# Check if we're in the right directory
if [ ! -f "backend.py" ]; then
    echo "❌ Error: Please run this script from the NoSubvo project root directory"
    exit 1
fi

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo "❌ PostgreSQL is not installed."
    echo ""
    echo "Installation instructions:"
    echo "  macOS: brew install postgresql@17"
    echo "  Ubuntu: sudo apt-get install postgresql-17 postgresql-client-17"
    echo "  Windows: Download from https://www.postgresql.org/download/"
    exit 1
fi

# Check PostgreSQL version
echo "🔍 Checking PostgreSQL version..."
PG_VERSION=$(psql --version | grep -oE '[0-9]+\.[0-9]+' | head -1)
echo "✅ PostgreSQL version: $PG_VERSION"

# Check if database exists
echo ""
echo "🔍 Checking if database 'nosuvo_db' exists..."
if psql -lqt | cut -d \| -f 1 | grep -qw nosuvo_db; then
    echo "✅ Database 'nosuvo_db' already exists"
else
    echo "📝 Creating database 'nosuvo_db'..."
    createdb nosuvo_db
    echo "✅ Database created"
fi

# Check if .env.local exists
echo ""
if [ ! -f ".env.local" ]; then
    echo "📝 Creating .env.local from template..."
    if [ -f ".env.local.new" ]; then
        mv .env.local.new .env.local
        echo "✅ .env.local created"
    else
        cp env_template.txt .env.local
        echo "✅ .env.local created from template"
        echo "⚠️  Please edit .env.local with your PostgreSQL credentials"
    fi
else
    echo "✅ .env.local already exists"
fi

# Install Python dependencies
echo ""
echo "📦 Installing Python dependencies..."
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
fi

pip install -q -r requirements.txt
echo "✅ Python dependencies installed"

# Test database connection
echo ""
echo "🔍 Testing database connection..."
if python database.py > /dev/null 2>&1; then
    echo "✅ Database connection successful"
else
    echo "❌ Database connection failed"
    echo "Please check your .env.local settings:"
    echo "  - DB_HOST"
    echo "  - DB_PORT"
    echo "  - DB_NAME"
    echo "  - DB_USER"
    echo "  - DB_PASSWORD"
    exit 1
fi

# Initialize database schema
echo ""
echo "🔧 Initializing database schema..."
python -c "from database import init_database_schema; init_database_schema(); print('✅ Database schema initialized')"

# Insert sample exercises
echo ""
echo "📚 Inserting sample exercises..."
python -c "from backend import insert_sample_exercises; insert_sample_exercises(); print('✅ Sample exercises added')"

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Start backend: python backend.py"
echo "2. Start frontend: cd frontend && npm start"
echo "3. Open browser: http://localhost:3000"

