#!/bin/bash

# NoSubvo - Setup Verification Script

echo "🔍 NoSubvo Setup Verification"
echo "======================================"
echo ""

# Check Python
echo "Checking Python installation..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "✅ $PYTHON_VERSION"
else
    echo "❌ Python3 not found"
    exit 1
fi

# Check Node.js
echo "Checking Node.js installation..."
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo "✅ Node.js $NODE_VERSION"
else
    echo "❌ Node.js not found"
    exit 1
fi

# Check npm
echo "Checking npm installation..."
if command -v npm &> /dev/null; then
    NPM_VERSION=$(npm --version)
    echo "✅ npm $NPM_VERSION"
else
    echo "❌ npm not found"
    exit 1
fi

# Check virtual environment
echo "Checking Python virtual environment..."
if [ -d "venv" ]; then
    echo "✅ Virtual environment exists"
else
    echo "❌ Virtual environment not found"
    exit 1
fi

# Check Python packages
echo "Checking Python packages..."
source venv/bin/activate
if python -c "import flask" 2>/dev/null; then
    echo "✅ Flask installed"
else
    echo "⚠️  Flask not installed - run: pip install -r requirements.txt"
fi

if python -c "import flask_cors" 2>/dev/null; then
    echo "✅ Flask-CORS installed"
else
    echo "⚠️  Flask-CORS not installed"
fi

if python -c "import spacy" 2>/dev/null; then
    echo "✅ spaCy installed"
    
    # Check spaCy model
    if python -c "import spacy; spacy.load('en_core_web_sm')" 2>/dev/null; then
        echo "✅ spaCy English model installed"
    else
        echo "⚠️  spaCy English model not installed - run: python -m spacy download en_core_web_sm"
    fi
else
    echo "⚠️  spaCy not installed"
fi

# Check frontend
echo "Checking frontend setup..."
if [ -d "frontend" ]; then
    echo "✅ Frontend directory exists"
    
    if [ -f "frontend/package.json" ]; then
        echo "✅ package.json found"
    else
        echo "❌ package.json not found"
    fi
    
    if [ -d "frontend/node_modules" ]; then
        echo "✅ Node modules installed"
    else
        echo "⚠️  Node modules not installed - run: cd frontend && npm install"
    fi
else
    echo "❌ Frontend directory not found"
fi

# Check key files
echo "Checking project files..."
FILES=("backend.py" "requirements.txt" "README.md" "QUICKSTART.md")
for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file missing"
    fi
done

echo ""
echo "======================================"
echo "Setup Verification Complete!"
echo ""
echo "Next steps:"
echo "1. If any ⚠️ warnings above, install missing dependencies"
echo "2. Run ./start.sh to start both servers"
echo "3. Open http://localhost:3000 in your browser"
echo ""
echo "Happy Reading! 📚⚡"


