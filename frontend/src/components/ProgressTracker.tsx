import React, { useState, useEffect } from 'react';

interface ReadingSession {
  date: string;
  mode: string;
  duration: number;
  wordsRead: number;
  wpm: number;
}

const ProgressTracker: React.FC = () => {
  const [sessions, setSessions] = useState<ReadingSession[]>([]);
  const [showStats, setShowStats] = useState(false);

  useEffect(() => {
    // Load sessions from localStorage
    const stored = localStorage.getItem('readingSessions');
    if (stored) {
      setSessions(JSON.parse(stored));
    }
  }, []);

  const stats = {
    totalSessions: sessions.length,
    totalWordsRead: sessions.reduce((acc, s) => acc + s.wordsRead, 0),
    averageWPM: sessions.length > 0 
      ? Math.round(sessions.reduce((acc, s) => acc + s.wpm, 0) / sessions.length)
      : 0,
    totalTime: sessions.reduce((acc, s) => acc + s.duration, 0),
  };

  return (
    <div className="bg-white rounded-xl shadow-lg p-8 mb-8">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-800">Your Progress</h2>
        <button
          onClick={() => setShowStats(!showStats)}
          className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition"
        >
          {showStats ? 'Hide Stats' : 'Show Stats'}
        </button>
      </div>

      {showStats && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-4 text-center">
              <div className="text-3xl font-bold text-blue-600">{stats.totalSessions}</div>
              <div className="text-sm text-gray-600">Sessions</div>
            </div>
            <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-4 text-center">
              <div className="text-3xl font-bold text-green-600">
                {stats.totalWordsRead.toLocaleString()}
              </div>
              <div className="text-sm text-gray-600">Words Read</div>
            </div>
            <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg p-4 text-center">
              <div className="text-3xl font-bold text-purple-600">{stats.averageWPM}</div>
              <div className="text-sm text-gray-600">Avg WPM</div>
            </div>
            <div className="bg-gradient-to-br from-orange-50 to-orange-100 rounded-lg p-4 text-center">
              <div className="text-3xl font-bold text-orange-600">
                {Math.round(stats.totalTime / 60)}
              </div>
              <div className="text-sm text-gray-600">Minutes</div>
            </div>
          </div>

          {sessions.length === 0 ? (
            <div className="text-center text-gray-500 py-8">
              <p className="text-lg">No reading sessions yet!</p>
              <p>Start a reading exercise to track your progress.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-2 px-4 text-gray-700">Date</th>
                    <th className="text-left py-2 px-4 text-gray-700">Mode</th>
                    <th className="text-right py-2 px-4 text-gray-700">Words</th>
                    <th className="text-right py-2 px-4 text-gray-700">WPM</th>
                    <th className="text-right py-2 px-4 text-gray-700">Duration</th>
                  </tr>
                </thead>
                <tbody>
                  {sessions.slice(-10).reverse().map((session, index) => (
                    <tr key={index} className="border-b hover:bg-gray-50">
                      <td className="py-2 px-4 text-gray-600">
                        {new Date(session.date).toLocaleDateString()}
                      </td>
                      <td className="py-2 px-4">
                        <span className={`px-2 py-1 rounded text-xs font-semibold ${
                          session.mode === 'RSVP' 
                            ? 'bg-indigo-100 text-indigo-800' 
                            : 'bg-purple-100 text-purple-800'
                        }`}>
                          {session.mode}
                        </span>
                      </td>
                      <td className="text-right py-2 px-4 text-gray-600">
                        {session.wordsRead}
                      </td>
                      <td className="text-right py-2 px-4 text-gray-600 font-semibold">
                        {session.wpm}
                      </td>
                      <td className="text-right py-2 px-4 text-gray-600">
                        {Math.round(session.duration)}s
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default ProgressTracker;


