#!/bin/bash

# NoSubvo Startup Script

echo "🚀 Starting NoSubvo - Subvocalization Reduction Tool"
echo ""

# Check and fix Tailwind CSS if needed
echo "🔧 Checking Tailwind CSS configuration..."
cd "$(dirname "$0")/frontend"
if ! npm list tailwindcss@^3.4.0 > /dev/null 2>&1; then
    echo "📦 Installing compatible Tailwind CSS version..."
    npm install -D "tailwindcss@^3.4.0" postcss autoprefixer
fi
cd ..

# Start backend
echo "📡 Starting Flask backend on port 5000..."
source venv/bin/activate
python backend.py &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Start frontend
echo "🎨 Starting React frontend on port 3000..."
cd frontend
npm start &
FRONTEND_PID=$!

echo ""
echo "✅ Both servers started!"
echo "   Backend PID: $BACKEND_PID"
echo "   Frontend PID: $FRONTEND_PID"
echo ""
echo "🌐 Open http://localhost:3000 in your browser"
echo ""
echo "Press Ctrl+C to stop both servers"

# Wait for Ctrl+C
trap "kill $BACKEND_PID $FRONTEND_PID" EXIT
wait


