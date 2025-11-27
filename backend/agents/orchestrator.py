"""Orchestrator Agent - Coordinates all other agents."""

from typing import Dict, List, Optional
from backend.agents.user_profiler import UserProfilerAgent
from backend.agents.curriculum_agent import CurriculumAgent
from backend.agents.scheduler_agent import SchedulerAgent
from backend.agents.assessment_agent import AssessmentAgent


class OrchestratorAgent:
    """Main orchestrator that coordinates all agents to create learning paths."""

    def __init__(self):
        """Initialize all sub-agents."""
        self.user_profiler = UserProfilerAgent()
        self.curriculum_agent = CurriculumAgent()
        self.scheduler_agent = SchedulerAgent()
        self.assessment_agent = AssessmentAgent()

    async def create_learning_path(
        self,
        topic: str,
        calendar_credentials: Optional[Dict] = None,
        assessment_responses: Optional[List[Dict]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict:
        """
        Orchestrate the creation of a complete learning path.

        This is the main workflow that coordinates all agents:
        1. User Profiler: Assess proficiency and availability
        2. Curriculum Agent: Generate curriculum and find resources
        3. Scheduler Agent: Create optimal study schedule
        4. Assessment Agent: Generate quizzes for modules

        Args:
            topic: Learning topic
            calendar_credentials: Optional Google Calendar OAuth credentials
            assessment_responses: Optional proficiency assessment responses
            start_date: Optional start date for the schedule
            end_date: Optional end date for the schedule

        Returns:
            Complete learning path with curriculum, schedule, and assessments
        """
        try:
            # Step 1: User Profiling
            print(f"[Orchestrator] Starting user profiling for topic: {topic}")
            user_profile = await self.user_profiler.run(
                topic=topic,
                calendar_credentials=calendar_credentials,
                assessment_responses=assessment_responses
            )
            print(f"[Orchestrator] User profile: {user_profile['proficiency_level']} - {user_profile['commitment_level']}")

            # Step 2: Curriculum Generation
            print("[Orchestrator] Generating curriculum...")
            
            # Calculate duration in weeks if dates are provided
            duration_weeks = None
            if start_date and end_date:
                from datetime import datetime
                start = datetime.fromisoformat(start_date)
                end = datetime.fromisoformat(end_date)
                days = (end - start).days
                if days > 0:
                    duration_weeks = max(1, round(days / 7, 1))
                    print(f"[Orchestrator] Calculated duration: {duration_weeks} weeks")

            curriculum = await self.curriculum_agent.run(
                topic=topic,
                user_profile=user_profile,
                duration_weeks=duration_weeks
            )
            print(f"[Orchestrator] Curriculum generated with {len(curriculum.get('modules', []))} modules")

            # Step 3: Schedule Generation
            print("[Orchestrator] Creating study schedule...")
            schedule = await self.scheduler_agent.run(
                curriculum=curriculum,
                user_profile=user_profile,
                calendar_credentials=calendar_credentials,
                start_date=start_date,
                end_date=end_date
            )
            print(f"[Orchestrator] Schedule created with {len(schedule)} sessions")

            # Step 4: Generate assessments for each module
            print("[Orchestrator] Generating module assessments...")
            assessments = []
            for module in curriculum.get("modules", []):
                quiz = await self.assessment_agent.generate_module_quiz(module, num_questions=5)
                assessments.append(quiz)
            print(f"[Orchestrator] Generated {len(assessments)} assessments")

            # Compile complete learning path
            learning_path = {
                "topic": topic,
                "user_profile": user_profile,
                "curriculum": curriculum,
                "schedule": schedule,
                "assessments": assessments,
                "status": "active",
                "progress": {
                    "modules_completed": 0,
                    "sessions_completed": 0,
                    "total_modules": len(curriculum.get("modules", [])),
                    "total_sessions": len(schedule)
                }
            }

            print("[Orchestrator] Learning path created successfully!")
            return learning_path

        except Exception as e:
            print(f"[Orchestrator] Error creating learning path: {e}")
            raise

    async def generate_proficiency_assessment(self, topic: str) -> List[Dict]:
        """Generate proficiency assessment questions for a topic."""
        return self.user_profiler.generate_proficiency_assessment(topic)

    async def evaluate_quiz(self, quiz: Dict, user_responses: Dict[str, str]) -> Dict:
        """Evaluate a quiz submission."""
        evaluation = self.assessment_agent.evaluate_quiz(quiz, user_responses)
        gaps = self.assessment_agent.identify_knowledge_gaps(evaluation)
        evaluation["knowledge_gaps"] = gaps
        return evaluation

    async def regenerate_schedule(
        self,
        curriculum: Dict,
        user_profile: Dict,
        calendar_credentials: Optional[Dict] = None
    ) -> List[Dict]:
        """Regenerate schedule (e.g., after calendar conflicts)."""
        return await self.scheduler_agent.run(
            curriculum=curriculum,
            user_profile=user_profile,
            calendar_credentials=calendar_credentials
        )
