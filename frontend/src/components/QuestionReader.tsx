import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';

interface Question {
  question: string;
  options: {
    A: string;
    B: string;
    C: string;
    D: string;
  };
  answer: string;
}

interface QuestionReaderProps {
  text: string;
  onBack: () => void;
  readingMode: 'rsvp' | 'chunk';
  exercises: Question[];
  exerciseId?: number;
}

const QuestionReader: React.FC<QuestionReaderProps> = ({ text, onBack, readingMode, exercises, exerciseId }) => {
  const { sessionToken } = useAuth();
  const [questions, setQuestions] = useState<Question[]>(exercises);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [selectedAnswer, setSelectedAnswer] = useState<string | null>(null);
  const [showAnswer, setShowAnswer] = useState(false);
  const [isCorrect, setIsCorrect] = useState(false);
  const [loading, setLoading] = useState(false);
  const [answers, setAnswers] = useState<{ [key: number]: { answer: string; isCorrect: boolean } }>({});
  const [quizCompleted, setQuizCompleted] = useState(false);
  const [submittingProgress, setSubmittingProgress] = useState(false);
  const [questionChunks, setQuestionChunks] = useState<string[]>([]);
  const [currentChunkIndex, setCurrentChunkIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [chunkDelay, setChunkDelay] = useState(800);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    setQuestions(exercises);
  }, [exercises]);

  useEffect(() => {
    if (questions.length > 0) {
      chunkCurrentQuestion();
    }
  }, [questions, currentQuestionIndex]);

  useEffect(() => {
    if (isPlaying && currentChunkIndex < questionChunks.length) {
      intervalRef.current = setInterval(() => {
        setCurrentChunkIndex(prev => {
          if (prev >= questionChunks.length - 1) {
            setIsPlaying(false);
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
  }, [isPlaying, chunkDelay, questionChunks.length, currentChunkIndex]);


  const chunkCurrentQuestion = () => {
    if (questions.length === 0) return;
    
    const currentQuestion = questions[currentQuestionIndex];
    if (readingMode === 'chunk') {
      // Use simple chunking for questions
      const words = currentQuestion.question.split(/\s+/);
      const chunks: string[] = [];
      let currentChunk: string[] = [];

      words.forEach((word, index) => {
        currentChunk.push(word);
        
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

      setQuestionChunks(chunks.filter(c => c.trim().length > 0));
    } else {
      // RSVP mode - word by word
      setQuestionChunks(currentQuestion.question.split(/\s+/).filter(word => word.length > 0));
    }
    
    setCurrentChunkIndex(0);
    setIsPlaying(true);
  };

  const handleAnswerSelect = (answerKey: string) => {
    if (showAnswer) return; // Prevent changing answer after showing result
    
    setSelectedAnswer(answerKey);
    const correct = answerKey === questions[currentQuestionIndex].answer;
    setIsCorrect(correct);
    setShowAnswer(true);
    
    // Store the answer
    setAnswers(prev => ({
      ...prev,
      [currentQuestionIndex]: { answer: answerKey, isCorrect: correct }
    }));
  };

  const submitProgress = async () => {
    if (!sessionToken || !exerciseId) return;
    
    setSubmittingProgress(true);
    
    try {
      const correctAnswers = Object.values(answers).filter(answer => answer.isCorrect).length;
      const totalQuestions = questions.length;
      const comprehensionScore = totalQuestions > 0 ? correctAnswers / totalQuestions : 0;
      
      const response = await fetch('/progress', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${sessionToken}`
        },
        body: JSON.stringify({
          exercise_id: exerciseId,
          comprehension_score: comprehensionScore,
          questions_answered: totalQuestions,
          questions_correct: correctAnswers,
          reading_speed_wpm: 250, // Default value, could be tracked from reading session
          session_duration_seconds: 300 // Default value, could be tracked from reading session
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        console.log('Progress submitted:', data);
        // Could show success message or redirect
      }
    } catch (error) {
      console.error('Failed to submit progress:', error);
    } finally {
      setSubmittingProgress(false);
    }
  };

  const handleNextQuestion = () => {
    if (currentQuestionIndex < questions.length - 1) {
      setCurrentQuestionIndex(prev => prev + 1);
      setSelectedAnswer(null);
      setShowAnswer(false);
      setIsCorrect(false);
    } else {
      // Quiz completed
      setQuizCompleted(true);
      if (sessionToken && exerciseId) {
        submitProgress();
      }
    }
  };

  const handlePreviousQuestion = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(prev => prev - 1);
      setSelectedAnswer(null);
      setShowAnswer(false);
      setIsCorrect(false);
    }
  };

  const togglePlay = () => {
    if (currentChunkIndex >= questionChunks.length - 1) {
      setCurrentChunkIndex(0);
    }
    setIsPlaying(!isPlaying);
  };

  const handleReset = () => {
    setIsPlaying(false);
    setCurrentChunkIndex(0);
  };

  const progress = questions.length > 0 ? ((currentQuestionIndex + 1) / questions.length) * 100 : 0;
  const questionProgress = questionChunks.length > 0 ? (currentChunkIndex / questionChunks.length) * 100 : 0;

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-green-900 to-blue-900">
        <div className="text-white text-2xl">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-white mx-auto mb-4"></div>
          Generating comprehension questions...
        </div>
      </div>
    );
  }

  if (questions.length === 0) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-green-900 to-blue-900">
        <div className="text-white text-center">
          <h2 className="text-2xl font-bold mb-4">No Questions Available</h2>
          <button
            onClick={onBack}
            className="px-6 py-3 bg-white bg-opacity-20 text-white rounded-lg hover:bg-opacity-30 transition"
          >
            ← Back to Reading
          </button>
        </div>
      </div>
    );
  }

  const currentQuestion = questions[currentQuestionIndex];

  // Quiz completion screen
  if (quizCompleted) {
    const correctAnswers = Object.values(answers).filter(answer => answer.isCorrect).length;
    const totalQuestions = questions.length;
    const comprehensionScore = totalQuestions > 0 ? (correctAnswers / totalQuestions) * 100 : 0;
    
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-900 to-blue-900 flex items-center justify-center">
        <div className="bg-white rounded-2xl p-12 shadow-2xl max-w-2xl w-full mx-4 text-center">
          <div className="mb-8">
            <div className={`text-6xl mb-4 ${comprehensionScore >= 70 ? 'text-green-500' : 'text-orange-500'}`}>
              {comprehensionScore >= 70 ? '🎉' : '📚'}
            </div>
            <h2 className="text-3xl font-bold text-gray-800 mb-4">
              {comprehensionScore >= 70 ? 'Excellent Work!' : 'Keep Practicing!'}
            </h2>
            <div className="text-4xl font-bold text-indigo-600 mb-2">
              {comprehensionScore.toFixed(0)}%
            </div>
            <p className="text-gray-600">
              You answered {correctAnswers} out of {totalQuestions} questions correctly
            </p>
          </div>

          <div className="bg-gray-50 rounded-xl p-6 mb-8">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">What happens next?</h3>
            <div className="text-sm text-gray-600 space-y-2">
              {comprehensionScore >= 70 ? (
                <>
                  <p>✅ This exercise is marked as <strong>completed</strong></p>
                  <p>🚀 You'll get a new exercise from your personalized queue</p>
                  <p>📈 Your progress has been saved</p>
                </>
              ) : (
                <>
                  <p>🔄 This exercise will be added to the bottom of your queue</p>
                  <p>📚 You can try it again after practicing more</p>
                  <p>💪 Keep working on your comprehension skills!</p>
                </>
              )}
            </div>
          </div>

          <div className="flex gap-4 justify-center">
            <button
              onClick={onBack}
              className="px-8 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition font-semibold"
            >
              Continue Reading
            </button>
          </div>

          {submittingProgress && (
            <div className="mt-4 text-sm text-gray-500">
              Saving your progress...
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-900 to-blue-900 flex flex-col">
      {/* Header */}
      <div className="bg-black bg-opacity-30 p-4">
        <div className="container mx-auto flex justify-between items-center">
          <button
            onClick={onBack}
            className="px-4 py-2 bg-white bg-opacity-20 text-white rounded-lg hover:bg-opacity-30 transition"
          >
            ← Back
          </button>
          <h2 className="text-2xl font-bold text-white">Comprehension Check</h2>
          <div className="text-white">
            Question {currentQuestionIndex + 1} of {questions.length}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="max-w-4xl w-full">
          {/* Question Display */}
          <div className="bg-white rounded-2xl p-12 shadow-2xl mb-8">
            <div className="min-h-[200px] flex items-center justify-center">
              {questionChunks.map((chunk, index) => (
                <span
                  key={index}
                  className={`text-3xl transition-all duration-300 ${
                    index === currentChunkIndex
                      ? 'text-green-900 font-bold scale-110'
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

          {/* Question Progress */}
          <div className="mb-8">
            <div className="w-full bg-white bg-opacity-20 rounded-full h-3">
              <div
                className="bg-green-400 h-3 rounded-full transition-all duration-300"
                style={{ width: `${questionProgress}%` }}
              ></div>
            </div>
            <p className="text-white text-center mt-2">
              {readingMode === 'chunk' ? 'Chunk' : 'Word'} {currentChunkIndex + 1} of {questionChunks.length}
            </p>
          </div>

          {/* Question Controls */}
          <div className="bg-black bg-opacity-30 rounded-xl p-6 mb-8">
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
                <label className="text-white font-semibold">
                  {readingMode === 'chunk' ? 'Chunk' : 'Word'} Display Time: {chunkDelay}ms
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
          </div>

          {/* Answer Options */}
          <div className="bg-white rounded-xl p-8 shadow-xl mb-8">
            <h3 className="text-xl font-bold text-gray-800 mb-6">Select your answer:</h3>
            <div className="space-y-4">
              {Object.entries(currentQuestion.options).map(([key, option]) => (
                <button
                  key={key}
                  onClick={() => handleAnswerSelect(key)}
                  disabled={showAnswer}
                  className={`w-full p-4 text-left rounded-lg border-2 transition-all ${
                    showAnswer
                      ? key === currentQuestion.answer
                        ? 'border-green-500 bg-green-100 text-green-800'
                        : key === selectedAnswer
                        ? 'border-red-500 bg-red-100 text-red-800'
                        : 'border-gray-300 bg-gray-50 text-gray-600'
                      : selectedAnswer === key
                      ? 'border-blue-500 bg-blue-100 text-blue-800'
                      : 'border-gray-300 hover:border-blue-400 hover:bg-blue-50'
                  }`}
                >
                  <span className="font-semibold mr-3">
                    {key}.
                  </span>
                  {option}
                </button>
              ))}
            </div>

            {/* Answer Feedback */}
            {showAnswer && (
              <div className={`mt-6 p-4 rounded-lg ${
                isCorrect ? 'bg-green-100 border border-green-300' : 'bg-red-100 border border-red-300'
              }`}>
                <div className="flex items-center">
                  <span className={`text-2xl mr-2 ${isCorrect ? 'text-green-600' : 'text-red-600'}`}>
                    {isCorrect ? '✅' : '❌'}
                  </span>
                  <span className={`font-bold ${isCorrect ? 'text-green-800' : 'text-red-800'}`}>
                    {isCorrect ? 'Correct!' : 'Incorrect'}
                  </span>
                </div>
              </div>
            )}
          </div>

          {/* Navigation */}
          <div className="flex justify-between items-center">
            <button
              onClick={handlePreviousQuestion}
              disabled={currentQuestionIndex === 0}
              className="px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              ← Previous
            </button>

            <div className="text-white text-center">
              <div className="w-full bg-white bg-opacity-20 rounded-full h-2 mb-2">
                <div
                  className="bg-blue-400 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${progress}%` }}
                ></div>
              </div>
              <p className="text-sm">Overall Progress</p>
            </div>

            <button
              onClick={handleNextQuestion}
              disabled={currentQuestionIndex === questions.length - 1 && !showAnswer}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              {currentQuestionIndex === questions.length - 1 ? 'Finish Quiz' : 'Next →'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default QuestionReader;
