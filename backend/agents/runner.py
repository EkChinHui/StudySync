"""StudySync Learning Path Runner.

Provides two execution modes:
1. Direct tool calling (fast, deterministic) - Default for API use
2. Full ADK agent conversation (flexible, LLM-driven) - For complex scenarios

The direct mode calls tool functions sequentially for predictable behavior,
while the agent mode uses the orchestrator for flexible LLM-driven execution.
"""

from typing import Dict, List, Optional, Callable, Awaitable, Any
import asyncio

from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types

from backend.agents.agents import studysync_orchestrator
from backend.agents.tools import (
    assess_proficiency,
    determine_commitment_level,
    generate_curriculum,
    create_study_schedule,
    generate_module_quiz,
    find_session_resources,
)

# Type for progress callback: async def callback(phase: str, message: str, data: dict = None)
ProgressCallback = Callable[[str, str, Optional[Dict[str, Any]]], Awaitable[None]]


class LearningPathRunner:
    """Runner for creating learning paths using StudySync agents.

    Provides two execution modes:
    - create_learning_path(): Direct tool calling for fast, deterministic results
    - create_learning_path_with_agents(): Full ADK agent conversation for flexibility
    """

    def __init__(self):
        """Initialize the runner with session service."""
        self.session_service = InMemorySessionService()

    async def create_learning_path(
        self,
        topic: str,
        assessment_responses: Optional[List[Dict]] = None,
        calendar_credentials: Optional[Dict] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        commitment_level: Optional[str] = None,
        proficiency_level: Optional[str] = None,
        progress_callback: Optional[ProgressCallback] = None
    ) -> Dict:
        """Create a learning path using direct tool execution.

        This method calls tools directly for predictable, fast execution.
        Use this for API endpoints where deterministic behavior is needed.

        Args:
            topic: The learning topic (e.g., "Python programming")
            assessment_responses: Optional list of proficiency assessment responses
            calendar_credentials: Optional Google Calendar OAuth credentials
            start_date: Optional start date in ISO format (YYYY-MM-DD)
            end_date: Optional end date in ISO format (YYYY-MM-DD)
            commitment_level: Optional commitment level ("light", "moderate", "intensive")
            proficiency_level: Optional proficiency level ("beginner", "intermediate", "advanced")
            progress_callback: Optional async callback for progress updates

        Returns:
            Complete learning path dictionary with:
            - topic: str
            - user_profile: dict with proficiency and commitment info
            - curriculum: dict with modules and subtopics
            - schedule: list of session dicts
            - assessments: list of quiz dicts
            - status: "active"
            - progress: dict with completion tracking
        """
        print(f"[LearningPathRunner] Creating learning path for: {topic}")

        # Step 1: Profile user
        if progress_callback:
            await progress_callback("profiling", "Analyzing your proficiency level...")

        # Use provided levels or assess
        if proficiency_level and proficiency_level in ["beginner", "intermediate", "advanced"]:
            assessed_level = proficiency_level
            print(f"[LearningPathRunner] Using provided proficiency: {assessed_level}")
        else:
            profile_result = assess_proficiency(topic, assessment_responses)
            assessed_level = profile_result["proficiency_level"]
            print(f"[LearningPathRunner] Assessed proficiency: {assessed_level}")

        # Determine commitment
        if commitment_level and commitment_level in ["light", "moderate", "intensive"]:
            final_commitment = commitment_level
        else:
            commitment_result = determine_commitment_level(user_preference="moderate")
            final_commitment = commitment_result["commitment_level"]

        user_profile = {
            "topic": topic,
            "proficiency_level": assessed_level,
            "commitment_level": final_commitment,
            "preferences": {
                "session_duration": 30 if final_commitment == "light" else (45 if final_commitment == "moderate" else 60)
            }
        }

        if progress_callback:
            await progress_callback(
                "profiling",
                f"Profile complete: {assessed_level.capitalize()} level, {final_commitment} commitment"
            )

        # Step 2: Generate curriculum
        if progress_callback:
            await progress_callback("curriculum", f"Generating curriculum for {topic}...")

        # Calculate duration if dates provided
        duration_weeks = None
        if start_date and end_date:
            try:
                from datetime import datetime
                start = datetime.fromisoformat(start_date)
                end = datetime.fromisoformat(end_date)
                days = (end - start).days
                if days > 0:
                    duration_weeks = max(1, round(days / 7, 1))
            except Exception:
                pass

        curriculum = generate_curriculum(
            topic=topic,
            proficiency_level=assessed_level,
            commitment_level=final_commitment,
            duration_weeks=duration_weeks
        )

        num_modules = len(curriculum.get("modules", []))
        print(f"[LearningPathRunner] Generated {num_modules} modules")

        if progress_callback:
            module_titles = [m.get("title", "") for m in curriculum.get("modules", [])[:3]]
            preview = ", ".join(module_titles)
            if num_modules > 3:
                preview += f"... ({num_modules} total)"
            await progress_callback("curriculum", f"Curriculum ready: {preview}")

        # Step 3: Create schedule
        if progress_callback:
            await progress_callback("scheduling", "Creating your study schedule...")

        schedule_result = create_study_schedule(
            curriculum=curriculum,
            commitment_level=final_commitment,
            start_date=start_date,
            end_date=end_date
        )
        schedule = schedule_result.get("sessions", [])

        print(f"[LearningPathRunner] Created {len(schedule)} sessions")

        if progress_callback:
            await progress_callback("scheduling", f"Schedule created with {len(schedule)} sessions")

        # Step 4: Generate assessments (parallel with resources in real implementation)
        if progress_callback:
            await progress_callback("assessments", f"Generating quizzes for {num_modules} modules...")

        assessments = []
        for i, module in enumerate(curriculum.get("modules", [])):
            # Extract subtopic names
            subtopics = module.get("subtopics", [])
            subtopic_names = []
            for s in subtopics:
                if isinstance(s, dict):
                    subtopic_names.append(s.get("title", ""))
                else:
                    subtopic_names.append(str(s))

            quiz = generate_module_quiz(
                module_id=module.get("module_id", f"m{i+1}"),
                module_title=module.get("title", ""),
                subtopics=subtopic_names,
                proficiency_level=assessed_level
            )
            assessments.append(quiz)

            if progress_callback:
                await progress_callback(
                    "assessments",
                    f"Quiz ready for {module.get('title', '')} ({i+1}/{num_modules})",
                    {"current": i + 1, "total": num_modules}
                )

        print(f"[LearningPathRunner] Generated {len(assessments)} quizzes")

        # Step 5: Find resources for each session
        if progress_callback:
            await progress_callback("resources", f"Finding resources for {len(schedule)} sessions...")

        total_resources = 0
        for i, session in enumerate(schedule):
            session_topic = session.get("session_topic", session.get("module_title", ""))

            if progress_callback:
                await progress_callback(
                    "resources",
                    f"Finding resources for {session_topic}...",
                    {"current": i + 1, "total": len(schedule)}
                )

            resources = find_session_resources(
                main_topic=topic,
                session_topic=session_topic
            )

            # Combine videos and articles into session resources
            session["resources"] = resources.get("videos", []) + resources.get("articles", [])
            total_resources += len(session["resources"])

        print(f"[LearningPathRunner] Found {total_resources} total resources")

        if progress_callback:
            await progress_callback("resources", f"Found {total_resources} resources for all sessions")

        # Step 6: Compile final learning path
        if progress_callback:
            await progress_callback("complete", "Learning path created successfully!")

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
                "total_modules": num_modules,
                "total_sessions": len(schedule)
            }
        }

        print(f"[LearningPathRunner] Learning path complete!")
        return learning_path

    async def create_learning_path_with_agents(
        self,
        topic: str,
        assessment_responses: Optional[List[Dict]] = None,
        calendar_credentials: Optional[Dict] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        commitment_level: Optional[str] = None,
        proficiency_level: Optional[str] = None,
        progress_callback: Optional[ProgressCallback] = None
    ) -> Dict:
        """Create a learning path using full ADK agent conversation.

        This method uses the orchestrator agent for flexible, LLM-driven execution.
        Use this when you need adaptive behavior or complex decision making.

        Args:
            topic: The learning topic
            assessment_responses: Optional proficiency assessment responses
            calendar_credentials: Optional Google Calendar credentials
            start_date: Optional start date
            end_date: Optional end date
            commitment_level: Optional commitment level
            proficiency_level: Optional proficiency level
            progress_callback: Optional progress callback (limited support in agent mode)

        Returns:
            Complete learning path dictionary (structure may vary based on agent output)
        """
        print(f"[LearningPathRunner] Creating learning path with agents for: {topic}")

        # Build initial state
        initial_state = {
            "topic": topic,
            "assessment_responses": assessment_responses or [],
            "calendar_credentials": calendar_credentials,
            "start_date": start_date,
            "end_date": end_date,
            "commitment_level": commitment_level,
            "proficiency_level": proficiency_level,
        }

        # Create session
        session = await self.session_service.create_session(
            app_name="studysync",
            user_id="user",
            state=initial_state
        )

        # Create runner
        runner = Runner(
            agent=studysync_orchestrator,
            app_name="studysync",
            session_service=self.session_service
        )

        # Create message
        message = types.Content(
            role="user",
            parts=[types.Part(text=f"Create a complete learning path for: {topic}")]
        )

        # Run the orchestrator
        final_response = None
        async for event in runner.run_async(
            user_id="user",
            session_id=session.id,
            new_message=message
        ):
            # Log progress
            if event.content:
                try:
                    text_parts = [p.text for p in event.content.parts if hasattr(p, 'text') and p.text]
                    if text_parts and progress_callback:
                        phase = "progress"
                        if hasattr(event, 'author'):
                            author = event.author.lower()
                            if "profiler" in author:
                                phase = "profiling"
                            elif "curriculum" in author:
                                phase = "curriculum"
                            elif "scheduler" in author:
                                phase = "scheduling"
                            elif "resource" in author:
                                phase = "resources"
                            elif "assessment" in author:
                                phase = "assessments"
                        await progress_callback(phase, text_parts[0])
                except Exception as e:
                    print(f"[LearningPathRunner] Event processing error: {e}")

            if hasattr(event, 'is_final_response') and event.is_final_response():
                final_response = event

        # Extract learning path from session state
        learning_path = session.state.get("learning_path", {})

        if not learning_path:
            print("[LearningPathRunner] WARNING: No learning path in session state, returning empty")
            learning_path = {
                "topic": topic,
                "user_profile": {},
                "curriculum": {},
                "schedule": [],
                "assessments": [],
                "status": "incomplete",
                "progress": {}
            }

        return learning_path

    async def generate_proficiency_assessment(self, topic: str) -> List[Dict]:
        """Generate proficiency assessment questions for a topic.

        Args:
            topic: The learning topic to assess

        Returns:
            List of assessment question dicts
        """
        from backend.agents.tools import generate_proficiency_assessment
        result = generate_proficiency_assessment(topic)
        return result.get("questions", [])

    async def evaluate_quiz(self, quiz: Dict, user_responses: Dict[str, str]) -> Dict:
        """Evaluate a quiz submission.

        Args:
            quiz: Quiz dict with questions
            user_responses: Dict mapping question index to answer letter

        Returns:
            Evaluation results with score, feedback, and knowledge gaps
        """
        from backend.agents.tools import evaluate_quiz_responses
        return evaluate_quiz_responses(quiz, user_responses)
