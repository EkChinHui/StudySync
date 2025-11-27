/**
 * Dashboard Page
 */

import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { learningPaths, schedule } from '../api/client';

interface Module {
  module_id: string;
  title: string;
  duration_hours: number;
  learning_objectives: string[];
  subtopics: string[];
  prerequisites: string[];
  resources: any[];
}

interface StudySession {
  id: string;
  module_id: string;
  module_title: string;
  description?: string;
  scheduled_time: string;
  duration_minutes: number;
  completed: boolean;
  resources: any[];
}

interface DashboardData {
  learning_path_id: string;
  topic: string;
  progress: {
    completion_percentage: number;
    sessions_completed: number;
    total_sessions: number;
    average_quiz_score: number;
    quizzes_taken: number;
  };
  curriculum: {
    modules: Module[];
  };
  upcoming_sessions: StudySession[];
}

const Dashboard: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const [showAllSessions, setShowAllSessions] = useState(false);
  const [allSessions, setAllSessions] = useState<StudySession[]>([]);
  const [loadingSessions, setLoadingSessions] = useState(false);

  useEffect(() => {
    loadDashboard();
  }, [id]);

  const loadDashboard = async () => {
    try {
      const response = await learningPaths.getDashboard(id!);
      setDashboard(response.data);
    } catch (err) {
      setError('Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  };

  const handleLoadAllSessions = async () => {
    if (allSessions.length > 0) {
      setShowAllSessions(true);
      return;
    }

    setLoadingSessions(true);
    try {
      const response = await learningPaths.getSessions(id!);
      setAllSessions(response.data);
      setShowAllSessions(true);
    } catch (err) {
      alert('Failed to load full schedule');
    } finally {
      setLoadingSessions(false);
    }
  };

  const handleDownloadSchedule = async () => {
    try {
      const response = await schedule.downloadICS(id!);
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `studysync_${dashboard?.topic}.ics`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      alert('Failed to download schedule');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-blue-600"></div>
      </div>
    );
  }

  if (error || !dashboard) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-red-600">{error || 'Dashboard not found'}</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">{dashboard.topic}</h1>
              <p className="text-gray-600 mt-1">Your personalized learning path</p>
            </div>
            <div className="flex space-x-3">
              <button
                onClick={handleLoadAllSessions}
                className="bg-white text-blue-600 border border-blue-600 px-4 py-2 rounded-lg hover:bg-blue-50 transition-colors"
              >
                View Full Schedule
              </button>
              <button
                onClick={handleDownloadSchedule}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
              >
                Download Schedule
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Progress Overview */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <p className="text-gray-600 text-sm mb-1">Completion</p>
            <p className="text-3xl font-bold text-blue-600">
              {Math.round(dashboard.progress.completion_percentage)}%
            </p>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <p className="text-gray-600 text-sm mb-1">Sessions Done</p>
            <p className="text-3xl font-bold text-green-600">
              {dashboard.progress.sessions_completed}/{dashboard.progress.total_sessions}
            </p>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <p className="text-gray-600 text-sm mb-1">Avg Quiz Score</p>
            <p className="text-3xl font-bold text-purple-600">
              {Math.round(dashboard.progress.average_quiz_score * 100)}%
            </p>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <p className="text-gray-600 text-sm mb-1">Quizzes Taken</p>
            <p className="text-3xl font-bold text-orange-600">
              {dashboard.progress.quizzes_taken}
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Upcoming Sessions */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Upcoming Sessions</h2>
            <div className="space-y-3">
              {dashboard.upcoming_sessions.length === 0 ? (
                <p className="text-gray-600">No upcoming sessions</p>
              ) : (
                dashboard.upcoming_sessions.map((session) => (
                  <div
                    key={session.id}
                    className="border border-gray-200 rounded-lg p-4 hover:border-blue-400 transition-colors cursor-pointer"
                    onClick={() => navigate(`/session/${session.id}`)}
                  >
                    <h3 className="font-semibold text-gray-900">{session.module_title}</h3>
                    <p className="text-sm text-gray-600 mt-1">
                      {new Date(session.scheduled_time).toLocaleString()}
                    </p>
                    <p className="text-sm text-gray-500">{session.duration_minutes} minutes</p>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Curriculum */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Curriculum</h2>
            <div className="space-y-3">
              {dashboard.curriculum.modules?.map((module) => (
                <div key={module.module_id} className="border border-gray-200 rounded-lg p-4">
                  <h3 className="font-semibold text-gray-900">{module.title}</h3>
                  <p className="text-sm text-gray-600 mt-1">
                    {module.duration_hours} hours " {module.subtopics.length} topics
                  </p>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {module.subtopics.slice(0, 3).map((topic, idx) => (
                      <span
                        key={idx}
                        className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded"
                      >
                        {topic}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Full Schedule Modal */}
      {showAllSessions && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[80vh] flex flex-col">
            <div className="p-6 border-b border-gray-200 flex justify-between items-center">
              <h2 className="text-2xl font-bold text-gray-900">Full Study Schedule</h2>
              <button
                onClick={() => setShowAllSessions(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="p-6 overflow-y-auto flex-1">
              {loadingSessions ? (
                <div className="flex justify-center py-12">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-4 border-blue-600"></div>
                </div>
              ) : (
                <div className="space-y-4">
                  {allSessions.map((session) => (
                    <div
                      key={session.id}
                      className={`border rounded-lg p-4 flex justify-between items-center ${session.completed ? 'bg-green-50 border-green-200' : 'bg-white border-gray-200'
                        }`}
                    >
                      <div>
                        <h3 className="font-semibold text-gray-900">{session.module_title}</h3>
                        {session.description && (
                          <p className="text-sm text-gray-500 mt-1">{session.description}</p>
                        )}
                        <p className="text-sm text-gray-600 mt-1">
                          {new Date(session.scheduled_time).toLocaleString()}
                        </p>
                      </div>
                      <div className="flex items-center space-x-4">
                        <span className="text-sm text-gray-500">{session.duration_minutes} min</span>
                        {session.completed ? (
                          <span className="text-green-600 font-medium text-sm">Completed</span>
                        ) : (
                          <button
                            onClick={() => {
                              setShowAllSessions(false);
                              navigate(`/session/${session.id}`);
                            }}
                            className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                          >
                            Start
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
