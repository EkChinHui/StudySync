"""
StudySync Orchestrator - ADK-based workflow orchestration.

Uses Google ADK's workflow agents to coordinate the learning path creation:
1. Sequential: UserProfiler -> Curriculum -> Scheduler (dependencies between each)
2. Parallel: ResourceFinder || Assessment (both only need schedule)
"""

from typing import Dict, List, Optional, AsyncGenerator, Callable, Awaitable, Any
from google.adk.agents import BaseAgent, SequentialAgent, ParallelAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.adk.events import Event
from google.genai import types
from pydantic import Field

# Type for progress callback: async def callback(phase: str, message: str, data: dict = None)
ProgressCallback = Callable[[str, str, Optional[Dict[str, Any]]], Awaitable[None]]

from backend.agents.adk.user_profiler import UserProfilerAgent
from backend.agents.adk.curriculum import CurriculumAgent
from backend.agents.adk.scheduler import SchedulerAgent
from backend.agents.adk.resource_finder import ResourceFinderAgent
from backend.agents.adk.assessment import AssessmentAgent


class StudySyncOrchestrator(BaseAgent):
    """
    Main orchestrator that coordinates all agents to create learning paths.

    Workflow:
    1. UserProfiler: Assess user proficiency and commitment
    2. CurriculumAgent: Generate curriculum structure with topics
    3. SchedulerAgent: Create sessions with scheduled times for each topic
    4. ResourceFinderAgent || AssessmentAgent: Find resources per session + generate quizzes

    This ensures each session has UNIQUE resources specific to its topic.
    """

    name: str = "studysync_orchestrator"
    description: str = "Orchestrates the complete learning path creation workflow"

    # Sub-agents
    user_profiler: UserProfilerAgent = Field(default_factory=UserProfilerAgent)
    curriculum_agent: CurriculumAgent = Field(default_factory=CurriculumAgent)
    scheduler_agent: SchedulerAgent = Field(default_factory=SchedulerAgent)
    resource_finder: ResourceFinderAgent = Field(default_factory=ResourceFinderAgent)
    assessment_agent: AssessmentAgent = Field(default_factory=AssessmentAgent)

    # Workflow agents (built on init)
    _sequential_phase: Optional[SequentialAgent] = None
    _parallel_phase: Optional[ParallelAgent] = None

    # Store last result for retrieval (workaround for ADK session state not persisting)
    _last_learning_path: Optional[Dict] = None

    def model_post_init(self, __context) -> None:
        """Initialize workflow agents after model creation."""
        # Phase 1: Sequential execution (UserProfiler -> Curriculum -> Scheduler)
        # Each step depends on the previous
        self._sequential_phase = SequentialAgent(
            name="sequential_planning",
            description="Sequentially runs profiling, curriculum, and scheduling",
            sub_agents=[self.user_profiler, self.curriculum_agent, self.scheduler_agent]
        )

        # Phase 2: Parallel execution (ResourceFinder || Assessment)
        # Both only need the schedule - can run concurrently
        self._parallel_phase = ParallelAgent(
            name="parallel_resources_and_assessment",
            description="Concurrently finds resources and generates assessments",
            sub_agents=[self.resource_finder, self.assessment_agent]
        )

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        """
        Execute the complete learning path creation workflow.

        Flow:
        1. Sequential: UserProfiler -> Curriculum -> Scheduler
        2. Parallel: ResourceFinder || Assessment
        3. Compile final learning path
        """
        print(f"[{self.name}] Starting learning path creation...")

        # Phase 1: Sequential planning (profile -> curriculum -> schedule)
        print(f"[{self.name}] Phase 1: Sequential (Profile -> Curriculum -> Schedule)...")
        async for event in self._sequential_phase.run_async(ctx):
            yield event

        # Phase 2: Parallel resource finding and assessment generation
        print(f"[{self.name}] Phase 2: Parallel (Resources || Assessments)...")
        async for event in self._parallel_phase.run_async(ctx):
            yield event

        # Compile the complete learning path
        learning_path = self._compile_learning_path(ctx)
        ctx.session.state["learning_path"] = learning_path

        # Also store in instance for retrieval (workaround for ADK session state)
        self._last_learning_path = learning_path

        print(f"[{self.name}] Learning path creation complete!")

        yield Event(
            author=self.name,
            content=types.Content(
                role="model",
                parts=[types.Part(text="Learning path created successfully")]
            )
        )

    def _compile_learning_path(self, ctx: InvocationContext) -> Dict:
        """Compile all agent outputs into a complete learning path."""
        state = ctx.session.state

        return {
            "topic": state.get("topic", ""),
            "user_profile": state.get("user_profile", {}),
            "curriculum": state.get("curriculum", {}),
            "schedule": state.get("schedule", []),
            "assessments": state.get("assessments", []),
            "status": "active",
            "progress": {
                "modules_completed": 0,
                "sessions_completed": 0,
                "total_modules": len(state.get("curriculum", {}).get("modules", [])),
                "total_sessions": len(state.get("schedule", []))
            }
        }


