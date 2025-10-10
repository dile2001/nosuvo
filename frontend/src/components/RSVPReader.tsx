import React, { useState, useEffect, useRef } from 'react';
import QuestionReader from './QuestionReader';

interface RSVPReaderProps {
  text: string;
  onBack: () => void;
  onStartQuestions?: (text: string) => void;
}

const RSVPReader: React.FC<RSVPReaderProps> = ({ text, onBack, onStartQuestions }) => {
  const [words, setWords] = useState<string[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [wpm, setWpm] = useState(300);
  const [showControls, setShowControls] = useState(true);
  const [showCompletionMessage, setShowCompletionMessage] = useState(false);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    // Split text into words
    const wordArray = text.split(/\s+/).filter(word => word.length > 0);
    setWords(wordArray);
  }, [text]);

  useEffect(() => {
    if (isPlaying && currentIndex < words.length) {
      const delay = 60000 / wpm; // Convert WPM to milliseconds
      intervalRef.current = setInterval(() => {
        setCurrentIndex(prev => {
          if (prev >= words.length - 1) {
            setIsPlaying(false);
            setShowCompletionMessage(true);
            return prev;
          }
          return prev + 1;
        });
      }, delay);
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [isPlaying, wpm, words.length, currentIndex]);

  const togglePlay = () => {
    if (currentIndex >= words.length - 1) {
      setCurrentIndex(0);
    }
    setIsPlaying(!isPlaying);
  };

  const handleReset = () => {
    setIsPlaying(false);
    setCurrentIndex(0);
    setShowCompletionMessage(false);
  };

  const handleStartQuestions = () => {
    if (onStartQuestions) {
      onStartQuestions(text);
    }
  };

  const handleSpeedChange = (newWpm: number) => {
    setWpm(newWpm);
  };

  const currentWord = words[currentIndex] || '';
  const progress = words.length > 0 ? (currentIndex / words.length) * 100 : 0;

  // Show completion message and question prompt
  if (showCompletionMessage) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-indigo-900 to-purple-900 flex items-center justify-center">
        <div className="max-w-2xl mx-auto p-8 text-center">
          <div className="bg-white rounded-2xl p-12 shadow-2xl">
            <div className="text-6xl mb-6">🎉</div>
            <h2 className="text-3xl font-bold text-gray-800 mb-4">
              Reading Complete!
            </h2>
            <p className="text-xl text-gray-600 mb-8">
              Great job! You've finished reading the text using RSVP mode.
            </p>
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-8">
              <h3 className="text-xl font-bold text-blue-800 mb-2">
                Now answer these questions to check your understanding
              </h3>
              <p className="text-blue-700">
                The questions will be displayed using the same RSVP technique to maintain your reading flow.
              </p>
            </div>
            <div className="flex gap-4 justify-center">
              <button
                onClick={handleStartQuestions}
                className="px-8 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition font-semibold text-lg"
              >
                Start Questions →
              </button>
              <button
                onClick={handleReset}
                className="px-8 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition font-semibold text-lg"
              >
                Read Again
              </button>
              <button
                onClick={onBack}
                className="px-8 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition font-semibold text-lg"
              >
                ← Back to Home
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Find the optimal recognition point (ORP) - usually 1/3 into the word
  const getORPIndex = (word: string) => {
    if (word.length <= 1) return 0;
    return Math.floor(word.length * 0.37); // Optimal Recognition Point
  };

  const orpIndex = getORPIndex(currentWord);

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-900 to-purple-900 flex flex-col">
      {/* Header */}
      <div className="bg-black bg-opacity-30 p-4">
        <div className="container mx-auto flex justify-between items-center">
          <button
            onClick={onBack}
            className="px-4 py-2 bg-white bg-opacity-20 text-white rounded-lg hover:bg-opacity-30 transition"
          >
            ← Back
          </button>
          <h2 className="text-2xl font-bold text-white">RSVP Mode</h2>
          <button
            onClick={() => setShowControls(!showControls)}
            className="px-4 py-2 bg-white bg-opacity-20 text-white rounded-lg hover:bg-opacity-30 transition"
          >
            {showControls ? 'Hide' : 'Show'} Controls
          </button>
        </div>
      </div>

      {/* Main Reading Area */}
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          {/* Word Display with ORP */}
          <div className="bg-white bg-opacity-10 backdrop-blur-lg rounded-2xl p-12 mb-8 min-w-[400px]">
            <div className="text-7xl font-bold text-white tracking-wider">
              {currentWord.split('').map((char, idx) => (
                <span
                  key={idx}
                  className={idx === orpIndex ? 'text-yellow-400' : ''}
                >
                  {char}
                </span>
              ))}
            </div>
            {/* Focus Line */}
            <div className="mt-8 h-1 bg-yellow-400 opacity-50"></div>
          </div>

          {/* Progress Bar */}
          <div className="mb-8">
            <div className="w-full bg-white bg-opacity-20 rounded-full h-2">
              <div
                className="bg-yellow-400 h-2 rounded-full transition-all duration-100"
                style={{ width: `${progress}%` }}
              ></div>
            </div>
            <p className="text-white mt-2">
              {currentIndex + 1} / {words.length} words
            </p>
          </div>
        </div>
      </div>

      {/* Controls */}
      {showControls && (
        <div className="bg-black bg-opacity-30 p-6">
          <div className="container mx-auto max-w-4xl">
            {/* Play/Pause & Reset */}
            <div className="flex justify-center gap-4 mb-6">
              <button
                onClick={handleReset}
                className="px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 transition font-semibold"
              >
                ⟲ Reset
              </button>
              <button
                onClick={togglePlay}
                className="px-8 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition font-semibold text-xl"
              >
                {isPlaying ? '⏸ Pause' : '▶ Play'}
              </button>
            </div>

            {/* Speed Control */}
            <div className="bg-white bg-opacity-10 backdrop-blur-lg rounded-xl p-6">
              <div className="flex items-center justify-between mb-4">
                <label className="text-white font-semibold text-lg">
                  Reading Speed: {wpm} WPM
                </label>
                <div className="flex gap-2">
                  <button
                    onClick={() => handleSpeedChange(Math.max(100, wpm - 50))}
                    className="px-3 py-1 bg-white bg-opacity-20 text-white rounded hover:bg-opacity-30 transition"
                  >
                    -50
                  </button>
                  <button
                    onClick={() => handleSpeedChange(wpm + 50)}
                    className="px-3 py-1 bg-white bg-opacity-20 text-white rounded hover:bg-opacity-30 transition"
                  >
                    +50
                  </button>
                </div>
              </div>
              <input
                type="range"
                min="100"
                max="1000"
                step="50"
                value={wpm}
                onChange={(e) => handleSpeedChange(parseInt(e.target.value))}
                className="w-full h-2 bg-white bg-opacity-30 rounded-lg appearance-none cursor-pointer"
              />
              <div className="flex justify-between text-white text-sm mt-2">
                <span>100 WPM (Slow)</span>
                <span>300 WPM (Average)</span>
                <span>500 WPM (Fast)</span>
                <span>1000 WPM (Very Fast)</span>
              </div>
            </div>

            {/* Tips */}
            <div className="mt-6 bg-yellow-400 bg-opacity-20 border border-yellow-400 rounded-lg p-4">
              <p className="text-yellow-100 text-sm">
                <strong>💡 Tip:</strong> The highlighted letter (in yellow) is the Optimal Recognition Point. 
                Focus your eyes there and let the words flow through your peripheral vision. 
                Start slow and gradually increase speed.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default RSVPReader;


