import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import QuestionReader from './QuestionReader';

interface ChunkReaderProps {
  text: string;
  onBack: () => void;
  onStartQuestions?: (text: string) => void;
}

const ChunkReader: React.FC<ChunkReaderProps> = ({ text, onBack, onStartQuestions }) => {
  const [chunks, setChunks] = useState<string[]>([]);
  const [currentChunkIndex, setCurrentChunkIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [chunkDelay, setChunkDelay] = useState(800); // milliseconds per chunk
  const [loading, setLoading] = useState(true);
  const [useAI, setUseAI] = useState(false);
  const [showCompletionMessage, setShowCompletionMessage] = useState(false);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    fetchChunks();
  }, [text, useAI]);

  const fetchChunks = async () => {
    setLoading(true);
    try {
      if (useAI) {
        // For now, use simple chunking. You can integrate your OpenAI service here
        const simpleChunks = text.split(/[.!?]+/).filter(s => s.trim().length > 0);
        setChunks(simpleChunks);
      } else {
        // Use backend chunking service
        try {
          const response = await axios.post('http://localhost:5000/chunk', {
            text: text
          });
          setChunks(response.data.chunks);
        } catch (error) {
          console.error('Backend not available, using fallback chunking');
          // Fallback to simple chunking
          const fallbackChunks = chunkTextLocally(text);
          setChunks(fallbackChunks);
        }
      }
    } catch (error) {
      console.error('Error fetching chunks:', error);
      // Fallback chunking
      const fallbackChunks = chunkTextLocally(text);
      setChunks(fallbackChunks);
    } finally {
      setLoading(false);
    }
  };

  const chunkTextLocally = (text: string): string[] => {
    // Simple local chunking algorithm
    const words = text.split(/\s+/);
    const chunks: string[] = [];
    let currentChunk: string[] = [];

    words.forEach((word, index) => {
      currentChunk.push(word);
      
      // Create chunks of 2-4 words, breaking at punctuation
      if (
        currentChunk.length >= 3 ||
        word.match(/[,;:]$/) ||
        word.match(/[.!?]$/) ||
        index === words.length - 1
      ) {
        chunks.push(currentChunk.join(' '));
        currentChunk = [];
      }
    });

    return chunks.filter(c => c.trim().length > 0);
  };

  useEffect(() => {
    if (isPlaying && currentChunkIndex < chunks.length) {
      intervalRef.current = setInterval(() => {
        setCurrentChunkIndex(prev => {
          if (prev >= chunks.length - 1) {
            setIsPlaying(false);
            setShowCompletionMessage(true);
            return prev;
          }
          return prev + 1;
        });
      }, chunkDelay);
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [isPlaying, chunkDelay, chunks.length, currentChunkIndex]);

  const togglePlay = () => {
    if (currentChunkIndex >= chunks.length - 1) {
      setCurrentChunkIndex(0);
    }
    setIsPlaying(!isPlaying);
  };

  const handleReset = () => {
    setIsPlaying(false);
    setCurrentChunkIndex(0);
    setShowCompletionMessage(false);
  };

  const handleStartQuestions = () => {
    if (onStartQuestions) {
      onStartQuestions(text);
    }
  };

  const progress = chunks.length > 0 ? (currentChunkIndex / chunks.length) * 100 : 0;

  // Show completion message and question prompt
  if (showCompletionMessage) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 to-pink-900 flex items-center justify-center">
        <div className="max-w-2xl mx-auto p-8 text-center">
          <div className="bg-white rounded-2xl p-12 shadow-2xl">
            <div className="text-6xl mb-6">🎉</div>
            <h2 className="text-3xl font-bold text-gray-800 mb-4">
              Reading Complete!
            </h2>
            <p className="text-xl text-gray-600 mb-8">
              Great job! You've finished reading the text using Chunk mode.
            </p>
            <div className="bg-purple-50 border border-purple-200 rounded-lg p-6 mb-8">
              <h3 className="text-xl font-bold text-purple-800 mb-2">
                Now answer these questions to check your understanding
              </h3>
              <p className="text-purple-700">
                The questions will be displayed using the same chunking technique to maintain your reading flow.
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
                className="px-8 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition font-semibold text-lg"
              >
                ← Back to Home
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-900 to-pink-900">
        <div className="text-white text-2xl">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-white mx-auto mb-4"></div>
          Processing text into chunks...
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 to-pink-900 flex flex-col">
      {/* Header */}
      <div className="bg-black bg-opacity-30 p-4">
        <div className="container mx-auto flex justify-between items-center">
          <button
            onClick={onBack}
            className="px-4 py-2 bg-white bg-opacity-20 text-white rounded-lg hover:bg-opacity-30 transition"
          >
            ← Back
          </button>
          <h2 className="text-2xl font-bold text-white">Chunk Reading Mode</h2>
          <div className="w-20"></div>
        </div>
      </div>

      {/* Main Reading Area */}
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="max-w-4xl w-full">
          {/* Chunk Display */}
          <div className="bg-white rounded-2xl p-12 shadow-2xl mb-8">
            <div className="min-h-[200px] flex items-center justify-center">
              {chunks.map((chunk, index) => (
                <span
                  key={index}
                  className={`text-3xl transition-all duration-300 ${
                    index === currentChunkIndex
                      ? 'text-purple-900 font-bold scale-110'
                      : index < currentChunkIndex
                      ? 'text-gray-400'
                      : 'text-gray-300'
                  } ${index === currentChunkIndex ? 'inline-block' : 'hidden'}`}
                >
                  {chunk}
                </span>
              ))}
            </div>
          </div>

          {/* All Chunks Preview */}
          <div className="bg-white bg-opacity-10 backdrop-blur-lg rounded-xl p-6 mb-8 max-h-60 overflow-y-auto">
            <p className="text-white leading-relaxed">
              {chunks.map((chunk, index) => (
                <span
                  key={index}
                  className={`transition-all duration-200 ${
                    index === currentChunkIndex
                      ? 'bg-yellow-400 text-black font-bold px-1 rounded'
                      : index < currentChunkIndex
                      ? 'text-gray-300'
                      : 'text-white'
                  }`}
                >
                  {chunk}{' '}
                </span>
              ))}
            </p>
          </div>

          {/* Progress Bar */}
          <div className="mb-8">
            <div className="w-full bg-white bg-opacity-20 rounded-full h-3">
              <div
                className="bg-pink-400 h-3 rounded-full transition-all duration-300"
                style={{ width: `${progress}%` }}
              ></div>
            </div>
            <p className="text-white text-center mt-2">
              Chunk {currentChunkIndex + 1} of {chunks.length}
            </p>
          </div>

          {/* Controls */}
          <div className="bg-black bg-opacity-30 rounded-xl p-6">
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
              <button
                onClick={() => setCurrentChunkIndex(Math.min(chunks.length - 1, currentChunkIndex + 1))}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-semibold"
              >
                Next →
              </button>
            </div>

            {/* Speed Control */}
            <div className="bg-white bg-opacity-10 backdrop-blur-lg rounded-xl p-6">
              <div className="flex items-center justify-between mb-4">
                <label className="text-white font-semibold">
                  Chunk Display Time: {chunkDelay}ms
                </label>
                <div className="flex gap-2">
                  <button
                    onClick={() => setChunkDelay(Math.max(200, chunkDelay - 100))}
                    className="px-3 py-1 bg-white bg-opacity-20 text-white rounded hover:bg-opacity-30 transition"
                  >
                    Faster
                  </button>
                  <button
                    onClick={() => setChunkDelay(Math.min(2000, chunkDelay + 100))}
                    className="px-3 py-1 bg-white bg-opacity-20 text-white rounded hover:bg-opacity-30 transition"
                  >
                    Slower
                  </button>
                </div>
              </div>
              <input
                type="range"
                min="200"
                max="2000"
                step="100"
                value={chunkDelay}
                onChange={(e) => setChunkDelay(parseInt(e.target.value))}
                className="w-full h-2 bg-white bg-opacity-30 rounded-lg appearance-none cursor-pointer"
              />
            </div>

            {/* Tips */}
            <div className="mt-6 bg-pink-400 bg-opacity-20 border border-pink-400 rounded-lg p-4">
              <p className="text-pink-100 text-sm">
                <strong>💡 Tip:</strong> Focus on understanding each phrase as a complete unit of meaning. 
                Don't try to pronounce each word - let your brain process the whole chunk visually.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChunkReader;