class LearningPathRunner:
    """
    Runner for creating learning paths using the ADK orchestrator.

    This provides a simple interface to create learning paths,
    handling session management and event processing.
    """

    def __init__(self):
        """Initialize the runner with orchestrator and session service."""
        self.orchestrator = StudySyncOrchestrator()
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
        """
        Create a complete learning path.

        Args:
            topic: The learning topic
            assessment_responses: User's proficiency assessment responses
            calendar_credentials: Optional Google Calendar OAuth credentials
            start_date: Optional start date (ISO format)
            end_date: Optional end date (ISO format)
            commitment_level: Optional commitment level
            proficiency_level: Optional proficiency level
            progress_callback: Optional async callback for progress updates

        Returns:
            Complete learning path dictionary
        """
        # Build initial state
        initial_state = {
            "topic": topic,
            "assessment_responses": assessment_responses or [],
            "calendar_credentials": calendar_credentials,
            "start_date": start_date,
            "end_date": end_date,
            "commitment_level": commitment_level,
            "proficiency_level": proficiency_level,
            "progress_callback": progress_callback,  # Pass callback to agents via state
        }

        # Calculate duration if dates provided
        if start_date and end_date:
            from datetime import datetime
            try:
                start = datetime.fromisoformat(start_date)
                end = datetime.fromisoformat(end_date)
                days = (end - start).days
                if days > 0:
                    initial_state["duration_weeks"] = max(1, round(days / 7, 1))
            except Exception:
                pass

        # Create a new session via service
        session = await self.session_service.create_session(
            app_name="studysync",
            user_id="user",
            state=initial_state
        )

        # Create runner and execute
        runner = Runner(
            agent=self.orchestrator,
            app_name="studysync",
            session_service=self.session_service
        )

        # Run the orchestrator
        print(f"[LearningPathRunner] Creating learning path for: {topic}")

        # Create Content object for the message
        message = types.Content(
            role="user",
            parts=[types.Part(text=f"Create a learning path for: {topic}")]
        )

        async for event in runner.run_async(
            user_id="user",
            session_id=session.id,
            new_message=message
        ):
            # Process events and stream progress if callback provided
            if event.content and progress_callback:
                # Extract message from event content
                try:
                    text_parts = [p.text for p in event.content.parts if hasattr(p, 'text') and p.text]
                    if text_parts:
                        message_text = text_parts[0]
                        # Determine phase from author
                        phase = "progress"
                        if hasattr(event, 'author'):
                            if "profiler" in event.author.lower():
                                phase = "profiling"
                            elif "curriculum" in event.author.lower():
                                phase = "curriculum"
                            elif "scheduler" in event.author.lower():
                                phase = "scheduling"
                            elif "resource" in event.author.lower():
                                phase = "resources"
                            elif "assessment" in event.author.lower():
                                phase = "assessments"
                        await progress_callback(phase, message_text)
                except Exception as e:
                    print(f"[LearningPathRunner] Error processing event: {e}")
            elif event.content:
                print(f"[LearningPathRunner] Event: {event.content}")

        # Get the learning path from orchestrator instance (workaround for ADK session state)
        learning_path = self.orchestrator._last_learning_path

        if learning_path:
            print(f"[LearningPathRunner] Retrieved learning path with {len(learning_path.get('curriculum', {}).get('modules', []))} modules")
        else:
            print("[LearningPathRunner] ERROR: No learning path was generated")
            learning_path = {}

        # Clear the stored result to prevent stale data
        self.orchestrator._last_learning_path = None

        return learning_path

    async def generate_proficiency_assessment(self, topic: str) -> List[Dict]:
        """Generate proficiency assessment questions for a topic."""
        return self.orchestrator.user_profiler.generate_proficiency_assessment(topic)

    async def evaluate_quiz(self, quiz: Dict, user_responses: Dict[str, str]) -> Dict:
        """Evaluate a quiz submission."""
        evaluation = self.orchestrator.assessment_agent.evaluate_quiz(quiz, user_responses)
        gaps = self.orchestrator.assessment_agent.identify_knowledge_gaps(evaluation)
        evaluation["knowledge_gaps"] = gaps
        return evaluation
