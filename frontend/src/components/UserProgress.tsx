import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';

interface ProgressData {
  total_exercises: number;
  completed_exercises: number;
  failed_exercises: number;
  queue_count: number;
  avg_comprehension: number;
  avg_reading_speed: number;
  total_reading_time_seconds: number;
  completion_rate: number;
}

const UserProgress: React.FC = () => {
  const { sessionToken } = useAuth();
  const [progress, setProgress] = useState<ProgressData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (sessionToken) {
      fetchProgress();
    } else {
      setLoading(false);
    }
  }, [sessionToken]);

  const fetchProgress = async () => {
    try {
      const response = await fetch('/user/progress', {
        headers: {
          'Authorization': `Bearer ${sessionToken}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setProgress(data.progress);
      }
    } catch (error) {
      console.error('Failed to fetch progress:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatTime = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    
    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    }
    return `${minutes}m`;
  };

  if (loading) {
    return (
      <div className="bg-white rounded-xl shadow-lg p-6">
        <h3 className="text-xl font-bold text-gray-800 mb-4">Your Progress</h3>
        <div className="animate-pulse space-y-3">
          <div className="h-4 bg-gray-200 rounded w-3/4"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2"></div>
          <div className="h-4 bg-gray-200 rounded w-2/3"></div>
        </div>
      </div>
    );
  }

  if (!progress) {
    return null;
  }

  return (
    <div className="bg-white rounded-xl shadow-lg p-6">
      <h3 className="text-xl font-bold text-gray-800 mb-4">Your Progress</h3>
      
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="text-center p-3 bg-green-50 rounded-lg">
          <div className="text-2xl font-bold text-green-600">{progress.completed_exercises}</div>
          <div className="text-sm text-green-700">Completed</div>
        </div>
        
        <div className="text-center p-3 bg-red-50 rounded-lg">
          <div className="text-2xl font-bold text-red-600">{progress.failed_exercises}</div>
          <div className="text-sm text-red-700">Need Review</div>
        </div>
      </div>

      <div className="space-y-3">
        <div className="flex justify-between items-center">
          <span className="text-gray-600">Completion Rate</span>
          <span className="font-semibold text-indigo-600">{progress.completion_rate}%</span>
        </div>
        
        <div className="flex justify-between items-center">
          <span className="text-gray-600">Queue Length</span>
          <span className="font-semibold text-blue-600">{progress.queue_count}</span>
        </div>
        
        <div className="flex justify-between items-center">
          <span className="text-gray-600">Avg Comprehension</span>
          <span className="font-semibold text-purple-600">{(progress.avg_comprehension * 100).toFixed(0)}%</span>
        </div>
        
        <div className="flex justify-between items-center">
          <span className="text-gray-600">Avg Reading Speed</span>
          <span className="font-semibold text-orange-600">{progress.avg_reading_speed.toFixed(0)} WPM</span>
        </div>
        
        <div className="flex justify-between items-center">
          <span className="text-gray-600">Total Reading Time</span>
          <span className="font-semibold text-gray-800">{formatTime(progress.total_reading_time_seconds)}</span>
        </div>
      </div>

      <div className="mt-4 p-3 bg-blue-50 rounded-lg">
        <div className="text-sm text-blue-800">
          <strong>How the Queue Works:</strong>
        </div>
        <div className="text-xs text-blue-700 mt-1">
          • Complete exercises with 70%+ comprehension to mark them as done<br/>
          • Failed exercises are moved to the bottom of your queue for review<br/>
          • Your personalized queue adapts based on your performance
        </div>
      </div>
    </div>
  );
};

export default UserProgress;
