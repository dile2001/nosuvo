# 📋 NoSubvo - Project Summary

## 🎯 Project Overview

**NoSubvo** is a web-based application designed to help users eliminate subvocalization and dramatically improve their reading speed through scientifically-backed techniques.

**Created:** October 5, 2025  
**Tech Stack:** React + TypeScript, Flask + Python, spaCy NLP  
**Target Users:** Anyone looking to read faster while maintaining comprehension

---

## 📁 Project Structure

```
/Users/dile/labs/nosuvo/
│
├── frontend/                      # React TypeScript application
│   ├── src/
│   │   ├── components/
│   │   │   ├── RSVPReader.tsx    # Rapid Serial Visual Presentation mode
│   │   │   ├── ChunkReader.tsx   # Phrase-based chunk reading mode
│   │   │   └── ProgressTracker.tsx # Progress tracking & statistics
│   │   ├── App.tsx               # Main application component
│   │   ├── App.css               # Application styles
│   │   └── index.css             # Global styles with Tailwind
│   ├── public/                   # Static assets
│   ├── package.json              # Frontend dependencies
│   ├── tailwind.config.js        # Tailwind CSS configuration
│   └── tsconfig.json             # TypeScript configuration
│
├── backend.py                    # Flask API server with spaCy NLP
├── useAi.py                      # OpenAI integration for advanced chunking
├── app.py                        # Original Flask app (legacy)
├── app1.py                       # Experimental chunking (legacy)
├── reading1.txt                  # Sample reading text
│
├── venv/                         # Python virtual environment
├── requirements.txt              # Python dependencies
├── test_backend.py              # Backend API test script
├── start.sh                     # Convenient startup script
│
├── README.md                    # Main documentation
├── QUICKSTART.md                # Quick start guide
├── FEATURES.md                  # Feature list & roadmap
├── PROJECT_SUMMARY.md           # This file
├── env_template.txt             # Environment variable template
└── .gitignore                   # Git ignore rules
```

---

## 🚀 Key Features

### 1. RSVP Mode (Rapid Serial Visual Presentation)
- Words flash one at a time at optimal focal point
- Adjustable speed: 100-1000 WPM
- Optimal Recognition Point (ORP) highlighting
- Forces eyes to stay still, prevents subvocalization

### 2. Chunk Reading Mode
- Text broken into meaningful phrase chunks
- Uses spaCy NLP for intelligent parsing
- Progressive highlighting
- Better for comprehension retention

### 3. Progress Tracking
- Session history with date/time
- Words per minute tracking
- Total words read statistics
- LocalStorage persistence

### 4. Smart Backend
- Flask REST API
- spaCy for NLP-powered chunking
- CORS-enabled for frontend integration
- Fallback chunking when backend unavailable

---

## 🛠️ Technologies Used

### Frontend
- **React 19.2** - UI framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **Axios** - HTTP client
- **LocalStorage** - Data persistence

### Backend
- **Flask 3.1** - Web framework
- **spaCy 3.7** - Natural Language Processing
- **Flask-CORS** - Cross-origin support
- **OpenAI API** - Optional advanced chunking

### Development Tools
- **npm/yarn** - Package management
- **Python venv** - Virtual environment
- **Git** - Version control

---

## 📊 Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Browser                           │
│  ┌─────────────────────────────────────────────┐   │
│  │         React Frontend (Port 3000)          │   │
│  │  ┌──────────┐  ┌───────────┐  ┌──────────┐ │   │
│  │  │   RSVP   │  │   Chunk   │  │ Progress │ │   │
│  │  │  Reader  │  │  Reader   │  │ Tracker  │ │   │
│  │  └────┬─────┘  └─────┬─────┘  └──────────┘ │   │
│  │       │              │                       │   │
│  │       └──────────────┴───────────────────────┤   │
│  │                  Axios HTTP                  │   │
│  └──────────────────────┬────────────────────────┘   │
└─────────────────────────┼────────────────────────────┘
                          │
                    HTTP/JSON
                          │
┌─────────────────────────▼────────────────────────────┐
│         Flask Backend API (Port 5000)                │
│  ┌──────────────────────────────────────────────┐   │
│  │         Endpoints                            │   │
│  │  • GET  /health                              │   │
│  │  • POST /chunk                               │   │
│  └────────────┬─────────────────────────────────┘   │
│               │                                      │
│  ┌────────────▼─────────────────────────────────┐   │
│  │         spaCy NLP Engine                     │   │
│  │  • Tokenization                              │   │
│  │  • POS Tagging                               │   │
│  │  • Dependency Parsing                        │   │
│  │  • Noun/Verb/Prep Phrase Extraction          │   │
│  └──────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────┘
```

---

## 🔌 API Endpoints

### GET `/`
Returns API information and available endpoints

### GET `/health`
Health check endpoint
```json
{
  "status": "healthy",
  "message": "Service is running"
}
```

### POST `/chunk`
Process text into reading chunks
```json
Request:
{
  "text": "Your text here..."
}

