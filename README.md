# NoSubvo - Subvocalization Reduction Tool

A modern web application designed to help users eliminate subvocalization and dramatically improve their reading speed through proven techniques.

## 🎯 What is Subvocalization?

Subvocalization is the habit of silently pronouncing words in your head while reading. While it helped you learn to read, it now limits your reading speed to about 150-250 words per minute (your speaking speed). By reducing subvocalization, you can potentially read at 400-700+ WPM while maintaining comprehension.

## ✨ Features

### 1. **RSVP Mode (Rapid Serial Visual Presentation)**
- Words flash one at a time at your optimal focal point
- Adjustable speed from 100-1000 WPM
- Optimal Recognition Point (ORP) highlighting
- Forces eyes to stay still and prevents subvocalization

### 2. **Chunk Reading Mode**
- Text broken into meaningful phrase-level chunks
- Progressive highlighting of noun phrases, verb phrases, and prepositional phrases
- Trains brain to process ideas in groups
- Better comprehension retention

### 3. **Progress Tracking**
- Track reading sessions, speed improvements, and total words read
- Visual statistics dashboard
- Historical session data

### 4. **Smart Text Processing**
- Backend powered by spaCy NLP for intelligent phrase chunking
- Optional OpenAI integration for advanced chunking

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Node.js 14+
- npm or yarn

### Backend Setup

1. **Install Python dependencies:**
```bash
cd /Users/dile/labs/nosuvo
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

2. **Run the backend server:**
```bash
python backend.py
```

The API will be available at `http://localhost:5000`

### Frontend Setup

1. **Install Node dependencies:**
```bash
cd frontend
npm install
```

2. **Start the development server:**
```bash
npm start
```

The app will open at `http://localhost:3000`

## 📖 How to Use

1. **Enter Your Text**: Paste any text you want to read, or use the sample text provided
2. **Choose a Mode**:
   - **RSVP Mode**: Best for speed training and eliminating subvocalization
   - **Chunk Mode**: Best for comprehension and learning to read in phrases
3. **Adjust Speed**: Start slow and gradually increase as you get comfortable
4. **Track Progress**: Monitor your improvement over time

## 💡 Tips for Success

1. **Start Slow**: Begin at a comfortable speed and gradually increase
2. **Use a Pacer**: In RSVP mode, focus on the highlighted letter (ORP)
3. **Occupy Your Inner Voice**: Try counting "1-2-3-4" or humming while reading
4. **Practice Daily**: 15-20 minutes daily for best results
5. **Don't Sacrifice Comprehension**: Speed is useless without understanding

## 🛠️ Tech Stack

**Frontend:**
- React with TypeScript
- Tailwind CSS for styling
- Axios for API calls
- Local storage for progress tracking

**Backend:**
- Flask (Python web framework)
- spaCy (NLP for text chunking)
- Flask-CORS (Cross-origin support)
- Optional: OpenAI API for advanced chunking

## 📁 Project Structure

```
nosuvo/
├── frontend/                # React TypeScript app
│   ├── src/
│   │   ├── components/
│   │   │   ├── RSVPReader.tsx
│   │   │   ├── ChunkReader.tsx
│   │   │   └── ProgressTracker.tsx
│   │   ├── App.tsx
│   │   └── index.tsx
│   └── package.json
├── backend.py              # Flask API server
├── requirements.txt        # Python dependencies
├── reading1.txt           # Sample reading text
└── README.md
```

## 🔧 API Endpoints

- `GET /` - API info
- `GET /health` - Health check
- `POST /chunk` - Process text into chunks
  ```json
  {
    "text": "Your text here..."
  }
  ```

## 🎨 Customization

### Adjust Reading Speeds
- Modify WPM ranges in `RSVPReader.tsx`
- Adjust chunk timing in `ChunkReader.tsx`

### Chunking Algorithm
- Edit chunking logic in `backend.py`
- Integrate with OpenAI using `useAi.py` as reference

## 🤝 Contributing

Feel free to submit issues and enhancement requests!

## 📝 License

MIT License - feel free to use this project for personal or commercial purposes.

## 🙏 Acknowledgments

Based on research in speed reading and cognitive psychology:
- RSVP technique pioneered by reading comprehension studies
- Chunking methodology from NLP and linguistics research
- Subvocalization reduction techniques from speed reading programs

---

**Happy Reading! 📚⚡**

Built with ❤️ to help you read faster and smarter.


