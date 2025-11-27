"""Google Calendar integration service."""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import json


class CalendarService:
    """Service for Google Calendar operations."""

    def __init__(self, credentials_dict: dict):
        """Initialize with OAuth credentials."""
        self.credentials = Credentials(
            token=credentials_dict.get("token"),
            refresh_token=credentials_dict.get("refresh_token"),
            token_uri=credentials_dict.get("token_uri", "https://oauth2.googleapis.com/token"),
            client_id=credentials_dict.get("client_id"),
            client_secret=credentials_dict.get("client_secret"),
            scopes=credentials_dict.get("scopes", ["https://www.googleapis.com/auth/calendar"])
        )
        self.service = build("calendar", "v3", credentials=self.credentials)

    def get_availability(self, days_back: int = 14) -> List[Dict]:
        """
        Analyze calendar for availability patterns.
        Returns free slots and busy patterns from the last N days.
        """
        now = datetime.utcnow()
        time_min = (now - timedelta(days=days_back)).isoformat() + "Z"
        time_max = now.isoformat() + "Z"

        try:
            events_result = self.service.events().list(
                calendarId="primary",
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy="startTime"
            ).execute()

            events = events_result.get("items", [])

            # Analyze patterns
            busy_hours = self._analyze_busy_hours(events)
            weekly_free_hours = self._calculate_weekly_free_hours(events)

            return {
                "busy_hours": busy_hours,
                "weekly_free_hours": weekly_free_hours,
                "events_analyzed": len(events)
            }

        except HttpError as error:
            print(f"An error occurred: {error}")
            return {"error": str(error)}

    def _analyze_busy_hours(self, events: List[Dict]) -> Dict[str, List[int]]:
        """Identify which hours are typically busy each day."""
        # Simple heuristic: count events by hour and day of week
        busy_by_day = {str(i): [] for i in range(7)}  # 0=Monday, 6=Sunday

        for event in events:
            start = event.get("start", {}).get("dateTime")
            if not start:
                continue

            dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
            day_of_week = dt.weekday()
            hour = dt.hour
            busy_by_day[str(day_of_week)].append(hour)

        return busy_by_day

    def _calculate_weekly_free_hours(self, events: List[Dict]) -> float:
        """Estimate average weekly free hours (9am-9pm work hours)."""
        # Simplified: assume 12 hours available per day (9am-9pm)
        # Subtract average daily meeting hours
        if not events:
            return 60.0  # Assume 60 hours free if no data

        total_busy_hours = 0
        for event in events:
            start = event.get("start", {}).get("dateTime")
            end = event.get("end", {}).get("dateTime")

            if start and end:
                start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
                end_dt = datetime.fromisoformat(end.replace("Z", "+00:00"))
                duration = (end_dt - start_dt).total_seconds() / 3600
                total_busy_hours += duration

        days_analyzed = 14
        avg_busy_per_day = total_busy_hours / days_analyzed
        avg_free_per_day = max(0, 12 - avg_busy_per_day)  # 12 hours available per day
        weekly_free = avg_free_per_day * 7

        return round(weekly_free, 1)

    def find_free_slots(self, start_date: datetime, num_sessions: int, session_duration_minutes: int) -> List[Dict]:
        """
        Find free slots for scheduling sessions.
        Simple implementation: find gaps between 9am-9pm.
        """
        slots = []
        current_date = start_date

        # Get events for next 60 days
        time_min = current_date.isoformat() + "Z"
        time_max = (current_date + timedelta(days=60)).isoformat() + "Z"

        try:
            events_result = self.service.events().list(
                calendarId="primary",
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy="startTime"
            ).execute()

            events = events_result.get("items", [])

            # Simple slot finding: look for free slots between 9am-9pm
            search_date = current_date
            while len(slots) < num_sessions and search_date < current_date + timedelta(days=60):
                # Skip weekends for POC
                if search_date.weekday() >= 5:
                    search_date += timedelta(days=1)
                    continue

                # Check 6pm-8pm slot (good for working professionals)
                slot_start = search_date.replace(hour=18, minute=0, second=0, microsecond=0)
                slot_end = slot_start + timedelta(minutes=session_duration_minutes)

                # Check if slot is free
                if self._is_slot_free(slot_start, slot_end, events):
                    slots.append({
                        "start": slot_start.isoformat(),
                        "end": slot_end.isoformat(),
                        "duration_minutes": session_duration_minutes
                    })

                search_date += timedelta(days=1)

            return slots

        except HttpError as error:
            print(f"An error occurred: {error}")
            return []

    def _is_slot_free(self, slot_start: datetime, slot_end: datetime, events: List[Dict]) -> bool:
        """Check if a time slot is free."""
        for event in events:
            event_start = event.get("start", {}).get("dateTime")
            event_end = event.get("end", {}).get("dateTime")

            if not event_start or not event_end:
                continue

            event_start_dt = datetime.fromisoformat(event_start.replace("Z", "+00:00"))
            event_end_dt = datetime.fromisoformat(event_end.replace("Z", "+00:00"))

            # Check for overlap
            if slot_start < event_end_dt and slot_end > event_start_dt:
                return False

        return True

    def create_event(self, summary: str, start_time: datetime, duration_minutes: int, description: str = "") -> Dict:
        """Create a calendar event."""
        end_time = start_time + timedelta(minutes=duration_minutes)

        event = {
            "summary": summary,
            "description": description,
            "start": {
                "dateTime": start_time.isoformat(),
                "timeZone": "UTC",
            },
            "end": {
                "dateTime": end_time.isoformat(),
                "timeZone": "UTC",
            },
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "popup", "minutes": 30},
                ],
            },
        }

        try:
            event = self.service.events().insert(calendarId="primary", body=event).execute()
            return {"success": True, "event_id": event.get("id"), "link": event.get("htmlLink")}
        except HttpError as error:
            return {"success": False, "error": str(error)}


def generate_ics_file(sessions: List[Dict]) -> str:
    """Generate .ics file content for calendar import."""
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//StudySync//Learning Schedule//EN",
        "CALSCALE:GREGORIAN",
    ]

    for session in sessions:
        start_dt = datetime.fromisoformat(session["scheduled_time"])
        end_dt = start_dt + timedelta(minutes=session.get("duration_minutes", 30))

        # Format for iCalendar
        dtstart = start_dt.strftime("%Y%m%dT%H%M%S")
        dtend = end_dt.strftime("%Y%m%dT%H%M%S")

        lines.extend([
            "BEGIN:VEVENT",
            f"SUMMARY:{session['module_title']}",
            f"DTSTART:{dtstart}",
            f"DTEND:{dtend}",
            f"DESCRIPTION:StudySync Learning Session",
            "BEGIN:VALARM",
            "TRIGGER:-PT30M",
            "DESCRIPTION:Study session starting in 30 minutes",
            "ACTION:DISPLAY",
            "END:VALARM",
            "END:VEVENT",
        ])

    lines.append("END:VCALENDAR")
    return "\n".join(lines)
