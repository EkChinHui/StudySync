"""Assessment Agent - ADK implementation for quiz generation and evaluation."""

from typing import AsyncGenerator, Dict, List
from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.genai import types
from pydantic import Field

from backend.services.llm_service import LLMService


class AssessmentAgent(BaseAgent):
    """
    Agent responsible for generating quizzes and evaluating responses.

    Reads from session state:
        - curriculum: Curriculum with modules

    Writes to session state:
        - assessments: List of quizzes for each module
    """

    name: str = "assessment_agent"
    description: str = "Generates quizzes for each module and evaluates user responses"

    # Services
    llm_service: LLMService = Field(default_factory=LLMService)

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        """Execute assessment generation for all modules."""
        print(f"[{self.name}] Starting assessment generation...")

        # Read curriculum from session state
        curriculum = ctx.session.state.get("curriculum", {})
        modules = curriculum.get("modules", [])
        progress_callback = ctx.session.state.get("progress_callback")

        # Emit initial progress
        if progress_callback:
            await progress_callback("assessments", f"Generating quizzes for {len(modules)} modules...")

        # Generate quizzes for all modules
        assessments = []
        total_modules = len(modules)
        for i, module in enumerate(modules):
            module_title = module.get("title", f"Module {i+1}")

            # Emit progress before generating
            if progress_callback:
                await progress_callback(
                    "assessments",
                    f"Generating quiz for {module_title}...",
                    {"current": i + 1, "total": total_modules}
                )

            quiz = await self.generate_module_quiz(module, num_questions=5)
            assessments.append(quiz)
            print(f"[{self.name}] Generated quiz for: {module_title}")

            # Emit progress after generating
            if progress_callback:
                await progress_callback(
                    "assessments",
                    f"Quiz ready for {module_title} ({i+1}/{total_modules})",
                    {"current": i + 1, "total": total_modules}
                )

            # Yield intermediate event
            yield Event(
                author=self.name,
                content=types.Content(
                    role="model",
                    parts=[types.Part(text=f"Quiz ready for {module_title}")]
                )
            )

        # Store in session state
        ctx.session.state["assessments"] = assessments

        print(f"[{self.name}] Generated {len(assessments)} assessments")

        # Emit completion
        if progress_callback:
            await progress_callback(
                "assessments",
                f"Assessment generation complete: {len(assessments)} quizzes ready"
            )

        # Yield completion event
        yield Event(
            author=self.name,
            content=types.Content(
                role="model",
                parts=[types.Part(text=f"Generated {len(assessments)} module assessments")]
            )
        )

    async def generate_module_quiz(self, module: Dict, num_questions: int = 5) -> Dict:
        """Generate a quiz for a specific module."""
        questions = self.llm_service.generate_quiz(
            module_title=module.get("title", ""),
            subtopics=module.get("subtopics", []),
            num_questions=num_questions
        )

        return {
            "module_id": module.get("module_id", ""),
            "module_title": module.get("title", ""),
            "assessment_type": "module_quiz",
            "questions": questions,
            "total_questions": len(questions)
        }

    def evaluate_quiz(self, quiz: Dict, user_responses: Dict[str, str]) -> Dict:
        """Evaluate user's quiz responses."""
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
            "passed": score >= 0.6,
            "results": results
        }

    def identify_knowledge_gaps(self, evaluation: Dict) -> List[str]:
        """Identify topics where user needs more practice."""
        gaps = []
        incorrect_results = [
            r for r in evaluation.get("results", [])
            if not r.get("is_correct", False)
        ]

        if incorrect_results:
            gaps.append("Review questions marked incorrect")

        if evaluation.get("score", 1.0) < 0.7:
            gaps.append("Consider reviewing the module materials")

        return gaps
