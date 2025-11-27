/**
 * Dashboard Page
 */

import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { learningPaths, schedule } from '../api/client';
import { useToast } from '../components/Toast';

interface Subtopic {
  title: string;
  description: string;
  estimated_minutes: number;
}

interface Module {
  module_id: string;
  title: string;
  duration_hours: number;
  learning_objectives: string[];
  subtopics: Subtopic[];
  prerequisites: string[];
  resources: any[];
}

interface StudySession {
  id: string;
  module_id: string;
  module_title: string;
  session_topic?: string;
  description?: string;
  scheduled_time: string;
  duration_minutes: number;
  completed: boolean;
  resources: any[];
}

interface QuizStatus {
  completed: boolean;
  score: number | null;
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
  quiz_status: Record<string, QuizStatus>;
  upcoming_sessions: StudySession[];
}

const Dashboard: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { showToast } = useToast();
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
      showToast('Failed to load full schedule', 'error');
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
      showToast('Schedule downloaded', 'success');
    } catch (err) {
      showToast('Failed to download schedule', 'error');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="text-center">
          <div className="relative w-16 h-16 mx-auto mb-4">
            <div className="absolute inset-0 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-full animate-ping opacity-20"></div>
            <div className="relative w-16 h-16 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-full flex items-center justify-center">
              <svg className="w-8 h-8 text-white animate-pulse" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
              </svg>
            </div>
          </div>
          <p className="text-gray-600">Loading your dashboard...</p>
        </div>
      </div>
    );
  }

  if (error || !dashboard) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <p className="text-red-600 font-medium">{error || 'Dashboard not found'}</p>
          <button
            onClick={() => navigate('/')}
            className="mt-4 text-blue-600 hover:text-blue-700 font-medium"
          >
            Go back home
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-md border-b border-gray-100 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2 cursor-pointer" onClick={() => navigate('/')}>
                <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-xl flex items-center justify-center">
                  <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                  </svg>
                </div>
                <span className="text-xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent hidden sm:block">
                  StudySync
                </span>
              </div>
              <div className="h-6 w-px bg-gray-300 hidden sm:block" />
              <div className="hidden sm:block">
                <h1 className="text-lg font-bold text-gray-900">{dashboard.topic}</h1>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={handleLoadAllSessions}
                className="text-gray-600 hover:text-gray-900 px-4 py-2 rounded-xl hover:bg-gray-100 transition-colors text-sm font-medium flex items-center gap-2"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
                <span className="hidden sm:inline">Full Schedule</span>
              </button>
              <button
                onClick={handleDownloadSchedule}
                className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white px-4 py-2 rounded-xl hover:shadow-lg hover:shadow-blue-500/25 transition-all text-sm font-medium flex items-center gap-2"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
                <span className="hidden sm:inline">Download</span>
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Mobile Title */}
        <div className="sm:hidden mb-6">
          <h1 className="text-2xl font-bold text-gray-900">{dashboard.topic}</h1>
          <p className="text-gray-600 text-sm">Your personalized learning path</p>
        </div>

        {/* Progress Overview */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          {[
            {
              label: 'Completion',
              value: `${Math.round(dashboard.progress.completion_percentage)}%`,
              icon: '📊',
              color: 'from-blue-500 to-indigo-500',
              bg: 'bg-blue-50',
            },
            {
              label: 'Sessions Done',
              value: `${dashboard.progress.sessions_completed}/${dashboard.progress.total_sessions}`,
              icon: '✅',
              color: 'from-emerald-500 to-teal-500',
              bg: 'bg-emerald-50',
            },
            {
              label: 'Quiz Average',
              value: `${Math.round(dashboard.progress.average_quiz_score * 100)}%`,
              icon: '🎯',
              color: 'from-purple-500 to-pink-500',
              bg: 'bg-purple-50',
            },
            {
              label: 'Quizzes Taken',
              value: dashboard.progress.quizzes_taken,
              icon: '📝',
              color: 'from-amber-500 to-orange-500',
              bg: 'bg-amber-50',
            },
          ].map((stat) => (
            <div key={stat.label} className="bg-white rounded-2xl shadow-sm border border-gray-100 p-5 hover:shadow-md transition-shadow">
              <div className="flex items-center gap-3 mb-3">
                <div className={`w-10 h-10 ${stat.bg} rounded-xl flex items-center justify-center`}>
                  <span className="text-lg">{stat.icon}</span>
                </div>
              </div>
              <p className={`text-2xl font-bold bg-gradient-to-r ${stat.color} bg-clip-text text-transparent`}>
                {stat.value}
              </p>
              <p className="text-gray-500 text-sm mt-1">{stat.label}</p>
            </div>
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Upcoming Sessions */}
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-bold text-gray-900">Upcoming Sessions</h2>
              <span className="text-sm text-gray-500">{dashboard.upcoming_sessions.length} remaining</span>
            </div>
            <div className="space-y-3">
              {dashboard.upcoming_sessions.length === 0 ? (
                <div className="text-center py-8">
                  <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-3">
                    <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  <p className="text-gray-600 font-medium">All sessions completed!</p>
                  <p className="text-gray-500 text-sm">Great job on finishing your learning path.</p>
                </div>
              ) : (
                dashboard.upcoming_sessions.map((session, index) => (
                  <div
                    key={session.id}
                    className={`group p-4 rounded-xl border-2 transition-all duration-200 cursor-pointer ${
                      index === 0
                        ? 'border-blue-200 bg-blue-50 hover:border-blue-300'
                        : 'border-gray-100 hover:border-gray-200 hover:bg-gray-50'
                    }`}
                    onClick={() => navigate(`/session/${session.id}`)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          {index === 0 && (
                            <span className="bg-blue-600 text-white text-xs px-2 py-0.5 rounded-full font-medium">
                              Next
                            </span>
                          )}
                          <h3 className="font-semibold text-gray-900">{session.module_title}</h3>
                        </div>
                        {session.session_topic && session.session_topic !== session.module_title && (
                          <p className="text-sm text-gray-600 mt-1">{session.session_topic}</p>
                        )}
                        <div className="flex items-center gap-3 mt-2 text-sm text-gray-500">
                          <span className="flex items-center gap-1">
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                            </svg>
                            {new Date(session.scheduled_time).toLocaleDateString()}
                          </span>
                          <span className="flex items-center gap-1">
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            {session.duration_minutes} min
                          </span>
                        </div>
                      </div>
                      <svg className="w-5 h-5 text-gray-400 group-hover:text-gray-600 group-hover:translate-x-1 transition-all" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Curriculum */}
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-bold text-gray-900">Curriculum</h2>
              <span className="text-sm text-gray-500">{dashboard.curriculum.modules?.length || 0} modules</span>
            </div>
            <div className="space-y-3">
              {dashboard.curriculum.modules?.map((module, index) => {
                const quizStatus = dashboard.quiz_status?.[module.module_id];
                const isCompleted = quizStatus?.completed;
                const score = quizStatus?.score;

                return (
                  <div key={module.module_id} className="p-4 rounded-xl border border-gray-100 hover:border-gray-200 hover:bg-gray-50 transition-all">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex items-start gap-3 flex-1">
                        <div className={`w-8 h-8 rounded-lg flex items-center justify-center text-sm font-bold flex-shrink-0 ${
                          isCompleted
                            ? 'bg-green-100 text-green-700'
                            : 'bg-gray-100 text-gray-600'
                        }`}>
                          {isCompleted ? (
                            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                              <path d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" />
                            </svg>
                          ) : (
                            index + 1
                          )}
                        </div>
                        <div className="flex-1 min-w-0">
                          <h3 className="font-semibold text-gray-900 truncate">{module.title}</h3>
                          <p className="text-sm text-gray-500 mt-0.5">
                            {module.duration_hours}h · {module.subtopics?.length || 0} topics
                          </p>
                        </div>
                      </div>
                      {isCompleted ? (
                        <div className="flex items-center gap-2 flex-shrink-0">
                          <span className="text-sm font-medium text-green-600 bg-green-50 px-2 py-1 rounded-lg">
                            {Math.round((score || 0) * 100)}%
                          </span>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              navigate(`/quiz/${module.module_id}?learning_path_id=${dashboard.learning_path_id}&review=true`);
                            }}
                            className="text-gray-500 hover:text-gray-700 text-sm px-3 py-2 rounded-lg hover:bg-gray-100 transition-all font-medium"
                          >
                            Review
                          </button>
                        </div>
                      ) : (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            navigate(`/quiz/${module.module_id}?learning_path_id=${dashboard.learning_path_id}`);
                          }}
                          className="bg-gradient-to-r from-purple-600 to-indigo-600 text-white text-sm px-4 py-2 rounded-lg hover:shadow-md hover:shadow-purple-500/25 transition-all font-medium flex-shrink-0"
                        >
                          Take Quiz
                        </button>
                      )}
                    </div>
                    <div className="mt-3 flex flex-wrap gap-2">
                      {module.subtopics?.slice(0, 3).map((topic, idx) => (
                        <span
                          key={idx}
                          className="bg-gray-100 text-gray-600 text-xs px-2 py-1 rounded-lg"
                        >
                          {typeof topic === 'string' ? topic : topic.title}
                        </span>
                      ))}
                      {module.subtopics && module.subtopics.length > 3 && (
                        <span className="text-gray-400 text-xs px-2 py-1">
                          +{module.subtopics.length - 3} more
                        </span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>

      {/* Full Schedule Modal */}
      {showAllSessions && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-3xl shadow-2xl w-full max-w-4xl max-h-[85vh] flex flex-col overflow-hidden">
            <div className="p-6 border-b border-gray-100 flex justify-between items-center">
              <div>
                <h2 className="text-xl font-bold text-gray-900">Full Study Schedule</h2>
                <p className="text-gray-500 text-sm mt-1">{allSessions.length} sessions total</p>
              </div>
              <button
                onClick={() => setShowAllSessions(false)}
                className="w-10 h-10 rounded-xl hover:bg-gray-100 flex items-center justify-center transition-colors"
              >
                <svg className="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="p-6 overflow-y-auto flex-1">
              {loadingSessions ? (
                <div className="flex justify-center py-12">
                  <div className="w-12 h-12 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin"></div>
                </div>
              ) : (
                <div className="space-y-3">
                  {allSessions.map((session, index) => (
                    <div
                      key={session.id}
                      className={`p-4 rounded-xl border-2 flex items-center justify-between transition-all ${
                        session.completed
                          ? 'bg-green-50 border-green-200'
                          : 'bg-white border-gray-100 hover:border-gray-200'
                      }`}
                    >
                      <div className="flex items-center gap-4">
                        <div className={`w-10 h-10 rounded-xl flex items-center justify-center font-bold text-sm ${
                          session.completed
                            ? 'bg-green-100 text-green-700'
                            : 'bg-gray-100 text-gray-600'
                        }`}>
                          {session.completed ? (
                            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                              <path d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" />
                            </svg>
                          ) : (
                            index + 1
                          )}
                        </div>
                        <div>
                          <h3 className="font-semibold text-gray-900">{session.module_title}</h3>
                          {session.session_topic && session.session_topic !== session.module_title && (
                            <p className="text-sm text-gray-600">{session.session_topic}</p>
                          )}
                          <p className="text-sm text-gray-500 mt-1">
                            {new Date(session.scheduled_time).toLocaleString()} · {session.duration_minutes} min
                          </p>
                        </div>
                      </div>
                      {!session.completed && (
                        <button
                          onClick={() => {
                            setShowAllSessions(false);
                            navigate(`/session/${session.id}`);
                          }}
                          className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white text-sm px-4 py-2 rounded-lg hover:shadow-md transition-all font-medium"
                        >
                          Start
                        </button>
                      )}
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
