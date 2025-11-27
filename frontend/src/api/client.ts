/**
 * API client for StudySync backend
 */

import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests (disabled for POC)
// apiClient.interceptors.request.use((config) => {
//   const token = localStorage.getItem('access_token');
//   if (token) {
//     config.headers.Authorization = `Bearer ${token}`;
//   }
//   return config;
// });

// API functions
export const auth = {
  register: (email: string, password: string) =>
    apiClient.post('/api/auth/register', { email, password }),

  login: (email: string, password: string) =>
    apiClient.post('/api/auth/login', { email, password }),

  connectCalendar: (accessToken: string, refreshToken: string) =>
    apiClient.post('/api/auth/calendar/connect', {
      access_token: accessToken,
      refresh_token: refreshToken,
    }),
};

export const learningPaths = {
  create: (topic: string, assessmentResponses?: any[], useCalendar = false, startDate?: string, endDate?: string) =>
    apiClient.post('/api/learning-paths', {
      topic,
      assessment_responses: assessmentResponses,
      use_calendar: useCalendar,
      start_date: startDate,
      end_date: endDate,
    }),

  getAll: () => apiClient.get('/api/learning-paths'),

  getById: (id: string) => apiClient.get(`/api/learning-paths/${id}`),

  getDashboard: (id: string) =>
    apiClient.get(`/api/learning-paths/${id}/dashboard`),

  getSessions: (id: string) =>
    apiClient.get(`/api/learning-paths/${id}/sessions`),
};

export const assessments = {
  getProficiency: (topic: string) =>
    apiClient.post('/api/assessments/proficiency', { topic }),

  getQuiz: (moduleId: string, learningPathId: string) =>
    apiClient.get(`/api/assessments/quiz/${moduleId}`, {
      params: { learning_path_id: learningPathId },
    }),

  submitQuiz: (assessmentId: string, responses: Record<string, string>) =>
    apiClient.post(`/api/assessments/quiz/${assessmentId}/submit`, {
      responses,
    }),
};

export const schedule = {
  downloadICS: (learningPathId: string) =>
    apiClient.get(`/api/schedule/${learningPathId}/ics`, {
      responseType: 'blob',
    }),

  getSession: (sessionId: string) =>
    apiClient.get(`/api/schedule/sessions/${sessionId}`),

  completeSession: (sessionId: string, notes = '') =>
    apiClient.post(`/api/schedule/sessions/${sessionId}/complete`, { notes }),
};

export default apiClient;
