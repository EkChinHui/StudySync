"""User Profiler Agent - Analyzes user proficiency and availability."""

from typing import Dict, List
from backend.services.calendar_service import CalendarService
from backend.services.llm_service import LLMService


class UserProfilerAgent:
    """Agent responsible for user profiling and assessment."""

    def __init__(self):
        """Initialize the agent."""
        self.llm_service = LLMService()

    async def run(self, topic: str, calendar_credentials: Dict = None, assessment_responses: List[Dict] = None) -> Dict:
        """
        Run the user profiler agent.

        Args:
            topic: The learning topic
            calendar_credentials: Google Calendar OAuth credentials
            assessment_responses: User's responses to proficiency questions

        Returns:
            User profile with proficiency level, commitment, and availability
        """
        profile = {
            "topic": topic,
            "proficiency_level": "beginner",
            "commitment_level": "moderate",
            "weekly_free_hours": 40.0,
            "preferences": {
                "session_duration": 30,
                "preferred_times": ["evening"]
            }
        }

        # Analyze calendar if credentials provided
        if calendar_credentials:
            calendar_analysis = self._analyze_calendar(calendar_credentials)
            profile["weekly_free_hours"] = calendar_analysis.get("weekly_free_hours", 40.0)
            profile["calendar_analyzed"] = True
        else:
            profile["calendar_analyzed"] = False

        # Determine proficiency level from assessment
        if assessment_responses:
            proficiency = self._assess_proficiency(assessment_responses)
            profile["proficiency_level"] = proficiency

        # Determine commitment level based on availability
        commitment = self._determine_commitment(profile["weekly_free_hours"])
        profile["commitment_level"] = commitment

        return profile

    def generate_proficiency_assessment(self, topic: str) -> List[Dict]:
        """Generate proficiency assessment questions."""
        return self.llm_service.generate_proficiency_questions(topic)

    def _analyze_calendar(self, credentials: Dict) -> Dict:
        """Analyze user's Google Calendar for availability."""
        try:
            calendar_service = CalendarService(credentials)
            availability = calendar_service.get_availability(days_back=14)
            return availability
        except Exception as e:
            print(f"Error analyzing calendar: {e}")
            return {"weekly_free_hours": 40.0, "error": str(e)}

    def _assess_proficiency(self, responses: List[Dict]) -> str:
        """
        Assess proficiency level based on responses.
        Simple rule-based logic for POC.
        """
        if not responses:
            return "beginner"

        correct_count = 0
        total_questions = len(responses)

        for response in responses:
            if response.get("is_correct", False):
                correct_count += 1

        accuracy = correct_count / total_questions if total_questions > 0 else 0

        if accuracy >= 0.7:
            return "advanced"
        elif accuracy >= 0.4:
            return "intermediate"
        else:
            return "beginner"

    def _determine_commitment(self, weekly_free_hours: float) -> str:
        """Determine commitment level based on available time."""
        if weekly_free_hours < 10:
            return "light"  # 2-4 hours/week
        elif weekly_free_hours < 20:
            return "moderate"  # 5-8 hours/week
        else:
            return "intensive"  # 10+ hours/week
