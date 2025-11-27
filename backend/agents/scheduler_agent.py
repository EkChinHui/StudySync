"""Scheduler Agent - Creates optimal study schedules."""

from typing import Dict, List
from datetime import datetime, timedelta
from backend.services.calendar_service import CalendarService


class SchedulerAgent:
    """Agent responsible for intelligent lesson scheduling."""

    def __init__(self):
        """Initialize the agent."""
        pass

    async def run(self, curriculum: Dict, user_profile: Dict, calendar_credentials: Dict = None, start_date: str = None, end_date: str = None) -> List[Dict]:
        """
        Generate study schedule for the curriculum.

        Args:
            curriculum: Curriculum from CurriculumAgent
            user_profile: User profile from UserProfilerAgent
            calendar_credentials: Optional Google Calendar credentials
            start_date: Optional start date string (ISO format)
            end_date: Optional end date string (ISO format)

        Returns:
            List of scheduled study sessions
        """
        sessions = []
        session_duration = user_profile["preferences"]["session_duration"]

        # Determine sessions per week based on commitment
        sessions_per_week = self._get_sessions_per_week(user_profile["commitment_level"])

        # Calculate total sessions needed
        total_hours = sum(module.get("duration_hours", 2) for module in curriculum.get("modules", []))
        total_sessions = int(total_hours * 60 / session_duration)

        # Adjust sessions per week if end_date is provided
        if start_date and end_date:
            try:
                start = datetime.fromisoformat(start_date)
                end = datetime.fromisoformat(end_date)
                weeks = (end - start).days / 7
                if weeks > 0:
                    required_per_week = total_sessions / weeks
                    # If required frequency is higher than preference, we might need to warn or adjust
                    # For now, we'll take the maximum of the two to ensure completion
                    sessions_per_week = max(sessions_per_week, int(required_per_week) + 1)
            except Exception as e:
                print(f"Error calculating sessions per week from dates: {e}")

        # Find available slots
        if calendar_credentials:
            slots = await self._find_calendar_slots(
                calendar_credentials,
                total_sessions,
                session_duration
            )
        else:
            slots = self._generate_default_slots(
                total_sessions,
                session_duration,
                sessions_per_week,
                start_date
            )

        # Map sessions to modules
        session_idx = 0
        for module in curriculum.get("modules", []):
            subtopics = module.get("subtopics", [])
            
            # If subtopics are structured (dicts), use them to define sessions
            if subtopics and isinstance(subtopics[0], dict):
                module_sessions = len(subtopics)
                for i, subtopic in enumerate(subtopics):
                    if session_idx >= len(slots):
                        break
                    
                    slot = slots[session_idx]
                    sessions.append({
                        "module_id": module["module_id"],
                        "module_title": f"{module['title']}: {subtopic['title']}",
                        "description": subtopic.get("description", ""),
                        "scheduled_time": slot["start"],
                        "duration_minutes": subtopic.get("estimated_minutes", session_duration),
                        "resources": module.get("resources", [])[:2],  # First 2 resources
                        "session_number": i + 1,
                        "total_module_sessions": module_sessions
                    })
                    session_idx += 1
            else:
                # Fallback to duration-based splitting if subtopics are just strings
                module_sessions = int(module.get("duration_hours", 2) * 60 / session_duration)
                for i in range(module_sessions):
                    if session_idx >= len(slots):
                        break

                    slot = slots[session_idx]
                    sessions.append({
                        "module_id": module["module_id"],
                        "module_title": module["title"],
                        "description": f"Session {i+1} of {module['title']}",
                        "scheduled_time": slot["start"],
                        "duration_minutes": session_duration,
                        "resources": module.get("resources", [])[:2],
                        "session_number": i + 1,
                        "total_module_sessions": module_sessions
                    })
                    session_idx += 1

        return sessions

    def _get_sessions_per_week(self, commitment_level: str) -> int:
        """Determine number of sessions per week based on commitment."""
        mapping = {
            "light": 2,  # 2 sessions/week
            "moderate": 3,  # 3 sessions/week
            "intensive": 5  # 5 sessions/week
        }
        return mapping.get(commitment_level, 3)

    async def _find_calendar_slots(self, credentials: Dict, num_sessions: int, duration_minutes: int) -> List[Dict]:
        """Find available slots in user's calendar."""
        try:
            calendar_service = CalendarService(credentials)
            start_date = datetime.now() + timedelta(days=1)  # Start tomorrow
            slots = calendar_service.find_free_slots(start_date, num_sessions, duration_minutes)
            return slots
        except Exception as e:
            print(f"Error finding calendar slots: {e}")
            return self._generate_default_slots(num_sessions, duration_minutes, 3)

    def _generate_default_slots(self, num_sessions: int, duration_minutes: int, sessions_per_week: int, start_date_str: str = None) -> List[Dict]:
        """Generate default time slots without calendar integration."""
        slots = []
        
        if start_date_str:
            try:
                current_date = datetime.fromisoformat(start_date_str)
            except ValueError:
                current_date = datetime.now() + timedelta(days=1)
        else:
            current_date = datetime.now() + timedelta(days=1)  # Start tomorrow

        # Default to 6 PM on weekdays
        default_hour = 18
        default_minute = 0

        sessions_this_week = 0
        while len(slots) < num_sessions:
            # Skip weekends unless we need to be intensive (more than 5 sessions/week)
            if sessions_per_week <= 5 and current_date.weekday() >= 5:
                current_date += timedelta(days=1)
                continue

            # Check if we've scheduled enough for this week
            if sessions_this_week >= sessions_per_week:
                # Move to next week
                days_to_monday = 7 - current_date.weekday()
                current_date += timedelta(days=days_to_monday)
                sessions_this_week = 0
                continue

            slot_start = current_date.replace(hour=default_hour, minute=default_minute, second=0, microsecond=0)
            slot_end = slot_start + timedelta(minutes=duration_minutes)

            slots.append({
                "start": slot_start.isoformat(),
                "end": slot_end.isoformat(),
                "duration_minutes": duration_minutes
            })

            sessions_this_week += 1
            current_date += timedelta(days=1)

        return slots
