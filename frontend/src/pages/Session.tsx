/**
 * Learning Session Page
 */

import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { schedule } from '../api/client';
import { useToast } from '../components/Toast';

interface Resource {
  type: string;
  title: string;
  url?: string;
  content?: string;
  platform?: string;
  duration?: string;
  channel?: string;
  source?: string;
  description?: string;
}

interface Session {
  id: string;
  module_title: string;
  session_topic?: string;
  description?: string;
  learning_objectives?: string[];
  session_number?: number;
  scheduled_time: string;
  duration_minutes: number;
  resources: Resource[];
  completed: boolean;
  notes?: string;
}

const formatDuration = (duration: string): string => {
  const seconds = parseInt(duration, 10);
  if (isNaN(seconds)) return duration;
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
};

const Session: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { showToast } = useToast();
  const [session, setSession] = useState<Session | null>(null);
  const [notes, setNotes] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadSession();
  }, [id]);

  const loadSession = async () => {
    try {
      const response = await schedule.getSession(id!);
      setSession(response.data);
      setNotes(response.data.notes || '');
    } catch (err) {
      showToast('Failed to load session', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleComplete = async () => {
    try {
      await schedule.completeSession(id!, notes);
      showToast('Session marked as complete!', 'success');
      navigate(-1);
    } catch (err) {
      showToast('Failed to mark session as complete', 'error');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-blue-600"></div>
      </div>
    );
  }

  if (!session) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-red-600">Session not found</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 py-8">
        <button
          onClick={() => navigate(-1)}
          className="text-blue-600 hover:text-blue-700 mb-6 flex items-center gap-2"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Back to Dashboard
        </button>

        <div className="bg-white rounded-lg shadow-lg p-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">{session.module_title}</h1>
          {session.session_topic && session.session_topic !== session.module_title && (
            <h2 className="text-xl text-gray-700 mb-2">{session.session_topic}</h2>
          )}
          <p className="text-gray-600 mb-4">
            Scheduled: {new Date(session.scheduled_time).toLocaleString()} · {session.duration_minutes} min
            {session.session_number && <span> · Session {session.session_number}</span>}
          </p>

          {session.description && (
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 mb-6">
              <p className="text-gray-700">{session.description}</p>
            </div>
          )}

          {session.learning_objectives && session.learning_objectives.length > 0 && (
            <div className="mb-6">
              <h3 className="text-lg font-medium text-gray-800 mb-2">Learning Objectives</h3>
              <ul className="list-disc list-inside space-y-1 text-gray-700">
                {session.learning_objectives.map((objective, idx) => (
                  <li key={idx}>{objective}</li>
                ))}
              </ul>
            </div>
          )}

          {session.completed && (
            <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg mb-6">
               This session has been completed
            </div>
          )}

          {/* Resources */}
          <div className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Learning Resources</h2>

            {session.resources.length === 0 ? (
              <p className="text-gray-600">No resources available</p>
            ) : (
              <>
                {/* Video Resources */}
                {session.resources.filter(r => r.type === 'video').length > 0 && (
                  <div className="mb-6">
                    <h3 className="text-lg font-medium text-gray-800 mb-3 flex items-center gap-2">
                      <svg className="w-5 h-5 text-red-600" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M19.615 3.184c-3.604-.246-11.631-.245-15.23 0-3.897.266-4.356 2.62-4.385 8.816.029 6.185.484 8.549 4.385 8.816 3.6.245 11.626.246 15.23 0 3.897-.266 4.356-2.62 4.385-8.816-.029-6.185-.484-8.549-4.385-8.816zm-10.615 12.816v-8l8 3.993-8 4.007z"/>
                      </svg>
                      Video Tutorials
                    </h3>
                    <div className="space-y-3">
                      {session.resources.filter(r => r.type === 'video').map((resource, idx) => (
                        <a
                          key={idx}
                          href={resource.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="block border border-gray-200 rounded-lg p-4 bg-red-50 hover:bg-red-100 transition-colors cursor-pointer"
                        >
                          <h4 className="font-medium text-gray-900">{resource.title}</h4>
                          <div className="flex items-center gap-3 mt-1 text-sm text-gray-600">
                            {resource.channel && <span>{resource.channel}</span>}
                            {resource.duration && <span>· {formatDuration(resource.duration)}</span>}
                          </div>
                        </a>
                      ))}
                    </div>
                  </div>
                )}

                {/* Article Resources */}
                {session.resources.filter(r => r.type === 'article').length > 0 && (
                  <div className="mb-6">
                    <h3 className="text-lg font-medium text-gray-800 mb-3 flex items-center gap-2">
                      <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                      Articles & Guides
                    </h3>
                    <div className="space-y-3">
                      {session.resources.filter(r => r.type === 'article').map((resource, idx) => (
                        <a
                          key={idx}
                          href={resource.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="block border border-gray-200 rounded-lg p-4 bg-blue-50 hover:bg-blue-100 transition-colors cursor-pointer"
                        >
                          <h4 className="font-medium text-gray-900">{resource.title}</h4>
                          <div className="flex items-center gap-3 mt-1 text-sm text-gray-600">
                            {resource.source && <span>{resource.source}</span>}
                          </div>
                          {resource.description && (
                            <p className="text-sm text-gray-600 mt-2 line-clamp-2">{resource.description}</p>
                          )}
                        </a>
                      ))}
                    </div>
                  </div>
                )}

                {/* Other Resources (fallback) */}
                {session.resources.filter(r => r.type !== 'video' && r.type !== 'article').length > 0 && (
                  <div className="mb-6">
                    <h3 className="text-lg font-medium text-gray-800 mb-3 flex items-center gap-2">
                      <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                      </svg>
                      Other Resources
                    </h3>
                    <div className="space-y-3">
                      {session.resources.filter(r => r.type !== 'video' && r.type !== 'article').map((resource, idx) => (
                        <div key={idx} className="border border-gray-200 rounded-lg p-4 bg-gray-50 hover:bg-gray-100 transition-colors">
                          <h4 className="font-medium text-gray-900">{resource.title}</h4>
                          <p className="text-sm text-gray-600 mt-1">{resource.type}</p>
                          {resource.url && (
                            <a
                              href={resource.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-blue-600 hover:text-blue-700 text-sm mt-2 inline-flex items-center gap-1"
                            >
                              Open Resource
                              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                              </svg>
                            </a>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </>
            )}
          </div>

          {/* Notes */}
          {!session.completed && (
            <div className="mb-8">
              <label className="block text-lg font-medium text-gray-700 mb-2">
                Session Notes
              </label>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                rows={4}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Add your notes here..."
              />
            </div>
          )}

          {/* Actions */}
          {!session.completed && (
            <button
              onClick={handleComplete}
              className="w-full bg-blue-600 text-white py-3 px-6 rounded-lg hover:bg-blue-700 transition-colors font-medium text-lg"
            >
              Mark as Complete
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default Session;
