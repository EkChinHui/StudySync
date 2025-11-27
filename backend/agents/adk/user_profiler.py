"""UserProfiler Agent - ADK implementation for proficiency assessment."""

from typing import AsyncGenerator, Dict, List, Optional, Any
from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.genai import types
from pydantic import Field

from backend.services.llm_service import LLMService
from backend.services.calendar_service import CalendarService


class UserProfilerAgent(BaseAgent):
    """
    Agent responsible for analyzing user proficiency and availability.

    Reads from session state:
        - topic: The learning topic
        - assessment_responses: User's answers to proficiency questions
        - calendar_credentials: Optional Google Calendar credentials

    Writes to session state:
        - user_profile: Dict with proficiency_level, commitment_level, etc.
    """

    name: str = "user_profiler"
    description: str = "Analyzes user proficiency level and time availability to create a learning profile"

    # Services
    llm_service: LLMService = Field(default_factory=LLMService)
    calendar_service: CalendarService = Field(default_factory=CalendarService)

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        """Execute user profiling logic."""
        print(f"[{self.name}] Starting user profiling...")

        # Read inputs from session state
        topic = ctx.session.state.get("topic", "")
        assessment_responses = ctx.session.state.get("assessment_responses", [])
        calendar_credentials = ctx.session.state.get("calendar_credentials")
        user_proficiency_level = ctx.session.state.get("proficiency_level")
        user_commitment_level = ctx.session.state.get("commitment_level")
        progress_callback = ctx.session.state.get("progress_callback")

        # Emit initial progress
        if progress_callback:
            await progress_callback("profiling", "Analyzing your proficiency level...")

        # Assess proficiency - user selection takes precedence
        if user_proficiency_level and user_proficiency_level in ["beginner", "intermediate", "advanced"]:
            proficiency_level = user_proficiency_level
            print(f"[{self.name}] Using user-selected proficiency: {proficiency_level}")
        else:
            proficiency_level = self._assess_proficiency(assessment_responses)
            print(f"[{self.name}] Assessed proficiency: {proficiency_level}")

        # Analyze calendar availability if credentials provided
        weekly_free_hours = 10  # Default
        calendar_analyzed = False

        if calendar_credentials:
            try:
                availability = self.calendar_service.get_availability(calendar_credentials)
                weekly_free_hours = availability.get("weekly_free_hours", 10)
                calendar_analyzed = True
                print(f"[{self.name}] Calendar analyzed: {weekly_free_hours} free hours/week")
            except Exception as e:
                print(f"[{self.name}] Calendar analysis failed: {e}")

        # Determine commitment level - user selection takes precedence
        if user_commitment_level and user_commitment_level in ["light", "moderate", "intensive"]:
            commitment_level = user_commitment_level
            print(f"[{self.name}] Using user-selected commitment: {commitment_level}")
        else:
            commitment_level = self._determine_commitment(weekly_free_hours)

        # Build user profile
        user_profile = {
            "topic": topic,
            "proficiency_level": proficiency_level,
            "commitment_level": commitment_level,
            "weekly_free_hours": weekly_free_hours,
            "calendar_analyzed": calendar_analyzed,
            "preferences": {
                "session_duration": self._get_session_duration(commitment_level),
                "preferred_times": ["evening"]
            }
        }

        # Store in session state
        ctx.session.state["user_profile"] = user_profile

        print(f"[{self.name}] Profile complete: {proficiency_level} - {commitment_level}")

        # Emit completion progress
        if progress_callback:
            await progress_callback(
                "profiling",
                f"Profile complete: {proficiency_level.capitalize()} level, {commitment_level} commitment"
            )

        # Yield completion event
        yield Event(
            author=self.name,
            content=types.Content(
                role="model",
                parts=[types.Part(text=f"User profile created: {proficiency_level} level, {commitment_level} commitment")]
            )
        )

    def _assess_proficiency(self, responses: List[Dict]) -> str:
        """Assess user proficiency based on assessment responses."""
        if not responses:
            return "beginner"

        # Simple scoring: count correct answers or self-reported levels
        score = 0
        for response in responses:
            if response.get("is_correct"):
                score += 1
            # Also check for self-reported familiarity
            answer = str(response.get("user_answer", "")).lower()
            if "advanced" in answer or "expert" in answer:
                score += 2
            elif "intermediate" in answer or "some experience" in answer:
                score += 1

        # Map score to level
        avg_score = score / len(responses) if responses else 0

        if avg_score >= 1.5:
            return "advanced"
        elif avg_score >= 0.5:
            return "intermediate"
        return "beginner"

    def _determine_commitment(self, weekly_hours: float) -> str:
        """Map weekly free hours to commitment level."""
        if weekly_hours >= 15:
            return "intensive"
        elif weekly_hours >= 8:
            return "moderate"
        return "light"

    def _get_session_duration(self, commitment_level: str) -> int:
        """Get recommended session duration based on commitment level."""
        durations = {
            "light": 30,
            "moderate": 45,
            "intensive": 60
        }
        return durations.get(commitment_level, 30)

    def generate_proficiency_assessment(self, topic: str) -> List[Dict]:
        """Generate proficiency assessment questions for a topic."""
        return self.llm_service.generate_proficiency_questions(topic)