Response:
{
  "success": true,
  "chunks": ["chunk 1", "chunk 2", ...],
  "chunk_count": 15,
  "original_length": 200
}
```

---

## 🎓 How It Works

### Subvocalization Elimination

**The Problem:** Most people subvocalize (silently pronounce words) when reading, limiting reading speed to ~150-250 WPM (speaking speed).

**The Solution:** Two proven techniques:

1. **RSVP (Rapid Serial Visual Presentation)**
   - Words appear too fast for subvocalization
   - Eyes stay fixed on one point (no movement)
   - Brain learns to process visually, not auditorily

2. **Chunk Reading**
   - Groups words into meaningful phrases
   - Trains brain to process ideas, not individual words
   - Reduces eye fixations per line

### The Science

- **Optimal Recognition Point (ORP)**: Studies show readers recognize words fastest when focusing ~37% into the word
- **Phrase Chunking**: Natural language processing identifies grammatical phrases that the brain processes as units
- **Progressive Speed Training**: Gradually increasing speed forces the brain to adapt and eliminate inner speech

---

## 📈 Performance Expectations

### Typical Progress Trajectory

| Phase | Timeframe | WPM Range | Focus |
|-------|-----------|-----------|-------|
| Baseline | Day 1 | 200-250 | Assessment |
| Beginner | Week 1-2 | 250-350 | Technique learning |
| Intermediate | Week 3-6 | 350-500 | Subvocalization reduction |
| Advanced | Week 7-12 | 500-700+ | Speed & comprehension balance |

*Results vary by individual practice time and dedication*

---

## 🚦 Getting Started

### Quick Start (5 minutes)

1. **Backend:**
   ```bash
   cd /Users/dile/labs/nosuvo
   source venv/bin/activate
   python backend.py
   ```

2. **Frontend:**
   ```bash
   cd /Users/dile/labs/nosuvo/frontend
   npm start
   ```

3. **Open:** http://localhost:3000

### Using the Startup Script

```bash
cd /Users/dile/labs/nosuvo
./start.sh
```

---

## 🧪 Testing

### Backend Test
```bash
cd /Users/dile/labs/nosuvo
source venv/bin/activate
python test_backend.py
```

### Manual Testing
1. Start both servers
2. Load sample text
3. Try RSVP mode at 300 WPM
4. Try Chunk mode
5. Check progress tracker

---

## 🔒 Security Notes

- ✅ API key secured with environment variables
- ✅ CORS configured for specific origins
- ✅ `.env` files in `.gitignore`
- ✅ No sensitive data in localStorage

**Before deploying:**
- Set up proper environment variable management
- Configure CORS for production domains
- Add authentication for user accounts
- Use HTTPS in production

---

## 📝 Development Workflow

### Adding New Features

1. **Frontend Component:**
   - Create in `frontend/src/components/`
   - Import in `App.tsx`
   - Add routing if needed

2. **Backend Endpoint:**
   - Add route in `backend.py`
   - Update API documentation
   - Test with `test_backend.py`

3. **Styling:**
   - Use Tailwind utility classes
   - Follow existing color scheme
   - Ensure mobile responsiveness

### Code Style
- **TypeScript:** Interfaces for props, strict typing
- **Python:** PEP 8, type hints where helpful
- **React:** Functional components with hooks
- **CSS:** Tailwind utilities, minimal custom CSS

---

## 🐛 Known Issues & Limitations

1. **LocalStorage Limits:** Progress data stored locally (10MB limit)
   - *Future:* Move to database with user accounts

2. **Backend Dependency:** Chunk mode requires running backend
   - *Current:* Falls back to local chunking
   - *Future:* Client-side spaCy alternative

3. **No Mobile App:** Web-only currently
   - *Future:* Native iOS/Android apps

4. **Single User:** No multi-user support yet
   - *Future:* User authentication system

---

## 🎯 Success Metrics

### User Success
- Average reading speed increase of 100+ WPM
- Maintain 80%+ comprehension
- Daily practice consistency

### Technical Success
- < 100ms API response time
- 99% uptime
- Zero data loss
- Mobile-friendly UI

---

## 📚 Resources & References

### Speed Reading Research
- Rapid Serial Visual Presentation studies
- Eye-tracking research on reading patterns
- Cognitive load theory

### Technical Documentation
- [React Docs](https://react.dev)
- [Flask Documentation](https://flask.palletsprojects.com)
- [spaCy Documentation](https://spacy.io)
- [Tailwind CSS](https://tailwindcss.com)

---

## 🤝 Contributing

See `FEATURES.md` for planned features and roadmap.

**How to contribute:**
1. Fork the repository
2. Create feature branch
3. Make your changes
4. Test thoroughly
5. Submit pull request

---

## 📄 License

MIT License - Free to use for personal or commercial purposes.

---

## 👥 Contact & Support

**Issues:** Use GitHub Issues for bug reports
**Questions:** See README.md and QUICKSTART.md
**Feature Requests:** Add to FEATURES.md discussion

---

## 🎉 Acknowledgments

Built with research from:
- Speed reading methodology pioneers
- Natural language processing research
- Cognitive psychology studies
- Open source community

---

**Version:** 1.0  
**Last Updated:** October 5, 2025  
**Status:** Production Ready ✅

Happy speed reading! 📚⚡


