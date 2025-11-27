/**
 * TypeScript types for StudySync
 */

export interface User {
  id: string;
  email: string;
}

export interface LearningPath {
  id: string;
  topic: string;
  proficiency_level: string;
  commitment_level: string;
  status: string;
  created_at: string;
}

export interface Subtopic {
  title: string;
  description: string;
  estimated_minutes: number;
}

export interface Module {
  module_id: string;
  title: string;
  duration_hours: number;
  learning_objectives: string[];
  subtopics: Subtopic[] | string[];
  prerequisites: string[];
  resources: Resource[];
}

export interface Resource {
  type: string;
  title: string;
  url?: string;
  content?: string;
  quality_score: number;
  is_generated: boolean;
}

export interface StudySession {
  id: string;
  module_id: string;
  module_title: string;
  scheduled_time: string;
  duration_minutes: number;
  completed: boolean;
  resources: Resource[];
}

export interface Question {
  question: string;
  type?: string;
  options: Record<string, string> | string[];
  difficulty?: string;
  correct_answer?: string;
  explanation?: string;
}

export interface Assessment {
  id: string;
  module_id: string;
  assessment_type: string;
  questions: Question[];
  completed: boolean;
  score?: number;
}

export interface Dashboard {
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
