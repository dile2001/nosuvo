# 🚀 Quick Start Guide - NoSubvo

Get up and running in 5 minutes!

## Step 1: Backend Setup (2 minutes)

```bash
# Navigate to project directory
cd /Users/dile/labs/nosuvo

# Activate virtual environment (already created)
source venv/bin/activate

# Install Flask dependencies (if not already done)
pip install flask-cors python-dotenv

# Start the backend
python backend.py
```

Backend will run on http://localhost:5000

## Step 2: Frontend Setup (3 minutes)

Open a NEW terminal:

```bash
# Navigate to frontend directory
cd /Users/dile/labs/nosuvo/frontend

# Install dependencies (if not already done)
npm install

# Start the frontend
npm start
```

Frontend will automatically open at http://localhost:3000

## 🎉 That's It!

Your subvocalization reduction app is now running!

### Quick Usage Tips:

1. **Paste text** or click "Load Sample Text"
2. **Choose a mode:**
   - RSVP Mode (⚡) - For speed training
   - Chunk Mode (🧩) - For comprehension
3. **Adjust speed** - Start at 250 WPM and increase gradually
4. **Practice daily** - 15-20 minutes for best results

## 🛠️ Alternative: Use the Startup Script

```bash
cd /Users/dile/labs/nosuvo
./start.sh
```

This will start both backend and frontend automatically!

## ❓ Troubleshooting

**Backend won't start?**
- Make sure you activated the virtual environment: `source venv/bin/activate`
- Check if port 5000 is available

**Frontend won't start?**
- Make sure you're in the frontend directory
- Try: `npm install` first
- Check if port 3000 is available

**Chunking not working?**
- Backend must be running on port 5000
- Check browser console for errors
- App will fall back to local chunking if backend is unavailable

## 📚 Learn More

See README.md for detailed documentation and customization options.

---

**Happy Reading! 📖⚡**


