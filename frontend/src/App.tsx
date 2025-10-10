import React, { useState } from 'react';
import axios from 'axios';
import './App.css';
import RSVPReader from './components/RSVPReader';
import ChunkReader from './components/ChunkReader';
import QuestionReader from './components/QuestionReader';
import ProgressTracker from './components/ProgressTracker';
import AuthModal from './components/AuthModal';
import UserProgress from './components/UserProgress';
import { AuthProvider, useAuth } from './contexts/AuthContext';

type ReadingMode = 'home' | 'rsvp' | 'chunk' | 'questions';

interface ExerciseData {
  question: string;
  options: {
    A: string;
    B: string;
    C: string;
    D: string;
  };
  answer: string;
}

interface ExerciseResponse {
  id: number;
  text: string;
  questions: ExerciseData[];
}

const AppContent: React.FC = () => {
  const { user, sessionToken, logout } = useAuth();
  const [mode, setMode] = useState<ReadingMode>('home');
  const [text, setText] = useState('');
  const [currentReadingMode, setCurrentReadingMode] = useState<'rsvp' | 'chunk'>('rsvp');
  const [exercises, setExercises] = useState<ExerciseData[]>([]);
  const [loading, setLoading] = useState(false);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [currentExerciseId, setCurrentExerciseId] = useState<number | null>(null);

  const sampleText = `Open your eyes in sea water and it is difficult to see much more than a murky, bleary green colour. Sounds, too, are garbled and difficult to comprehend. Without specialised equipment humans would be lost in these deep sea habitats, so how do fish make it seem so easy? Much of this is due to a biological phenomenon known as electroreception – the ability to perceive and act upon electrical stimuli as part of the overall senses. This ability is only found in aquatic or amphibious species because water is an efficient conductor of electricity.`;

  const loadExercise = async () => {
    setLoading(true);
    try {
      if (user && sessionToken) {
        // Use user-specific exercise endpoint
        const response = await fetch('/exercises/user', {
          headers: {
            'Authorization': `Bearer ${sessionToken}`
          }
        });
        
        if (response.ok) {
          const data = await response.json();
          if (data.success) {
            const exerciseData = data.exercise;
            setExercises(exerciseData.questions.questions || exerciseData.questions);
            setText(exerciseData.text);
            setCurrentExerciseId(exerciseData.id);
            return;
          }
        }
      }
      
      // Fallback to random exercise for non-authenticated users
      const response = await axios.get('/exercises');
      if (response.data.success) {
        const exerciseData: ExerciseResponse = response.data.exercise;
        setExercises(exerciseData.questions);
        setText(exerciseData.text);
        setCurrentExerciseId(exerciseData.id);
      }
    } catch (error) {
      console.error('Error loading exercises:', error);
      // Fallback to sample text if API fails
      setText(sampleText);
    } finally {
      setLoading(false);
    }
  };

  const handleStartReading = (selectedMode: ReadingMode) => {
    if (!text.trim()) {
      setText(sampleText);
    }
    setCurrentReadingMode(selectedMode as 'rsvp' | 'chunk');
    setMode(selectedMode);
  };

  const handleBack = () => {
    setMode('home');
  };

  const handleStartQuestions = (questionText: string) => {
    setText(questionText);
    setMode('questions');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {mode === 'home' ? (
        <div className="container mx-auto px-4 py-8 max-w-6xl">
          {/* Header */}
          <header className="text-center mb-12">
            <div className="flex justify-between items-center mb-4">
              <div></div>
              <h1 className="text-5xl font-bold text-indigo-900">
                NoSubvo
              </h1>
              <div className="flex gap-2">
                {user ? (
                  <>
                    <span className="text-sm text-gray-600">Welcome, {user.username}!</span>
                    <button
                      onClick={logout}
                      className="px-3 py-1 bg-gray-500 text-white text-sm rounded hover:bg-gray-600"
                    >
                      Logout
                    </button>
                  </>
                ) : (
                  <button
                    onClick={() => setShowAuthModal(true)}
                    className="px-4 py-2 bg-indigo-600 text-white text-sm rounded-lg hover:bg-indigo-700"
                  >
                    Login / Sign Up
                  </button>
                )}
              </div>
            </div>
            <p className="text-xl text-gray-700 mb-2">
              Eliminate Subvocalization, Read Faster
            </p>
            <p className="text-gray-600">
              {user 
                ? "Continue your personalized reading journey with intelligent text queues"
                : "Train your brain to read without inner speech and boost your reading speed by up to 3x"
              }
            </p>
          </header>

          {/* What is Subvocalization */}
          <div className="bg-white rounded-xl shadow-lg p-8 mb-8">
            <h2 className="text-2xl font-bold text-gray-800 mb-4">
              What is Subvocalization?
            </h2>
            <p className="text-gray-700 mb-4">
              Subvocalization is the habit of silently pronouncing each word in your head as you read. 
              While it helped you learn to read as a child, it now limits your reading speed to your 
              speaking speed (around 150-250 words per minute).
            </p>
            <p className="text-gray-700">
              By reducing subvocalization, you can train your brain to process text visually, 
              potentially increasing your reading speed to 400-700+ words per minute while maintaining comprehension.
            </p>
          </div>

          {/* Exercise Text Display */}
          <div className="bg-white rounded-xl shadow-lg p-8 mb-8">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-2xl font-bold text-gray-800">
                Reading Exercise
              </h2>
              <button
                onClick={() => loadExercise()}
                disabled={loading}
                className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition disabled:bg-gray-400 disabled:cursor-not-allowed"
              >
                {loading ? 'Loading...' : 'Load New Exercise'}
              </button>
            </div>
            
            {text ? (
              <div className="bg-gray-50 rounded-lg p-6 mb-4">
                <p className="text-gray-800 leading-relaxed whitespace-pre-wrap">
                  {text}
                </p>
              </div>
            ) : (
              <div className="bg-gray-50 rounded-lg p-6 mb-4 text-center">
                <p className="text-gray-500">
                  Click "Load New Exercise" to get a reading passage with comprehension questions
                </p>
              </div>
            )}
            
            {exercises.length > 0 && (
              <div className="mt-4 p-4 bg-blue-50 rounded-lg">
                <h3 className="font-semibold text-blue-800 mb-2">
                  📝 Comprehension Questions ({exercises.length})
                </h3>
                <p className="text-blue-700 text-sm">
                  Questions will be available after you complete the reading exercise
                </p>
              </div>
            )}
          </div>

          {/* Reading Modes */}
          <div className="grid md:grid-cols-2 gap-6 mb-8">
            {/* RSVP Mode */}
            <div className="bg-white rounded-xl shadow-lg p-8 hover:shadow-xl transition">
              <div className="flex items-center mb-4">
                <div className="w-12 h-12 bg-indigo-100 rounded-full flex items-center justify-center mr-4">
                  <span className="text-2xl">⚡</span>
                </div>
                <h3 className="text-2xl font-bold text-gray-800">RSVP Mode</h3>
              </div>
              <p className="text-gray-700 mb-6">
                <strong>Rapid Serial Visual Presentation</strong> - Words flash one at a time 
                at your optimal focal point. This forces your eyes to stay still and prevents 
                subvocalization by moving faster than your inner voice.
              </p>
              <ul className="text-gray-600 mb-6 space-y-2">
                <li>✓ Adjustable speed (WPM)</li>
                <li>✓ Focus point optimization</li>
                <li>✓ Best for speed training</li>
              </ul>
              <button
                onClick={() => handleStartReading('rsvp')}
                disabled={!text.trim()}
                className="w-full px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition disabled:bg-gray-400 disabled:cursor-not-allowed"
              >
                Start RSVP Reading
              </button>
            </div>

            {/* Chunk Mode */}
            <div className="bg-white rounded-xl shadow-lg p-8 hover:shadow-xl transition">
              <div className="flex items-center mb-4">
                <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center mr-4">
                  <span className="text-2xl">🧩</span>
                </div>
                <h3 className="text-2xl font-bold text-gray-800">Chunk Mode</h3>
              </div>
              <p className="text-gray-700 mb-6">
                <strong>Phrase-based Reading</strong> - Text is broken into meaningful chunks 
                (noun phrases, verb phrases) that highlight progressively. Train your brain to 
                process ideas in groups rather than word-by-word.
              </p>
              <ul className="text-gray-600 mb-6 space-y-2">
                <li>✓ Natural phrase grouping</li>
                <li>✓ Better comprehension</li>
                <li>✓ Progressive highlighting</li>
              </ul>
              <button
                onClick={() => handleStartReading('chunk')}
                disabled={!text.trim()}
                className="w-full px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition disabled:bg-gray-400 disabled:cursor-not-allowed"
              >
                Start Chunk Reading
              </button>
            </div>
          </div>

          {/* Progress Tracker */}
          {user ? <UserProgress /> : <ProgressTracker />}

          {/* Tips Section */}
          <div className="bg-white rounded-xl shadow-lg p-8">
            <h2 className="text-2xl font-bold text-gray-800 mb-4">
              Tips for Reducing Subvocalization
            </h2>
            <div className="grid md:grid-cols-2 gap-6">
              <div>
                <h4 className="font-bold text-gray-800 mb-2">1. Use a Pacer</h4>
                <p className="text-gray-700">
                  Move your finger or cursor faster than you can subvocalize to force your eyes to keep up.
                </p>
              </div>
              <div>
                <h4 className="font-bold text-gray-800 mb-2">2. Increase Speed Gradually</h4>
                <p className="text-gray-700">
                  Push beyond comfort but not so fast that comprehension drops completely.
                </p>
              </div>
              <div>
                <h4 className="font-bold text-gray-800 mb-2">3. Occupy Your Inner Voice</h4>
                <p className="text-gray-700">
                  Count "1-2-3-4" or hum quietly while reading to prevent inner speech.
                </p>
              </div>
              <div>
                <h4 className="font-bold text-gray-800 mb-2">4. Practice Daily</h4>
                <p className="text-gray-700">
                  Spend 15-20 minutes daily with these exercises for best results.
                </p>
              </div>
            </div>
          </div>
        </div>
      ) : mode === 'rsvp' ? (
        <RSVPReader text={text} onBack={handleBack} onStartQuestions={handleStartQuestions} />
      ) : mode === 'chunk' ? (
        <ChunkReader text={text} onBack={handleBack} onStartQuestions={handleStartQuestions} />
      ) : mode === 'questions' ? (
        <QuestionReader text={text} onBack={handleBack} readingMode={currentReadingMode} exercises={exercises} exerciseId={currentExerciseId || undefined} />
      ) : null}
      
      {/* Auth Modal */}
      <AuthModal isOpen={showAuthModal} onClose={() => setShowAuthModal(false)} />
    </div>
  );
};

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;
