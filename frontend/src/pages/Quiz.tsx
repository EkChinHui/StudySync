/**
 * Quiz Page
 */

import React, { useEffect, useState } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { assessments } from '../api/client';
import { useToast } from '../components/Toast';

interface Question {
  id: string;
  question: string;
  options: Record<string, string> | string[];
}

interface QuizData {
  assessment_id: string;
  module_title: string;
  questions: Question[];
}

interface QuestionResult {
  question_id: string;
  question: string;
  user_answer: string;
  correct_answer: string;
  is_correct: boolean;
  explanation: string;
}

interface QuizResult {
  score: number;
  correct_count: number;
  total_questions: number;
  passed: boolean;
  results: QuestionResult[];
  knowledge_gaps?: string[];
}

const Quiz: React.FC = () => {
  const { moduleId } = useParams<{ moduleId: string }>();
  const [searchParams] = useSearchParams();
  const learningPathId = searchParams.get('learning_path_id') || searchParams.get('learningPathId') || '';
  const isReviewMode = searchParams.get('review') === 'true';
  const navigate = useNavigate();
  const { showToast } = useToast();

  const [quiz, setQuiz] = useState<QuizData | null>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<QuizResult | null>(null);

  useEffect(() => {
    if (isReviewMode) {
      loadQuizResults();
    } else {
      loadQuiz();
    }
  }, [moduleId, learningPathId, isReviewMode]);

  const loadQuiz = async () => {
    try {
      const response = await assessments.getQuiz(moduleId!, learningPathId);
      setQuiz(response.data);
    } catch (err) {
      showToast('Failed to load quiz', 'error');
    } finally {
      setLoading(false);
    }
  };

  const loadQuizResults = async () => {
    try {
      const response = await assessments.getQuizResults(moduleId!, learningPathId);
      setQuiz({
        assessment_id: response.data.assessment_id,
        module_title: response.data.module_title,
        questions: response.data.questions,
      });
      setResult(response.data);
    } catch (err) {
      showToast('Failed to load quiz results', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleAnswerChange = (questionId: string, answer: string) => {
    setAnswers((prev) => ({ ...prev, [questionId]: answer }));
  };

  const handleSubmit = async () => {
    if (!quiz) return;

    const unanswered = quiz.questions.filter((q, idx) => !answers[q.id || `q${idx}`]);
    if (unanswered.length > 0) {
      showToast(`Please answer all questions. ${unanswered.length} remaining.`, 'info');
      return;
    }

    setSubmitting(true);
    try {
      const response = await assessments.submitQuiz(quiz.assessment_id, answers);
      setResult(response.data);
    } catch (err) {
      showToast('Failed to submit quiz', 'error');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-blue-600"></div>
      </div>
    );
  }

  if (!quiz) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-red-600">Quiz not found</div>
      </div>
    );
  }

  if (result) {
    const getOptionText = (questionIdx: number, answerKey: string): string => {
      if (!quiz) return answerKey;
      const question = quiz.questions[questionIdx];
      if (!question) return answerKey;
      if (Array.isArray(question.options)) {
        return question.options[parseInt(answerKey)] || answerKey;
      }
      return question.options[answerKey] || answerKey;
    };

    return (
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-3xl mx-auto px-4 py-8">
          {/* Score Summary */}
          <div className="bg-white rounded-lg shadow-lg p-8 text-center mb-8">
            {isReviewMode ? (
              <>
                <div className="text-6xl mb-4 text-blue-500">📋</div>
                <h1 className="text-3xl font-bold text-gray-900 mb-2">Quiz Review</h1>
                <p className="text-lg text-gray-600 mb-4">{quiz?.module_title}</p>
              </>
            ) : (
              <>
                <div className={`text-6xl mb-4 ${result.passed ? 'text-green-500' : 'text-red-500'}`}>
                  {result.passed ? '🎉' : '📚'}
                </div>
                <h1 className="text-3xl font-bold text-gray-900 mb-4">
                  {result.passed ? 'Congratulations!' : 'Keep Learning!'}
                </h1>
              </>
            )}
            <p className="text-2xl text-gray-700 mb-4">
              Score: {result.correct_count} / {result.total_questions}
            </p>
            {!isReviewMode && (
              <p className="text-gray-600 mb-6">
                {result.passed
                  ? 'Great job! You have demonstrated understanding of this module.'
                  : 'Review the material and try again to improve your understanding.'}
              </p>
            )}
            <button
              onClick={() => navigate(-1)}
              className="bg-blue-600 text-white py-3 px-8 rounded-lg hover:bg-blue-700 transition-colors font-medium"
            >
              Back to Dashboard
            </button>
          </div>

          {/* Question Review */}
          <div className="bg-white rounded-lg shadow-lg p-8">
            <h2 className="text-xl font-bold text-gray-900 mb-6">Review Your Answers</h2>
            <div className="space-y-6">
              {result.results.map((r, idx) => (
                <div
                  key={r.question_id}
                  className={`border rounded-lg p-4 ${
                    r.is_correct ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <span className={`text-xl ${r.is_correct ? 'text-green-600' : 'text-red-600'}`}>
                      {r.is_correct ? '✓' : '✗'}
                    </span>
                    <div className="flex-1">
                      <p className="font-medium text-gray-900 mb-2">
                        {idx + 1}. {r.question}
                      </p>
                      <p className={`text-sm ${r.is_correct ? 'text-green-700' : 'text-red-700'}`}>
                        Your answer: <strong>{r.user_answer}. {getOptionText(idx, r.user_answer)}</strong>
                      </p>
                      {!r.is_correct && (
                        <p className="text-sm text-green-700 mt-1">
                          Correct answer: <strong>{r.correct_answer}. {getOptionText(idx, r.correct_answer)}</strong>
                        </p>
                      )}
                      {r.explanation && (
                        <p className="text-sm text-gray-600 mt-2 italic">{r.explanation}</p>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-3xl mx-auto px-4 py-8">
        <button
          onClick={() => navigate(-1)}
          className="text-blue-600 hover:text-blue-700 mb-6 flex items-center"
        >
          ← Back to Dashboard
        </button>

        <div className="bg-white rounded-lg shadow-lg p-8">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">{quiz.module_title}</h1>
          <p className="text-gray-600 mb-8">
            Answer all {quiz.questions.length} questions to complete this quiz.
          </p>

          <div className="space-y-8">
            {quiz.questions.map((question, idx) => {
              const questionId = question.id || `q${idx}`;
              return (
                <div key={questionId} className="border-b border-gray-200 pb-6 last:border-0">
                  <h3 className="text-lg font-medium text-gray-900 mb-4">
                    {idx + 1}. {question.question}
                  </h3>
                  <div className="space-y-2">
                    {(Array.isArray(question.options)
                      ? question.options.map((opt, i) => ({ key: String(i), value: opt }))
                      : Object.entries(question.options).map(([key, value]) => ({ key, value }))
                    ).map(({ key, value }) => (
                      <label
                        key={key}
                        className={`flex items-center p-3 rounded-lg border cursor-pointer transition-colors ${
                          answers[questionId] === key
                            ? 'border-blue-500 bg-blue-50'
                            : 'border-gray-200 hover:bg-gray-50'
                        }`}
                      >
                        <input
                          type="radio"
                          name={questionId}
                          value={key}
                          checked={answers[questionId] === key}
                          onChange={() => handleAnswerChange(questionId, key)}
                          className="mr-3"
                        />
                        <span className="text-gray-700">
                          {!Array.isArray(question.options) && <strong>{key}. </strong>}
                          {value}
                        </span>
                      </label>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>

          <button
            onClick={handleSubmit}
            disabled={submitting}
            className="w-full mt-8 bg-blue-600 text-white py-3 px-6 rounded-lg hover:bg-blue-700 transition-colors font-medium text-lg disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {submitting ? 'Submitting...' : 'Submit Quiz'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default Quiz;
