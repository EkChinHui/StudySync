/**
 * Learning Session Page
 */

import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { schedule } from '../api/client';

interface Session {
  id: string;
  module_title: string;
  scheduled_time: string;
  duration_minutes: number;
  resources: any[];
  completed: boolean;
  notes?: string;
}

const Session: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
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
      alert('Failed to load session');
    } finally {
      setLoading(false);
    }
  };

  const handleComplete = async () => {
    try {
      await schedule.completeSession(id!, notes);
      alert('Session marked as complete!');
      navigate(-1);
    } catch (err) {
      alert('Failed to mark session as complete');
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
          className="text-blue-600 hover:text-blue-700 mb-6 flex items-center"
        >
          ê Back to Dashboard
        </button>

        <div className="bg-white rounded-lg shadow-lg p-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">{session.module_title}</h1>
          <p className="text-gray-600 mb-6">
            Scheduled: {new Date(session.scheduled_time).toLocaleString()} " {session.duration_minutes} min
          </p>

          {session.completed && (
            <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg mb-6">
               This session has been completed
            </div>
          )}

          {/* Resources */}
          <div className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Learning Resources</h2>
            <div className="space-y-3">
              {session.resources.length === 0 ? (
                <p className="text-gray-600">No resources available</p>
              ) : (
                session.resources.map((resource, idx) => (
                  <div key={idx} className="border border-gray-200 rounded-lg p-4">
                    <h3 className="font-medium text-gray-900">{resource.title}</h3>
                    <p className="text-sm text-gray-600 mt-1">{resource.type}</p>
                    {resource.url && (
                      <a
                        href={resource.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:text-blue-700 text-sm mt-2 inline-block"
                      >
                        Open Resource í
                      </a>
                    )}
                    {resource.content && (
                      <div className="mt-2 text-sm text-gray-700 whitespace-pre-wrap">
                        {resource.content.substring(0, 200)}...
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
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
