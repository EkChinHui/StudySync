"""Curriculum Agent - ADK implementation for curriculum generation."""

from typing import AsyncGenerator, Dict, List, Optional, Any
from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.genai import types
from pydantic import Field

from backend.services.llm_service import LLMService


class CurriculumAgent(BaseAgent):
    """
    Agent responsible for generating learning curriculum structure.

    This agent creates the curriculum with modules and topics, but does NOT
    find resources. Resources are found per-session by the ResourceFinderAgent
    after scheduling.

    Reads from session state:
        - topic: The learning topic
        - user_profile: User profile from UserProfilerAgent
        - duration_weeks: Optional duration constraint

    Writes to session state:
        - curriculum: Dict with modules and topics (no resources yet)
    """

    name: str = "curriculum_agent"
    description: str = "Generates personalized learning curriculum structure with modules and topics"

    # Services
    llm_service: LLMService = Field(default_factory=LLMService)

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        """Execute curriculum generation logic."""
        print(f"[{self.name}] Starting curriculum generation...")

        # Read inputs from session state
        topic = ctx.session.state.get("topic", "")
        user_profile = ctx.session.state.get("user_profile", {})
        duration_weeks = ctx.session.state.get("duration_weeks")
        progress_callback = ctx.session.state.get("progress_callback")

        # Emit initial progress
        if progress_callback:
            await progress_callback("curriculum", f"Generating curriculum for {topic}...")

        # Generate curriculum structure (without resources)
        curriculum = self.llm_service.generate_curriculum(
            topic=topic,
            proficiency_level=user_profile.get("proficiency_level", "beginner"),
            commitment_level=user_profile.get("commitment_level", "moderate"),
            duration_weeks=duration_weeks
        )

        num_modules = len(curriculum.get('modules', []))
        print(f"[{self.name}] Generated {num_modules} modules")

        # Store in session state (resources will be added per-session later)
        ctx.session.state["curriculum"] = curriculum

        print(f"[{self.name}] Curriculum structure complete")

        # Emit completion progress
        if progress_callback:
            module_titles = [m.get("title", "") for m in curriculum.get("modules", [])[:3]]
            preview = ", ".join(module_titles)
            if num_modules > 3:
                preview += f"... ({num_modules} total)"
            await progress_callback(
                "curriculum",
                f"Curriculum ready with {num_modules} modules: {preview}"
            )

        # Yield completion event
        yield Event(
            author=self.name,
            content=types.Content(
                role="model",
                parts=[types.Part(text=f"Curriculum generated with {num_modules} modules")]
            )
        )
