"""Assessment Agent - Generates and evaluates quizzes."""

from typing import Dict, List
from backend.services.llm_service import LLMService


class AssessmentAgent:
    """Agent responsible for generating assessments and evaluating responses."""

    def __init__(self):
        """Initialize the agent."""
        self.llm_service = LLMService()

    async def generate_module_quiz(self, module: Dict, num_questions: int = 5) -> Dict:
        """
        Generate a quiz for a module.

        Args:
            module: Module dictionary with title and subtopics
            num_questions: Number of questions to generate

        Returns:
            Quiz data with questions
        """
        questions = self.llm_service.generate_quiz(
            module_title=module.get("title", ""),
            subtopics=module.get("subtopics", []),
            num_questions=num_questions
        )

        quiz = {
            "module_id": module.get("module_id", ""),
            "module_title": module.get("title", ""),
            "assessment_type": "module_quiz",
            "questions": questions,
            "total_questions": len(questions)
        }

        return quiz

    def evaluate_quiz(self, quiz: Dict, user_responses: Dict[str, str]) -> Dict:
        """
        Evaluate user's quiz responses.

        Args:
            quiz: Quiz data with questions
            user_responses: Dict mapping question index to user's answer

        Returns:
            Evaluation results with score and feedback
        """
        correct_count = 0
        total_questions = len(quiz.get("questions", []))
        results = []

        for idx, question in enumerate(quiz.get("questions", [])):
            question_id = str(idx)
            user_answer = user_responses.get(question_id, "")
            correct_answer = question.get("correct_answer", "")

            is_correct = user_answer.upper() == correct_answer.upper()
            if is_correct:
                correct_count += 1

            results.append({
                "question_id": question_id,
                "question": question.get("question", ""),
                "user_answer": user_answer,
                "correct_answer": correct_answer,
                "is_correct": is_correct,
                "explanation": question.get("explanation", "")
            })

        score = correct_count / total_questions if total_questions > 0 else 0

        return {
            "score": score,
            "correct_count": correct_count,
            "total_questions": total_questions,
            "passed": score >= 0.6,  # 60% passing grade
            "results": results
        }

    def identify_knowledge_gaps(self, evaluation: Dict) -> List[str]:
        """
        Identify topics where user struggled.

        Args:
            evaluation: Evaluation results from evaluate_quiz

        Returns:
            List of topics to review
        """
        gaps = []
        incorrect_results = [r for r in evaluation.get("results", []) if not r["is_correct"]]

        if len(incorrect_results) > 0:
            gaps.append("Review questions marked incorrect")

        if evaluation.get("score", 1.0) < 0.7:
            gaps.append("Consider reviewing the module materials")

        return gaps
