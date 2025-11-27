"""Scheduler Agent - ADK implementation for study schedule generation."""

from typing import AsyncGenerator, Dict, List, Optional
from datetime import datetime, timedelta
from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.genai import types
from pydantic import Field

from backend.services.calendar_service import CalendarService


class SchedulerAgent(BaseAgent):
    """
    Agent responsible for creating optimal study schedules.

    Creates one session per topic/subtopic. Each session has a specific topic
    that will later get unique resources from the ResourceFinderAgent.

    Reads from session state:
        - curriculum: Curriculum from CurriculumAgent
        - user_profile: User profile from UserProfilerAgent
        - calendar_credentials: Optional Google Calendar credentials
        - start_date: Optional start date
        - end_date: Optional end date

    Writes to session state:
        - schedule: List of scheduled study sessions (without resources)
    """

    name: str = "scheduler_agent"
    description: str = "Creates optimal study schedules based on curriculum and user availability"

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        """Execute schedule generation logic."""
        print(f"[{self.name}] Starting schedule generation...")

        # Read inputs from session state
        curriculum = ctx.session.state.get("curriculum", {})
        user_profile = ctx.session.state.get("user_profile", {})
        calendar_credentials = ctx.session.state.get("calendar_credentials")
        start_date = ctx.session.state.get("start_date")
        end_date = ctx.session.state.get("end_date")
        main_topic = ctx.session.state.get("topic", "")
        progress_callback = ctx.session.state.get("progress_callback")

        # Emit initial progress
        if progress_callback:
            await progress_callback("scheduling", "Creating your study schedule...")

        # Generate schedule
        sessions = []
        preferences = user_profile.get("preferences", {})
        session_duration = preferences.get("session_duration", 30)
        commitment_level = user_profile.get("commitment_level", "moderate")

        # Determine sessions per week
        sessions_per_week = self._get_sessions_per_week(commitment_level)

        # Count total sessions needed (one per subtopic)
        total_sessions = 0
        for module in curriculum.get("modules", []):
            subtopics = module.get("subtopics", [])
            if subtopics:
                total_sessions += len(subtopics)
            else:
                # Fallback: estimate based on duration
                total_sessions += max(1, int(module.get("duration_hours", 2) * 60 / session_duration))

        # Adjust sessions per week if end_date provided
        if start_date and end_date:
            try:
                start = datetime.fromisoformat(start_date)
                end = datetime.fromisoformat(end_date)
                weeks = (end - start).days / 7
                if weeks > 0:
                    required_per_week = total_sessions / weeks
                    sessions_per_week = max(sessions_per_week, int(required_per_week) + 1)
            except Exception as e:
                print(f"[{self.name}] Error calculating dates: {e}")

        # Generate time slots
        if calendar_credentials:
            slots = await self._find_calendar_slots(
                calendar_credentials, total_sessions, session_duration
            )
        else:
            slots = self._generate_default_slots(
                total_sessions, session_duration, sessions_per_week, start_date
            )

        # Create one session per subtopic with specific topic info
        session_idx = 0
        session_number = 1
        for module in curriculum.get("modules", []):
            subtopics = module.get("subtopics", [])

            if subtopics and isinstance(subtopics[0], dict):
                for subtopic in subtopics:
                    if session_idx >= len(slots):
                        break

                    slot = slots[session_idx]
                    sessions.append({
                        "session_id": f"s{session_number}",
                        "module_id": module["module_id"],
                        "module_title": module["title"],
                        "session_topic": subtopic["title"],
                        "session_description": subtopic.get("description", ""),
                        "main_topic": main_topic,
                        "scheduled_time": slot["start"],
                        "duration_minutes": subtopic.get("estimated_minutes", session_duration),
                        "session_number": session_number,
                        "total_sessions": total_sessions,
                        "resources": []  # Will be filled by ResourceFinderAgent
                    })
                    session_idx += 1
                    session_number += 1
            elif subtopics:
                # Subtopics are strings
                for subtopic_title in subtopics:
                    if session_idx >= len(slots):
                        break

                    slot = slots[session_idx]
                    sessions.append({
                        "session_id": f"s{session_number}",
                        "module_id": module["module_id"],
                        "module_title": module["title"],
                        "session_topic": subtopic_title,
                        "session_description": f"Learn about {subtopic_title}",
                        "main_topic": main_topic,
                        "scheduled_time": slot["start"],
                        "duration_minutes": session_duration,
                        "session_number": session_number,
                        "total_sessions": total_sessions,
                        "resources": []
                    })
                    session_idx += 1
                    session_number += 1
            else:
                # No subtopics - create single session for module
                if session_idx >= len(slots):
                    break

                slot = slots[session_idx]
                sessions.append({
                    "session_id": f"s{session_number}",
                    "module_id": module["module_id"],
                    "module_title": module["title"],
                    "session_topic": module["title"],
                    "session_description": f"Introduction to {module['title']}",
                    "main_topic": main_topic,
                    "scheduled_time": slot["start"],
                    "duration_minutes": session_duration,
                    "session_number": session_number,
                    "total_sessions": total_sessions,
                    "resources": []
                })
                session_idx += 1
                session_number += 1

        # Store in session state
        ctx.session.state["schedule"] = sessions

        print(f"[{self.name}] Schedule created with {len(sessions)} sessions")

        # Emit completion progress
        if progress_callback:
            await progress_callback(
                "scheduling",
                f"Schedule created with {len(sessions)} study sessions"
            )

        # Yield completion event
        yield Event(
            author=self.name,
            content=types.Content(
                role="model",
                parts=[types.Part(text=f"Schedule created with {len(sessions)} sessions")]
            )
        )

    def _get_sessions_per_week(self, commitment_level: str) -> int:
        """Determine sessions per week based on commitment."""
        mapping = {
            "light": 2,
            "moderate": 3,
            "intensive": 5
        }
        return mapping.get(commitment_level, 3)

    async def _find_calendar_slots(
        self,
        credentials: Dict,
        num_sessions: int,
        duration_minutes: int
    ) -> List[Dict]:
        """Find available calendar slots."""
        try:
            calendar_service = CalendarService(credentials)
            start_date = datetime.now() + timedelta(days=1)
            slots = calendar_service.find_free_slots(start_date, num_sessions, duration_minutes)
            return slots
        except Exception as e:
            print(f"[{self.name}] Calendar error: {e}")
            return self._generate_default_slots(num_sessions, duration_minutes, 3)

    def _generate_default_slots(
        self,
        num_sessions: int,
        duration_minutes: int,
        sessions_per_week: int,
        start_date_str: str = None
    ) -> List[Dict]:
        """Generate default time slots."""
        slots = []

        if start_date_str:
            try:
                current_date = datetime.fromisoformat(start_date_str)
            except ValueError:
                current_date = datetime.now() + timedelta(days=1)
        else:
            current_date = datetime.now() + timedelta(days=1)

        default_hour = 18
        sessions_this_week = 0

        while len(slots) < num_sessions:
            if sessions_per_week <= 5 and current_date.weekday() >= 5:
                current_date += timedelta(days=1)
                continue

            if sessions_this_week >= sessions_per_week:
                days_to_monday = 7 - current_date.weekday()
                current_date += timedelta(days=days_to_monday)
                sessions_this_week = 0
                continue

            slot_start = current_date.replace(
                hour=default_hour, minute=0, second=0, microsecond=0
            )
            slot_end = slot_start + timedelta(minutes=duration_minutes)

            slots.append({
                "start": slot_start.isoformat(),
                "end": slot_end.isoformat(),
                "duration_minutes": duration_minutes
            })

            sessions_this_week += 1
            current_date += timedelta(days=1)

        return slots
