/**
 * Onboarding Page - Create Learning Path
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { assessments } from '../api/client';

interface Question {
  question: string;
  type?: string;
  options: Record<string, string> | string[];
  difficulty?: string;
  correct_answer?: string;
  explanation?: string;
}

interface ProgressMessage {
  message: string;
  phase: string;
  timestamp: string;
}

const Onboarding: React.FC = () => {
  const [step, setStep] = useState<'topic' | 'assessment' | 'commitment' | 'creating'>('topic');
  const [topic, setTopic] = useState('');
  const [questions, setQuestions] = useState<Question[]>([]);
  const [answers, setAnswers] = useState<Record<string, any>>({});
  const [commitmentLevel, setCommitmentLevel] = useState('moderate');
  const [proficiencyLevel, setProficiencyLevel] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [progressMessages, setProgressMessages] = useState<ProgressMessage[]>([]);
  const [currentPhase, setCurrentPhase] = useState('');

  const navigate = useNavigate();

  const handleTopicSubmit = async () => {
    if (!topic.trim()) return;

    setLoading(true);
    setError('');

    try {
      const response = await assessments.getProficiency(topic);
      setQuestions(response.data.questions);
      setStep('assessment');
    } catch (err: any) {
      setError('Failed to load assessment questions');
    } finally {
      setLoading(false);
    }
  };

  const handleAssessmentSubmit = () => {
    setStep('commitment');
  };

  const handleCreateLearningPath = async () => {
    setStep('creating');
    setLoading(true);
    setError('');
    setProgressMessages([]);
    setCurrentPhase('');

    // Convert answers to assessment responses format
    const assessmentResponses = questions.map((q, idx) => ({
      question: q.question,
      user_answer: answers[idx],
      is_correct: false, // Backend will evaluate
    }));

    // Build query params for SSE endpoint
    const params = new URLSearchParams({
      topic,
      commitment_level: commitmentLevel,
    });

    if (proficiencyLevel) {
      params.append('proficiency_level', proficiencyLevel);
    }
    if (startDate) {
      params.append('start_date', startDate);
    }
    if (endDate) {
      params.append('end_date', endDate);
    }
    if (assessmentResponses.length > 0) {
      params.append('assessment_responses', JSON.stringify(assessmentResponses));
    }

    // Connect to SSE endpoint
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

    eventSource.onerror = (err) => {
      console.error('EventSource error:', err);
      eventSource.close();
      setError('Connection lost. Please try again.');
      setLoading(false);
      setStep('commitment');
    };
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 py-12 px-4">
      <div className="max-w-3xl mx-auto">
        <div className="bg-white rounded-lg shadow-lg p-8">
          <h1 className="text-3xl font-bold text-gray-800 mb-2">
            Create Your Learning Path
          </h1>
          <p className="text-gray-600 mb-8">
            Let's personalize your learning journey
          </p>

          {/* Progress bar */}
          <div className="flex items-center mb-8">
            <div className={`flex-1 h-2 rounded ${step !== 'topic' ? 'bg-blue-600' : 'bg-gray-200'}`} />
            <div className={`flex-1 h-2 rounded mx-2 ${step === 'commitment' || step === 'creating' ? 'bg-blue-600' : 'bg-gray-200'}`} />
            <div className={`flex-1 h-2 rounded ${step === 'creating' ? 'bg-blue-600' : 'bg-gray-200'}`} />
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
              {error}
            </div>
          )}

          {/* Step 1: Topic Selection */}
          {step === 'topic' && (
            <div className="space-y-6">
              <div>
                <label className="block text-lg font-medium text-gray-700 mb-2">
                  What would you like to learn?
                </label>
                <input
                  type="text"
                  value={topic}
                  onChange={(e) => setTopic(e.target.value)}
                  placeholder="e.g., Python Programming, Machine Learning, Data Science"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-lg"
                />
              </div>

              <button
                onClick={handleTopicSubmit}
                disabled={!topic.trim() || loading}
                className="w-full bg-blue-600 text-white py-3 px-6 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-medium text-lg"
              >
                {loading ? 'Loading...' : 'Continue'}
              </button>
            </div>
          )}

          {/* Step 2: Proficiency Assessment */}
          {step === 'assessment' && (
            <div className="space-y-6">
              <div>
                <h2 className="text-xl font-semibold text-gray-800 mb-4">
                  Quick Assessment
                </h2>
                <p className="text-gray-600 mb-6">
                  Tell us about your experience level and answer a few questions
                </p>
              </div>

              {/* Proficiency Level Selection */}
              <div className="space-y-4 mb-8">
                <h3 className="font-medium text-gray-800">What's your experience level with {topic}?</h3>
                {[
                  { value: 'beginner', title: 'Beginner', description: 'New to this topic, little to no prior experience' },
                  { value: 'intermediate', title: 'Intermediate', description: 'Some experience, familiar with basic concepts' },
                  { value: 'advanced', title: 'Advanced', description: 'Significant experience, looking to deepen expertise' },
                ].map((level) => (
                  <label
                    key={level.value}
                    className={`block border-2 rounded-lg p-4 cursor-pointer transition-all ${proficiencyLevel === level.value
                      ? 'border-blue-600 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                      }`}
                  >
                    <input
                      type="radio"
                      name="proficiency"
                      value={level.value}
                      checked={proficiencyLevel === level.value}
                      onChange={(e) => setProficiencyLevel(e.target.value)}
                      className="sr-only"
                    />
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-semibold text-gray-800">{level.title}</p>
                        <p className="text-sm text-gray-600">{level.description}</p>
                      </div>
                      {proficiencyLevel === level.value && (
                        <div className="w-6 h-6 bg-blue-600 rounded-full flex items-center justify-center">
                          <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                            <path d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" />
                          </svg>
                        </div>
                      )}
                    </div>
                  </label>
                ))}
              </div>

              {/* Quiz Questions */}
              <h3 className="font-medium text-gray-800 mb-4">Answer these questions to help us calibrate your curriculum:</h3>

              {questions.map((question, idx) => (
                <div key={idx} className="border border-gray-200 rounded-lg p-4">
                  <p className="font-medium text-gray-800 mb-3">
                    {idx + 1}. {question.question}
                  </p>
                  <div className="space-y-2">
                    {Array.isArray(question.options) ? (
                      question.options.map((option, optIdx) => (
                        <label key={optIdx} className="flex items-center space-x-3 cursor-pointer">
                          <input
                            type="radio"
                            name={`question-${idx}`}
                            value={option}
                            checked={answers[idx] === option}
                            onChange={(e) => setAnswers({ ...answers, [idx]: e.target.value })}
                            className="w-4 h-4 text-blue-600"
                          />
                          <span className="text-gray-700">{option}</span>
                        </label>
                      ))
                    ) : (
                      Object.entries(question.options).map(([key, value]) => (
                        <label key={key} className="flex items-center space-x-3 cursor-pointer">
                          <input
                            type="radio"
                            name={`question-${idx}`}
                            value={key}
                            checked={answers[idx] === key}
                            onChange={(e) => setAnswers({ ...answers, [idx]: e.target.value })}
                            className="w-4 h-4 text-blue-600"
                          />
                          <span className="text-gray-700">{value}</span>
                        </label>
                      ))
                    )}
                  </div>
                </div>
              ))}

              <button
                onClick={handleAssessmentSubmit}
                disabled={Object.keys(answers).length < questions.length || !proficiencyLevel}
                className="w-full bg-blue-600 text-white py-3 px-6 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-medium text-lg"
              >
                Continue
              </button>
            </div>
          )}

          {/* Step 3: Commitment Level & Schedule */}
          {step === 'commitment' && (
            <div className="space-y-6">
              <div>
                <h2 className="text-xl font-semibold text-gray-800 mb-4">
                  Schedule & Commitment
                </h2>
                <p className="text-gray-600 mb-6">
                  Customize your learning schedule
                </p>
              </div>

              {/* Date Selection */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Start Date
                  </label>
                  <input
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    min={new Date().toISOString().split('T')[0]}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    End Date (Optional)
                  </label>
                  <input
                    type="date"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                    min={startDate || new Date().toISOString().split('T')[0]}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Leave blank for open-ended learning
                  </p>
                </div>
              </div>

              <div className="space-y-4">
                <h3 className="font-medium text-gray-800">Commitment Level</h3>
                {[
                  { value: 'light', title: 'Light', hours: '2-4 hours/week', sessions: '15-30 min sessions' },
                  { value: 'moderate', title: 'Moderate', hours: '5-8 hours/week', sessions: '30-45 min sessions' },
                  { value: 'intensive', title: 'Intensive', hours: '10+ hours/week', sessions: '45-90 min sessions' },
                ].map((level) => (
                  <label
                    key={level.value}
                    className={`block border-2 rounded-lg p-4 cursor-pointer transition-all ${commitmentLevel === level.value
                      ? 'border-blue-600 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                      }`}
                  >
                    <input
                      type="radio"
                      name="commitment"
                      value={level.value}
                      checked={commitmentLevel === level.value}
                      onChange={(e) => setCommitmentLevel(e.target.value)}
                      className="sr-only"
                    />
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-semibold text-gray-800">{level.title}</p>
                        <p className="text-sm text-gray-600">{level.hours}</p>
                        <p className="text-sm text-gray-500">{level.sessions}</p>
                      </div>
                      {commitmentLevel === level.value && (
                        <div className="w-6 h-6 bg-blue-600 rounded-full flex items-center justify-center">
                          <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                            <path d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" />
                          </svg>
                        </div>
                      )}
                    </div>
                  </label>
                ))}
              </div>

              <button
                onClick={handleCreateLearningPath}
                className="w-full bg-blue-600 text-white py-3 px-6 rounded-lg hover:bg-blue-700 transition-colors font-medium text-lg"
              >
                Create My Learning Path
              </button>
            </div>
          )}

          {/* Step 4: Creating */}
          {step === 'creating' && (
            <div className="py-8">
              <div className="flex items-center justify-center mb-6">
                <div className="animate-spin rounded-full h-12 w-12 border-b-4 border-blue-600"></div>
              </div>
              <h2 className="text-xl font-semibold text-gray-800 mb-2 text-center">
                Creating Your Learning Path...
              </h2>

              {/* Current Phase Indicator */}
              {currentPhase && (
                <div className="text-center mb-4">
                  <span className="inline-block px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm font-medium capitalize">
                    {currentPhase.replace('_', ' ')}
                  </span>
                </div>
              )}

              {/* Progress Messages */}
              <div className="mt-6 max-h-64 overflow-y-auto space-y-2">
                {progressMessages.map((msg, idx) => (
                  <div
                    key={idx}
                    className="flex items-start space-x-2 text-sm text-gray-700 bg-gray-50 px-4 py-2 rounded-lg animate-fadeIn"
                  >
                    <span className="text-green-500 mt-0.5 flex-shrink-0">
                      <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" />
                      </svg>
                    </span>
                    <span>{msg.message}</span>
                  </div>
                ))}
              </div>

              {progressMessages.length === 0 && (
                <p className="text-gray-600 text-center mt-4">
                  Our AI agents are analyzing your needs and building a personalized curriculum...
                </p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Onboarding;
