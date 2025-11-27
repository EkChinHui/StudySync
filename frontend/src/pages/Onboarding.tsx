/**
 * Onboarding Page - Create Learning Path
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

interface ProgressMessage {
  message: string;
  phase: string;
  timestamp: string;
}

const Onboarding: React.FC = () => {
  const [step, setStep] = useState<'topic' | 'commitment' | 'creating'>('topic');
  const [topic, setTopic] = useState('');
  const [commitmentLevel, setCommitmentLevel] = useState('moderate');
  const [proficiencyLevel, setProficiencyLevel] = useState('beginner');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [progressMessages, setProgressMessages] = useState<ProgressMessage[]>([]);
  const [currentPhase, setCurrentPhase] = useState('');

  const navigate = useNavigate();

  const handleTopicSubmit = () => {
    if (!topic.trim()) return;
    setStep('commitment');
  };

  const handleCreateLearningPath = async () => {
    setStep('creating');
    setLoading(true);
    setError('');
    setProgressMessages([]);
    setCurrentPhase('');

    const params = new URLSearchParams({
      topic,
      commitment_level: commitmentLevel,
      proficiency_level: proficiencyLevel,
    });

    if (startDate) {
      params.append('start_date', startDate);
    }
    if (endDate) {
      params.append('end_date', endDate);
    }

    const eventSource = new EventSource(
      `http://localhost:8000/api/learning-paths/create/stream?${params.toString()}`
    );

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        if (data.type === 'progress') {
          setCurrentPhase(data.phase);
          setProgressMessages(prev => [...prev, {
            message: data.message,
            phase: data.phase,
            timestamp: data.timestamp
          }]);
        } else if (data.type === 'complete') {
          eventSource.close();
          setLoading(false);
          if (data.data?.learning_path_id) {
            navigate(`/dashboard/${data.data.learning_path_id}`);
          }
        } else if (data.type === 'error') {
          eventSource.close();
          setError(data.message || 'Failed to create learning path');
          setLoading(false);
          setStep('commitment');
        }
      } catch (e) {
        console.error('Error parsing SSE event:', e);
      }
    };

    eventSource.onerror = () => {
      eventSource.close();
      setError('Connection lost. Please try again.');
      setLoading(false);
      setStep('commitment');
    };
  };

  const phaseLabels: Record<string, string> = {
    'curriculum': 'Building Curriculum',
    'resources': 'Finding Resources',
    'schedule': 'Creating Schedule',
    'assessments': 'Generating Assessments',
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
      {/* Header */}
      <nav className="bg-white/80 backdrop-blur-md border-b border-gray-100">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center gap-2 cursor-pointer" onClick={() => navigate('/')}>
            <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-xl flex items-center justify-center">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
              </svg>
            </div>
            <span className="text-xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
              StudySync
            </span>
          </div>
        </div>
      </nav>

      <div className="max-w-2xl mx-auto px-6 py-12">
        {/* Progress Steps */}
        <div className="flex items-center justify-center mb-12">
          {['Topic', 'Preferences', 'Create'].map((label, index) => {
            const stepIndex = index;
            const currentStepIndex = step === 'topic' ? 0 : step === 'commitment' ? 1 : 2;
            const isActive = stepIndex === currentStepIndex;
            const isCompleted = stepIndex < currentStepIndex;

            return (
              <React.Fragment key={label}>
                <div className="flex flex-col items-center">
                  <div
                    className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold text-sm transition-all duration-300 ${
                      isCompleted
                        ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white'
                        : isActive
                        ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white ring-4 ring-blue-100'
                        : 'bg-gray-200 text-gray-500'
                    }`}
                  >
                    {isCompleted ? (
                      <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" />
                      </svg>
                    ) : (
                      index + 1
                    )}
                  </div>
                  <span className={`text-xs mt-2 font-medium ${isActive || isCompleted ? 'text-blue-600' : 'text-gray-400'}`}>
                    {label}
                  </span>
                </div>
                {index < 2 && (
                  <div
                    className={`w-20 h-1 mx-2 rounded-full transition-all duration-300 ${
                      stepIndex < currentStepIndex ? 'bg-gradient-to-r from-blue-600 to-indigo-600' : 'bg-gray-200'
                    }`}
                  />
                )}
              </React.Fragment>
            );
          })}
        </div>

        {/* Card */}
        <div className="bg-white rounded-3xl shadow-xl shadow-gray-200/50 p-8 md:p-10">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl mb-6 flex items-center gap-3">
              <svg className="w-5 h-5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
              {error}
            </div>
          )}

          {/* Step 1: Topic Selection */}
          {step === 'topic' && (
            <div className="space-y-8">
              <div className="text-center">
                <div className="w-16 h-16 bg-gradient-to-br from-blue-100 to-indigo-100 rounded-2xl flex items-center justify-center mx-auto mb-6">
                  <span className="text-3xl">🎯</span>
                </div>
                <h1 className="text-2xl md:text-3xl font-bold text-gray-900 mb-2">
                  What do you want to learn?
                </h1>
                <p className="text-gray-600">
                  Enter any topic and we'll create a personalized learning path
                </p>
              </div>

              <div>
                <input
                  type="text"
                  value={topic}
                  onChange={(e) => setTopic(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleTopicSubmit()}
                  placeholder="e.g., Python Programming, Machine Learning, UX Design..."
                  className="w-full px-5 py-4 text-lg border-2 border-gray-200 rounded-2xl focus:ring-4 focus:ring-blue-100 focus:border-blue-500 transition-all duration-200 outline-none"
                  autoFocus
                />
              </div>

              <button
                onClick={handleTopicSubmit}
                disabled={!topic.trim()}
                className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 text-white py-4 px-6 rounded-2xl hover:shadow-lg hover:shadow-blue-500/25 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:shadow-none font-semibold text-lg flex items-center justify-center gap-2"
              >
                Continue
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                </svg>
              </button>
            </div>
          )}

          {/* Step 2: Preferences */}
          {step === 'commitment' && (
            <div className="space-y-8">
              <div className="text-center">
                <button
                  onClick={() => setStep('topic')}
                  className="text-gray-500 hover:text-gray-700 mb-4 inline-flex items-center gap-1 text-sm"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                  </svg>
                  Back
                </button>
                <h1 className="text-2xl md:text-3xl font-bold text-gray-900 mb-2">
                  Customize your path
                </h1>
                <p className="text-gray-600">
                  Learning <span className="font-semibold text-blue-600">{topic}</span>
                </p>
              </div>

              {/* Proficiency Level */}
              <div className="space-y-3">
                <label className="block text-sm font-semibold text-gray-700">Experience Level</label>
                <div className="grid grid-cols-3 gap-3">
                  {[
                    { value: 'beginner', label: 'Beginner', icon: '🌱' },
                    { value: 'intermediate', label: 'Intermediate', icon: '🌿' },
                    { value: 'advanced', label: 'Advanced', icon: '🌳' },
                  ].map((level) => (
                    <button
                      key={level.value}
                      onClick={() => setProficiencyLevel(level.value)}
                      className={`p-4 rounded-xl border-2 transition-all duration-200 ${
                        proficiencyLevel === level.value
                          ? 'border-blue-500 bg-blue-50 ring-4 ring-blue-100'
                          : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                      }`}
                    >
                      <div className="text-2xl mb-1">{level.icon}</div>
                      <div className={`text-sm font-medium ${proficiencyLevel === level.value ? 'text-blue-700' : 'text-gray-700'}`}>
                        {level.label}
                      </div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Commitment Level */}
              <div className="space-y-3">
                <label className="block text-sm font-semibold text-gray-700">Time Commitment</label>
                <div className="space-y-2">
                  {[
                    { value: 'light', label: 'Light', hours: '2-4 hrs/week', desc: 'Perfect for busy schedules' },
                    { value: 'moderate', label: 'Moderate', hours: '5-8 hrs/week', desc: 'Balanced learning pace' },
                    { value: 'intensive', label: 'Intensive', hours: '10+ hrs/week', desc: 'Fast-track your learning' },
                  ].map((level) => (
                    <button
                      key={level.value}
                      onClick={() => setCommitmentLevel(level.value)}
                      className={`w-full p-4 rounded-xl border-2 transition-all duration-200 text-left flex items-center justify-between ${
                        commitmentLevel === level.value
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                      }`}
                    >
                      <div>
                        <div className={`font-semibold ${commitmentLevel === level.value ? 'text-blue-700' : 'text-gray-900'}`}>
                          {level.label}
                        </div>
                        <div className="text-sm text-gray-500">{level.desc}</div>
                      </div>
                      <div className={`text-sm font-medium px-3 py-1 rounded-full ${
                        commitmentLevel === level.value ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-600'
                      }`}>
                        {level.hours}
                      </div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Date Selection */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Start Date</label>
                  <input
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    min={new Date().toISOString().split('T')[0]}
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-4 focus:ring-blue-100 focus:border-blue-500 transition-all duration-200 outline-none"
                  />
                </div>
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">End Date <span className="text-gray-400 font-normal">(optional)</span></label>
                  <input
                    type="date"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                    min={startDate || new Date().toISOString().split('T')[0]}
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-4 focus:ring-blue-100 focus:border-blue-500 transition-all duration-200 outline-none"
                  />
                </div>
              </div>

              <button
                onClick={handleCreateLearningPath}
                className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 text-white py-4 px-6 rounded-2xl hover:shadow-lg hover:shadow-blue-500/25 transition-all duration-300 font-semibold text-lg flex items-center justify-center gap-2"
              >
                Create My Learning Path
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </button>
            </div>
          )}

          {/* Step 3: Creating */}
          {step === 'creating' && (
            <div className="py-8">
              <div className="text-center mb-8">
                <div className="relative w-20 h-20 mx-auto mb-6">
                  <div className="absolute inset-0 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-full animate-ping opacity-20"></div>
                  <div className="relative w-20 h-20 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-full flex items-center justify-center">
                    <svg className="w-10 h-10 text-white animate-pulse" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                    </svg>
                  </div>
                </div>
                <h2 className="text-2xl font-bold text-gray-900 mb-2">
                  Creating Your Learning Path
                </h2>
                <p className="text-gray-600">
                  Our AI is building a personalized curriculum for <span className="font-semibold text-blue-600">{topic}</span>
                </p>
              </div>

              {/* Current Phase */}
              {currentPhase && (
                <div className="flex justify-center mb-6">
                  <span className="inline-flex items-center gap-2 px-4 py-2 bg-blue-100 text-blue-700 rounded-full text-sm font-medium">
                    <span className="w-2 h-2 bg-blue-600 rounded-full animate-pulse"></span>
                    {phaseLabels[currentPhase] || currentPhase}
                  </span>
                </div>
              )}

              {/* Progress Messages */}
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {progressMessages.map((msg, idx) => (
                  <div
                    key={idx}
                    className="flex items-start gap-3 text-sm bg-gray-50 px-4 py-3 rounded-xl animate-fadeIn"
                  >
                    <span className="w-5 h-5 bg-green-100 text-green-600 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                      <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" />
                      </svg>
                    </span>
                    <span className="text-gray-700">{msg.message}</span>
                  </div>
                ))}
              </div>

              {progressMessages.length === 0 && (
                <div className="flex items-center justify-center gap-3 text-gray-500">
                  <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                  <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                  <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Onboarding;
