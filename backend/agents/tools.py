"""StudySync Agent Tools - ADK tool functions for learning path creation.

Each tool is a Python function with detailed docstrings for LLM understanding.
Tools can access session state via ToolContext parameter.
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta

# Note: ToolContext is optional - tools work without ADK context for direct calls
try:
    from google.adk.tools.tool_context import ToolContext
except ImportError:
    ToolContext = None


# ============= Service Imports =============

def _get_llm_service():
    """Lazy load LLM service."""
    from backend.services.llm_service import LLMService
    return LLMService()


def _get_resource_service():
    """Lazy load resource discovery service."""
    from backend.services.resource_discovery_service import get_resource_discovery_service
    return get_resource_discovery_service()


def _get_calendar_service():
    """Lazy load calendar service."""
    from backend.services.calendar_service import CalendarService
    return CalendarService()


# ============= User Profiler Tools =============

def assess_proficiency(
    topic: str,
    assessment_responses: List[Dict] = None,
    tool_context: "ToolContext" = None
) -> Dict:
    """Assess user's proficiency level for a learning topic.

    Analyzes optional assessment responses to determine if the user is a
    beginner, intermediate, or advanced learner for the given topic.

    Args:
        topic: The learning topic to assess (e.g., "Python programming")
        assessment_responses: Optional list of assessment Q&A responses.
            Each response should have 'is_correct' (bool) and optionally
            'user_answer' (str) for self-reported familiarity.
        tool_context: ADK tool context for state access (optional)

    Returns:
        dict with:
        - 'proficiency_level': "beginner", "intermediate", or "advanced"
        - 'confidence_score': float 0.0-1.0 indicating assessment confidence
        - 'reasoning': str explaining the assessment
    """
    if not assessment_responses:
        return {
            "proficiency_level": "beginner",
            "confidence_score": 0.3,
            "reasoning": f"No assessment data provided for {topic}. Defaulting to beginner level."
        }

    # Score based on responses
    score = 0
    for response in assessment_responses:
        if response.get("is_correct"):
            score += 1
        # Check for self-reported familiarity
        answer = str(response.get("user_answer", "")).lower()
        if "advanced" in answer or "expert" in answer:
            score += 2
        elif "intermediate" in answer or "some experience" in answer:
            score += 1

    # Calculate average and map to level
    avg_score = score / len(assessment_responses) if assessment_responses else 0

    if avg_score >= 1.5:
        level = "advanced"
        reasoning = f"Strong performance on {topic} assessment indicates advanced knowledge."
    elif avg_score >= 0.5:
        level = "intermediate"
        reasoning = f"Moderate performance on {topic} assessment indicates intermediate knowledge."
    else:
        level = "beginner"
        reasoning = f"Assessment results suggest beginner-level knowledge of {topic}."

    return {
        "proficiency_level": level,
        "confidence_score": min(1.0, avg_score / 2),
        "reasoning": reasoning
    }


def analyze_calendar_availability(
    calendar_credentials: Dict = None,
    tool_context: "ToolContext" = None
) -> Dict:
    """Analyze user's calendar to find available study time slots.

    Connects to Google Calendar (if credentials provided) to identify
    free time slots suitable for study sessions.

    Args:
        calendar_credentials: Optional Google Calendar OAuth credentials dict
        tool_context: ADK tool context for state access (optional)

    Returns:
        dict with:
        - 'weekly_free_hours': float estimated free hours per week
        - 'available_slots': list of available time slots
        - 'busy_periods': list of busy time ranges
        - 'recommended_times': list of suggested study times
        - 'calendar_analyzed': bool whether calendar was successfully analyzed
    """
    if not calendar_credentials:
        return {
            "weekly_free_hours": 10,
            "available_slots": [],
            "busy_periods": [],
            "recommended_times": ["evening", "weekends"],
            "calendar_analyzed": False
        }

    try:
        calendar_service = _get_calendar_service()
        availability = calendar_service.get_availability(calendar_credentials)

        return {
            "weekly_free_hours": availability.get("weekly_free_hours", 10),
            "available_slots": availability.get("free_slots", []),
            "busy_periods": availability.get("busy_periods", []),
            "recommended_times": availability.get("recommended_times", ["evening"]),
            "calendar_analyzed": True
        }
    except Exception as e:
        print(f"[assess_calendar] Calendar analysis failed: {e}")
        return {
            "weekly_free_hours": 10,
            "available_slots": [],
            "busy_periods": [],
            "recommended_times": ["evening"],
            "calendar_analyzed": False,
            "error": str(e)
        }


def determine_commitment_level(
    weekly_hours: float = None,
    user_preference: str = None,
    tool_context: "ToolContext" = None
) -> Dict:
    """Determine user's commitment level based on available time or preference.

    Maps available weekly hours to a commitment level that determines
    session frequency and intensity.

    Args:
        weekly_hours: Optional estimated free hours per week
        user_preference: Optional explicit preference ("light", "moderate", "intensive")
        tool_context: ADK tool context for state access (optional)

    Returns:
        dict with:
        - 'commitment_level': "light", "moderate", or "intensive"
        - 'sessions_per_week': int recommended sessions per week
        - 'session_duration_minutes': int recommended session length
        - 'weekly_study_hours': float expected study time per week
    """
    # User preference takes precedence
    if user_preference and user_preference in ["light", "moderate", "intensive"]:
        level = user_preference
    elif weekly_hours is not None:
        if weekly_hours >= 15:
            level = "intensive"
        elif weekly_hours >= 8:
            level = "moderate"
        else:
            level = "light"
    else:
        level = "moderate"  # Default

    # Map level to specifics
    config = {
        "light": {
            "sessions_per_week": 2,
            "session_duration_minutes": 30,
            "weekly_study_hours": 2
        },
        "moderate": {
            "sessions_per_week": 3,
            "session_duration_minutes": 45,
            "weekly_study_hours": 5
        },
        "intensive": {
            "sessions_per_week": 5,
            "session_duration_minutes": 60,
            "weekly_study_hours": 10
        }
    }

    return {
        "commitment_level": level,
        **config[level]
    }


# ============= Curriculum Tools =============

def analyze_topic_scope(
    topic: str,
    proficiency_level: str,
    tool_context: "ToolContext" = None
) -> Dict:
    """Analyze a learning topic and determine its scope and key areas.

    Breaks down a topic into main learning areas and estimates complexity.
    Use this to understand what a topic covers before generating modules.

    Args:
        topic: The learning topic (e.g., "Python programming", "Machine Learning")
        proficiency_level: User's current level ("beginner", "intermediate", "advanced")
        tool_context: ADK tool context for state access (optional)

    Returns:
        dict with:
        - 'topic': str the learning topic
        - 'scope': str brief description of what the topic covers
        - 'key_areas': list of main learning areas (strings)
        - 'estimated_modules': int suggested number of modules
        - 'complexity': "low", "medium", or "high"
        - 'prerequisites_needed': list of prerequisite topics (if any)

    Example:
        >>> analyze_topic_scope("React Hooks", "beginner")
        {
            "topic": "React Hooks",
            "scope": "Modern React state and lifecycle management",
            "key_areas": ["useState", "useEffect", "useContext", "Custom Hooks"],
            "estimated_modules": 4,
            "complexity": "medium",
            "prerequisites_needed": ["JavaScript ES6", "React basics"]
        }
    """
    llm_service = _get_llm_service()
    return llm_service.analyze_topic_scope(topic, proficiency_level)


def generate_module_outline(
    topic: str,
    module_title: str,
    proficiency_level: str,
    module_number: int = 1,
    total_modules: int = 1,
    tool_context: "ToolContext" = None
) -> Dict:
    """Generate a detailed outline for a single curriculum module.

    Creates a module with learning objectives and subtopics. Use this
    iteratively to build a curriculum module by module.

    Args:
        topic: The main learning topic
        module_title: Title/focus of this specific module
        proficiency_level: User's current level ("beginner", "intermediate", "advanced")
        module_number: Position of this module in the sequence (1-based)
        total_modules: Total number of modules planned
        tool_context: ADK tool context for state access (optional)

    Returns:
        dict with:
        - 'module_id': str unique identifier (e.g., "m1")
        - 'title': str module title
        - 'description': str module overview
        - 'duration_hours': float estimated hours to complete
        - 'learning_objectives': list of 2-3 objective strings
        - 'subtopics': list of subtopic dicts, each with:
            - 'title': str subtopic title
            - 'description': str what will be covered
            - 'estimated_minutes': int session length
        - 'prerequisites': list of prerequisite module IDs

    Example:
        >>> generate_module_outline("Python", "Functions and Scope", "beginner", 2, 5)
        {
            "module_id": "m2",
            "title": "Functions and Scope",
            "description": "Learn to write reusable code with functions",
            "duration_hours": 3,
            "learning_objectives": ["Define and call functions", "Understand variable scope"],
            "subtopics": [
                {"title": "Defining Functions", "description": "...", "estimated_minutes": 30},
                {"title": "Parameters and Arguments", "description": "...", "estimated_minutes": 30},
                {"title": "Return Values", "description": "...", "estimated_minutes": 30}
            ],
            "prerequisites": ["m1"]
        }
    """
    llm_service = _get_llm_service()
    return llm_service.generate_module_outline(
        topic, module_title, proficiency_level, module_number, total_modules
    )


def estimate_curriculum_duration(
    modules: List[Dict],
    commitment_level: str,
    tool_context: "ToolContext" = None
) -> Dict:
    """Estimate total duration for a curriculum based on modules and commitment.

    Calculates how long it will take to complete a set of modules given
    the user's commitment level.

    Args:
        modules: List of module dicts with 'duration_hours' and 'subtopics'
        commitment_level: User's time commitment ("light", "moderate", "intensive")
        tool_context: ADK tool context for state access (optional)

    Returns:
        dict with:
        - 'total_hours': float total estimated hours
        - 'total_sessions': int total number of study sessions
        - 'estimated_weeks': float weeks to complete at given commitment
        - 'sessions_per_week': int based on commitment level
        - 'hours_per_week': float study time per week

    Example:
        >>> estimate_curriculum_duration(modules, "moderate")
        {
            "total_hours": 15,
            "total_sessions": 20,
            "estimated_weeks": 4,
            "sessions_per_week": 3,
            "hours_per_week": 5
        }
    """
    # Get commitment parameters
    commitment_config = determine_commitment_level(user_preference=commitment_level)
    sessions_per_week = commitment_config["sessions_per_week"]
    hours_per_week = commitment_config["weekly_study_hours"]

    # Calculate totals
    total_hours = sum(m.get("duration_hours", 2) for m in modules)
    total_sessions = sum(len(m.get("subtopics", [])) or 1 for m in modules)

    # Estimate weeks
    estimated_weeks = total_sessions / sessions_per_week if sessions_per_week > 0 else total_sessions / 3

    print(f"[estimate_curriculum_duration] {total_sessions} sessions, {estimated_weeks:.1f} weeks at {commitment_level}")

    return {
        "total_hours": total_hours,
        "total_sessions": total_sessions,
        "estimated_weeks": round(estimated_weeks, 1),
        "sessions_per_week": sessions_per_week,
        "hours_per_week": hours_per_week
    }


def generate_curriculum(
    topic: str,
    proficiency_level: str,
    commitment_level: str,
    duration_weeks: float = None,
    tool_context: "ToolContext" = None
) -> Dict:
    """Generate a complete structured learning curriculum for a topic.

    This is a convenience function that generates an entire curriculum at once.
    For more control, use analyze_topic_scope and generate_module_outline iteratively.

    Args:
        topic: The learning topic (e.g., "Python programming", "Machine Learning")
        proficiency_level: User's current level ("beginner", "intermediate", "advanced")
        commitment_level: User's time commitment ("light", "moderate", "intensive")
        duration_weeks: Optional constraint on curriculum duration in weeks
        tool_context: ADK tool context for state access (optional)

    Returns:
        dict with:
        - 'topic': str the learning topic
        - 'total_duration_weeks': int estimated weeks to complete
        - 'modules': list of module dicts, each containing:
            - 'module_id': str unique identifier
            - 'title': str module title
            - 'duration_hours': float estimated hours
            - 'learning_objectives': list of objective strings
            - 'subtopics': list of subtopic dicts with 'title', 'description', 'estimated_minutes'
            - 'prerequisites': list of prerequisite module IDs
    """
    llm_service = _get_llm_service()
    curriculum = llm_service.generate_curriculum(
        topic=topic,
        proficiency_level=proficiency_level,
        commitment_level=commitment_level,
        duration_weeks=duration_weeks
    )

    print(f"[generate_curriculum] Generated curriculum with {len(curriculum.get('modules', []))} modules")
    return curriculum


def get_module_resources(
    module_title: str,
    subtopics: List[str],
    tool_context: "ToolContext" = None
) -> List[Dict]:
    """Get learning resources for a specific module.

    Generates resource recommendations including videos, articles, and
    documentation for the given module and its subtopics.

    Args:
        module_title: Title of the module
        subtopics: List of subtopic strings or dicts with 'title' key
        tool_context: ADK tool context for state access (optional)

    Returns:
        list of resource dicts, each with:
        - 'type': "video", "article", "documentation", or "interactive"
        - 'title': str resource title
        - 'url': str resource URL
        - 'description': str brief description
    """
    llm_service = _get_llm_service()
    return llm_service.get_resources_for_module(module_title, subtopics)


def generate_study_guide(
    module_title: str,
    subtopics: List[str],
    tool_context: "ToolContext" = None
) -> str:
    """Generate a markdown study guide for a module.

    Creates a concise study guide with key concepts, important points,
    and practical examples for the module.

    Args:
        module_title: Title of the module
        subtopics: List of subtopic strings or dicts with 'title' key
        tool_context: ADK tool context for state access (optional)

    Returns:
        str markdown-formatted study guide
    """
    llm_service = _get_llm_service()
    return llm_service.generate_study_guide(module_title, subtopics)


# ============= Scheduler Tools =============

def generate_time_slots(
    num_slots: int,
    duration_minutes: int = 45,
    sessions_per_week: int = 3,
    start_date: str = None,
    preferred_time: str = "evening",
    skip_weekends: bool = True,
    tool_context: "ToolContext" = None
) -> Dict:
    """Generate available time slots for study sessions.

    Creates a list of time slots based on scheduling preferences.
    Use this before schedule_session to get available times.

    Args:
        num_slots: Number of time slots needed
        duration_minutes: Length of each session in minutes (default 45)
        sessions_per_week: Maximum sessions per week (default 3)
        start_date: Start date in ISO format YYYY-MM-DD (default: tomorrow)
        preferred_time: "morning" (9am), "afternoon" (2pm), or "evening" (6pm)
        skip_weekends: Whether to skip Saturday/Sunday (default True)
        tool_context: ADK tool context for state access (optional)

    Returns:
        dict with:
        - 'slots': list of slot dicts, each with:
            - 'slot_id': str unique identifier
            - 'start': str ISO datetime
            - 'end': str ISO datetime
            - 'duration_minutes': int
            - 'day_of_week': str (e.g., "Monday")
        - 'total_slots': int number of slots generated
        - 'span_weeks': float number of weeks covered

    Example:
        >>> generate_time_slots(10, duration_minutes=30, sessions_per_week=3)
        {
            "slots": [
                {"slot_id": "slot_1", "start": "2024-01-15T18:00:00", ...},
                ...
            ],
            "total_slots": 10,
            "span_weeks": 3.3
        }
    """
    slots = []

    # Parse start date
    if start_date:
        try:
            current_date = datetime.fromisoformat(start_date)
        except ValueError:
            current_date = datetime.now() + timedelta(days=1)
    else:
        current_date = datetime.now() + timedelta(days=1)

    # Set preferred hour
    hour_map = {"morning": 9, "afternoon": 14, "evening": 18}
    default_hour = hour_map.get(preferred_time, 18)

    sessions_this_week = 0
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    while len(slots) < num_slots:
        # Skip weekends if requested
        if skip_weekends and current_date.weekday() >= 5:
            current_date += timedelta(days=1)
            continue

        # Check weekly limit
        if sessions_this_week >= sessions_per_week:
            days_to_monday = 7 - current_date.weekday()
            current_date += timedelta(days=days_to_monday)
            sessions_this_week = 0
            continue

        slot_start = current_date.replace(hour=default_hour, minute=0, second=0, microsecond=0)
        slot_end = slot_start + timedelta(minutes=duration_minutes)

        slots.append({
            "slot_id": f"slot_{len(slots) + 1}",
            "start": slot_start.isoformat(),
            "end": slot_end.isoformat(),
            "duration_minutes": duration_minutes,
            "day_of_week": day_names[current_date.weekday()]
        })

        sessions_this_week += 1
        current_date += timedelta(days=1)

    # Calculate span
    if slots:
        first_slot = datetime.fromisoformat(slots[0]["start"])
        last_slot = datetime.fromisoformat(slots[-1]["start"])
        span_weeks = (last_slot - first_slot).days / 7
    else:
        span_weeks = 0

    print(f"[generate_time_slots] Generated {len(slots)} slots over {span_weeks:.1f} weeks")

    return {
        "slots": slots,
        "total_slots": len(slots),
        "span_weeks": round(span_weeks, 1)
    }


def schedule_session(
    module_id: str,
    module_title: str,
    session_topic: str,
    session_description: str,
    time_slot: Dict,
    session_number: int,
    total_sessions: int,
    learning_objectives: List[str] = None,
    main_topic: str = "",
    tool_context: "ToolContext" = None
) -> Dict:
    """Schedule a single study session into a time slot.

    Creates a session object with all necessary information.
    Use this iteratively to build a schedule session by session.

    Args:
        module_id: ID of the parent module
        module_title: Title of the parent module
        session_topic: Specific topic for this session
        session_description: Description of what will be covered
        time_slot: Time slot dict with 'start', 'end', 'duration_minutes'
        session_number: Position in the overall sequence (1-based)
        total_sessions: Total number of sessions in the curriculum
        learning_objectives: List of objectives for this session
        main_topic: Main topic of the curriculum
        tool_context: ADK tool context for state access (optional)

    Returns:
        dict with:
        - 'session_id': str unique identifier
        - 'module_id': str parent module ID
        - 'module_title': str parent module title
        - 'session_topic': str specific topic
        - 'session_description': str description
        - 'learning_objectives': list of objectives
        - 'main_topic': str main curriculum topic
        - 'scheduled_time': str ISO datetime
        - 'duration_minutes': int session length
        - 'session_number': int position in sequence
        - 'total_sessions': int total sessions
        - 'resources': list (empty, to be filled later)

    Example:
        >>> slot = {"start": "2024-01-15T18:00:00", "duration_minutes": 45}
        >>> schedule_session("m1", "Python Basics", "Variables", "Learn about variables", slot, 1, 20)
        {
            "session_id": "s1",
            "module_title": "Python Basics",
            "session_topic": "Variables",
            ...
        }
    """
    session = {
        "session_id": f"s{session_number}",
        "module_id": module_id,
        "module_title": module_title,
        "session_topic": session_topic,
        "session_description": session_description,
        "learning_objectives": learning_objectives or [],
        "main_topic": main_topic,
        "scheduled_time": time_slot.get("start"),
        "duration_minutes": time_slot.get("duration_minutes", 45),
        "session_number": session_number,
        "total_sessions": total_sessions,
        "resources": []
    }

    print(f"[schedule_session] Scheduled session {session_number}: {session_topic}")
    return session


def reschedule_session(
    session: Dict,
    new_time_slot: Dict,
    tool_context: "ToolContext" = None
) -> Dict:
    """Reschedule an existing session to a new time slot.

    Updates a session's scheduled time while preserving all other data.

    Args:
        session: Existing session dict to reschedule
        new_time_slot: New time slot dict with 'start', 'duration_minutes'
        tool_context: ADK tool context for state access (optional)

    Returns:
        dict: Updated session with new scheduled time

    Example:
        >>> new_slot = {"start": "2024-01-16T14:00:00", "duration_minutes": 45}
        >>> reschedule_session(session, new_slot)
        {..., "scheduled_time": "2024-01-16T14:00:00", ...}
    """
    updated_session = session.copy()
    updated_session["scheduled_time"] = new_time_slot.get("start")
    updated_session["duration_minutes"] = new_time_slot.get("duration_minutes", session.get("duration_minutes", 45))

    print(f"[reschedule_session] Rescheduled session {session.get('session_number')} to {new_time_slot.get('start')}")
    return updated_session


def validate_schedule(
    sessions: List[Dict],
    tool_context: "ToolContext" = None
) -> Dict:
    """Validate a schedule for conflicts and issues.

    Checks for overlapping sessions, gaps, and scheduling issues.

    Args:
        sessions: List of session dicts with 'scheduled_time' and 'duration_minutes'
        tool_context: ADK tool context for state access (optional)

    Returns:
        dict with:
        - 'valid': bool whether schedule has no conflicts
        - 'conflicts': list of conflict descriptions
        - 'warnings': list of warning messages
        - 'stats': dict with schedule statistics

    Example:
        >>> validate_schedule(sessions)
        {
            "valid": True,
            "conflicts": [],
            "warnings": ["Gap of 5 days between sessions 3 and 4"],
            "stats": {"total_sessions": 20, "span_days": 45}
        }
    """
    conflicts = []
    warnings = []

    if not sessions:
        return {
            "valid": True,
            "conflicts": [],
            "warnings": ["No sessions to validate"],
            "stats": {"total_sessions": 0, "span_days": 0}
        }

    # Sort sessions by time
    sorted_sessions = sorted(sessions, key=lambda s: s.get("scheduled_time", ""))

    # Check for overlaps
    for i in range(len(sorted_sessions) - 1):
        current = sorted_sessions[i]
        next_session = sorted_sessions[i + 1]

        try:
            current_start = datetime.fromisoformat(current.get("scheduled_time", ""))
            current_end = current_start + timedelta(minutes=current.get("duration_minutes", 45))
            next_start = datetime.fromisoformat(next_session.get("scheduled_time", ""))

            # Check overlap
            if current_end > next_start:
                conflicts.append(
                    f"Sessions {current.get('session_number')} and {next_session.get('session_number')} overlap"
                )

            # Check for large gaps (> 3 days)
            gap_days = (next_start - current_end).days
            if gap_days > 3:
                warnings.append(
                    f"Gap of {gap_days} days between sessions {current.get('session_number')} and {next_session.get('session_number')}"
                )

        except (ValueError, TypeError) as e:
            warnings.append(f"Could not parse time for session {current.get('session_number')}: {e}")

    # Calculate stats
    try:
        first_time = datetime.fromisoformat(sorted_sessions[0].get("scheduled_time", ""))
        last_time = datetime.fromisoformat(sorted_sessions[-1].get("scheduled_time", ""))
        span_days = (last_time - first_time).days
    except (ValueError, TypeError):
        span_days = 0

    print(f"[validate_schedule] Validated {len(sessions)} sessions: {len(conflicts)} conflicts, {len(warnings)} warnings")

    return {
        "valid": len(conflicts) == 0,
        "conflicts": conflicts,
        "warnings": warnings,
        "stats": {
            "total_sessions": len(sessions),
            "span_days": span_days
        }
    }


def create_study_schedule(
    curriculum: Dict,
    commitment_level: str,
    start_date: str = None,
    end_date: str = None,
    calendar_credentials: Dict = None,
    tool_context: "ToolContext" = None
) -> Dict:
    """Create a complete study schedule from a curriculum.

    This is a convenience function that generates an entire schedule at once.
    For more control, use generate_time_slots and schedule_session iteratively.

    Args:
        curriculum: Curriculum dict with 'modules' list
        commitment_level: User's commitment level ("light", "moderate", "intensive")
        start_date: Optional start date in ISO format (YYYY-MM-DD)
        end_date: Optional end date in ISO format (YYYY-MM-DD)
        calendar_credentials: Optional Google Calendar credentials for slot finding
        tool_context: ADK tool context for state access (optional)

    Returns:
        dict with:
        - 'sessions': list of session dicts
    """
    # Get session parameters based on commitment
    commitment_config = determine_commitment_level(user_preference=commitment_level)
    sessions_per_week = commitment_config["sessions_per_week"]
    session_duration = commitment_config["session_duration_minutes"]

    modules = curriculum.get("modules", [])
    main_topic = curriculum.get("topic", "")

    # Count total sessions needed (one per subtopic)
    total_sessions = 0
    for module in modules:
        subtopics = module.get("subtopics", [])
        if subtopics:
            total_sessions += len(subtopics)
        else:
            total_sessions += 1

    # Adjust sessions per week if end_date is constrained
    if start_date and end_date:
        try:
            start = datetime.fromisoformat(start_date)
            end = datetime.fromisoformat(end_date)
            weeks = (end - start).days / 7
            if weeks > 0:
                required_per_week = total_sessions / weeks
                sessions_per_week = max(sessions_per_week, int(required_per_week) + 1)
        except Exception as e:
            print(f"[create_study_schedule] Date calculation error: {e}")

    # Generate time slots using modular tool
    slots_result = generate_time_slots(
        num_slots=total_sessions,
        duration_minutes=session_duration,
        sessions_per_week=sessions_per_week,
        start_date=start_date,
        skip_weekends=(sessions_per_week <= 5)
    )
    slots = slots_result.get("slots", [])

    # Create sessions using modular tool
    sessions = []
    session_idx = 0
    session_number = 1

    for module in modules:
        subtopics = module.get("subtopics", [])
        module_objectives = module.get("learning_objectives", [])

        if subtopics:
            for subtopic in subtopics:
                if session_idx >= len(slots):
                    break

                # Handle subtopic as dict or string
                if isinstance(subtopic, dict):
                    topic_title = subtopic.get("title", f"Topic {session_number}")
                    topic_desc = subtopic.get("description", f"Learn about {topic_title}")
                    topic_minutes = subtopic.get("estimated_minutes", session_duration)
                else:
                    topic_title = str(subtopic)
                    topic_desc = f"Learn about {topic_title}"
                    topic_minutes = session_duration

                # Update slot duration if subtopic has specific duration
                slot = slots[session_idx].copy()
                slot["duration_minutes"] = topic_minutes

                session = schedule_session(
                    module_id=module.get("module_id", f"m{len(sessions) + 1}"),
                    module_title=module.get("title", ""),
                    session_topic=topic_title,
                    session_description=topic_desc,
                    time_slot=slot,
                    session_number=session_number,
                    total_sessions=total_sessions,
                    learning_objectives=module_objectives,
                    main_topic=main_topic
                )
                sessions.append(session)
                session_idx += 1
                session_number += 1
        else:
            # No subtopics - create single session for module
            if session_idx >= len(slots):
                break

            session = schedule_session(
                module_id=module.get("module_id", f"m{len(sessions) + 1}"),
                module_title=module.get("title", ""),
                session_topic=module.get("title", ""),
                session_description=f"Introduction to {module.get('title', '')}",
                time_slot=slots[session_idx],
                session_number=session_number,
                total_sessions=total_sessions,
                learning_objectives=module_objectives,
                main_topic=main_topic
            )
            sessions.append(session)
            session_idx += 1
            session_number += 1

    print(f"[create_study_schedule] Created {len(sessions)} sessions")
    return {"sessions": sessions}


# ============= Assessment Tools =============

def generate_module_quiz(
    module_id: str,
    module_title: str,
    subtopics: List[str],
    proficiency_level: str = "beginner",
    num_questions: int = 5,
    tool_context: "ToolContext" = None
) -> Dict:
    """Generate a quiz for a curriculum module.

    Creates multiple-choice questions testing understanding of the
    module's topics, with difficulty appropriate to proficiency level.

    Args:
        module_id: Unique identifier for the module
        module_title: Title of the module
        subtopics: List of subtopic strings covered in the module
        proficiency_level: Target difficulty ("beginner", "intermediate", "advanced")
        num_questions: Number of questions to generate (default 5)
        tool_context: ADK tool context for state access (optional)

    Returns:
        dict with:
        - 'module_id': str module identifier
        - 'module_title': str module title
        - 'assessment_type': "module_quiz"
        - 'questions': list of question dicts, each with:
            - 'question': str question text
            - 'options': dict of option letter to option text
            - 'correct_answer': str letter of correct answer
            - 'explanation': str explanation of correct answer
        - 'total_questions': int number of questions
    """
    llm_service = _get_llm_service()
    questions = llm_service.generate_quiz(
        module_title=module_title,
        subtopics=subtopics,
        num_questions=num_questions
    )

    print(f"[generate_module_quiz] Generated {len(questions)} questions for {module_title}")

    return {
        "module_id": module_id,
        "module_title": module_title,
        "assessment_type": "module_quiz",
        "questions": questions,
        "total_questions": len(questions)
    }


def evaluate_quiz_responses(
    quiz: Dict,
    user_responses: Dict[str, str],
    tool_context: "ToolContext" = None
) -> Dict:
    """Evaluate user's quiz responses and provide feedback.

    Grades the quiz and identifies areas for improvement.

    Args:
        quiz: Quiz dict with 'questions' list
        user_responses: Dict mapping question index (as string) to answer letter
        tool_context: ADK tool context for state access (optional)

    Returns:
        dict with:
        - 'score': float 0.0-1.0 percentage score
        - 'correct_count': int number of correct answers
        - 'total_questions': int total number of questions
        - 'passed': bool whether score >= 60%
        - 'results': list of result dicts for each question with:
            - 'question_id': str
            - 'question': str
            - 'user_answer': str
            - 'correct_answer': str
            - 'is_correct': bool
            - 'explanation': str
        - 'knowledge_gaps': list of improvement suggestions
    """
    correct_count = 0
    questions = quiz.get("questions", [])
    total_questions = len(questions)
    results = []

    for idx, question in enumerate(questions):
        question_id = str(idx)
        # Support both "0" and "q0" formats from frontend
        user_answer = user_responses.get(question_id, "") or user_responses.get(f"q{idx}", "")
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

    # Identify knowledge gaps
    knowledge_gaps = []
    if score < 0.7:
        knowledge_gaps.append("Consider reviewing the module materials before retaking the quiz")

    incorrect_count = total_questions - correct_count
    if incorrect_count > 0:
        knowledge_gaps.append(f"Review the {incorrect_count} questions you missed")

    return {
        "score": score,
        "correct_count": correct_count,
        "total_questions": total_questions,
        "passed": score >= 0.6,
        "results": results,
        "knowledge_gaps": knowledge_gaps
    }


def generate_proficiency_assessment(
    topic: str,
    num_questions: int = 5,
    tool_context: "ToolContext" = None
) -> Dict:
    """Generate initial proficiency assessment questions for a topic.

    Creates questions to determine if a user is beginner, intermediate,
    or advanced in the given topic.

    Args:
        topic: The learning topic to assess
        num_questions: Number of assessment questions (default 5)
        tool_context: ADK tool context for state access (optional)

    Returns:
        dict with:
        - 'topic': str the topic being assessed
        - 'questions': list of question dicts, each with:
            - 'question': str question text
            - 'type': "multiple_choice"
            - 'options': list of option strings
            - 'difficulty': "beginner", "intermediate", or "advanced"
    """
    llm_service = _get_llm_service()
    questions = llm_service.generate_proficiency_questions(topic)

    return {
        "topic": topic,
        "questions": questions
    }


# ============= Resource Tools =============

def search_youtube(
    query: str,
    max_results: int = 5,
    tool_context: "ToolContext" = None
) -> Dict:
    """Search YouTube for educational videos.

    Searches YouTube and returns video results with direct watch URLs.
    No API key required - uses youtube-search-python library.

    Args:
        query: Search query (e.g., "Python functions tutorial", "React hooks explained")
        max_results: Maximum number of results to return (default 5, max 10)
        tool_context: ADK tool context for state access (optional)

    Returns:
        dict with:
        - 'query': str the search query used
        - 'results': list of video dicts, each with:
            - 'type': "video"
            - 'title': str video title
            - 'url': str direct YouTube watch URL (youtube.com/watch?v=...)
            - 'duration': str video duration (e.g., "10:25")
            - 'channel': str channel name
            - 'views': str view count (e.g., "1.2M views")
            - 'thumbnail': str thumbnail URL
            - 'platform': "youtube"
            - 'quality_score': float 0.0-1.0 educational quality score
        - 'total_found': int number of results returned

    Example:
        >>> search_youtube("Python list comprehension tutorial", max_results=3)
        {
            "query": "Python list comprehension tutorial",
            "results": [
                {
                    "type": "video",
                    "title": "Python List Comprehension in 5 Minutes",
                    "url": "https://www.youtube.com/watch?v=abc123",
                    "duration": "5:32",
                    "channel": "Corey Schafer",
                    "quality_score": 0.85
                },
                ...
            ],
            "total_found": 3
        }
    """
    service = _get_resource_service()
    max_results = min(max_results, 10)  # Cap at 10

    videos = service.search_youtube_videos(query, max_results=max_results)

    # Add quality scores
    for video in videos:
        video["quality_score"] = service.score_video_quality(video)

    print(f"[search_youtube] Found {len(videos)} videos for: {query}")

    return {
        "query": query,
        "results": videos,
        "total_found": len(videos)
    }


def search_web(
    query: str,
    max_results: int = 5,
    tool_context: "ToolContext" = None
) -> Dict:
    """Search the web for articles and documentation using DuckDuckGo.

    Searches the web and returns article/documentation results with direct URLs.
    No API key required - uses duckduckgo-search library.

    Args:
        query: Search query (e.g., "Python functions guide", "React useState tutorial")
        max_results: Maximum number of results to return (default 5, max 10)
        tool_context: ADK tool context for state access (optional)

    Returns:
        dict with:
        - 'query': str the search query used
        - 'results': list of article dicts, each with:
            - 'type': "article"
            - 'title': str article title
            - 'url': str direct article URL
            - 'description': str article snippet/summary
            - 'source': str domain name (e.g., "realpython.com")
            - 'platform': "web"
            - 'quality_score': float 0.0-1.0 based on source trustworthiness
        - 'total_found': int number of results returned

    Example:
        >>> search_web("Python decorators explained", max_results=3)
        {
            "query": "Python decorators explained",
            "results": [
                {
                    "type": "article",
                    "title": "Primer on Python Decorators",
                    "url": "https://realpython.com/primer-on-python-decorators/",
                    "description": "In this tutorial, you'll learn what decorators are...",
                    "source": "realpython.com",
                    "quality_score": 0.9
                },
                ...
            ],
            "total_found": 3
        }
    """
    service = _get_resource_service()
    max_results = min(max_results, 10)  # Cap at 10

    articles = service.search_articles(query, max_results=max_results)

    # Add quality scores
    for article in articles:
        article["quality_score"] = service.score_article_quality(article)

    print(f"[search_web] Found {len(articles)} articles for: {query}")

    return {
        "query": query,
        "results": articles,
        "total_found": len(articles)
    }


def browse_url(
    url: str,
    tool_context: "ToolContext" = None
) -> Dict:
    """Fetch and extract content from a URL to verify its relevance.

    Retrieves a web page and extracts its main content, title, and metadata.
    Useful for verifying that a resource is relevant and high-quality before
    including it in recommendations.

    Args:
        url: The URL to fetch and analyze
        tool_context: ADK tool context for state access (optional)

    Returns:
        dict with:
        - 'url': str the URL that was fetched
        - 'success': bool whether the fetch was successful
        - 'title': str page title
        - 'description': str meta description or first paragraph
        - 'content_preview': str first 500 chars of main content
        - 'content_type': str detected type ("article", "documentation", "video_page", "other")
        - 'word_count': int approximate word count
        - 'error': str error message if fetch failed (only if success=False)

    Example:
        >>> browse_url("https://realpython.com/python-lists/")
        {
            "url": "https://realpython.com/python-lists/",
            "success": True,
            "title": "Python Lists and Tuples",
            "description": "Learn about Python lists and tuples...",
            "content_preview": "Lists and tuples are arguably Python's most...",
            "content_type": "article",
            "word_count": 2500
        }
    """
    import httpx
    from html.parser import HTMLParser

    class SimpleHTMLParser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.title = ""
            self.description = ""
            self.in_title = False
            self.in_body = False
            self.body_text = []
            self.current_tag = ""

        def handle_starttag(self, tag, attrs):
            self.current_tag = tag
            if tag == "title":
                self.in_title = True
            elif tag == "body":
                self.in_body = True
            elif tag == "meta":
                attrs_dict = dict(attrs)
                if attrs_dict.get("name", "").lower() == "description":
                    self.description = attrs_dict.get("content", "")

        def handle_endtag(self, tag):
            if tag == "title":
                self.in_title = False
            elif tag == "body":
                self.in_body = False
            self.current_tag = ""

        def handle_data(self, data):
            if self.in_title:
                self.title += data.strip()
            elif self.in_body and self.current_tag not in ["script", "style", "noscript"]:
                text = data.strip()
                if text:
                    self.body_text.append(text)

    try:
        with httpx.Client(timeout=10.0, follow_redirects=True) as client:
            response = client.get(url, headers={
                "User-Agent": "Mozilla/5.0 (compatible; StudySync/1.0; Educational Resource Checker)"
            })
            response.raise_for_status()

        content = response.text
        parser = SimpleHTMLParser()
        parser.feed(content)

        body_content = " ".join(parser.body_text)
        word_count = len(body_content.split())
        content_preview = body_content[:500] + "..." if len(body_content) > 500 else body_content

        # Detect content type
        content_type = "other"
        url_lower = url.lower()
        if "youtube.com" in url_lower or "youtu.be" in url_lower:
            content_type = "video_page"
        elif "docs." in url_lower or "documentation" in url_lower or "/docs/" in url_lower:
            content_type = "documentation"
        elif word_count > 300:
            content_type = "article"

        description = parser.description or (body_content[:200] + "..." if len(body_content) > 200 else body_content)

        print(f"[browse_url] Successfully fetched: {url[:50]}...")

        return {
            "url": url,
            "success": True,
            "title": parser.title,
            "description": description,
            "content_preview": content_preview,
            "content_type": content_type,
            "word_count": word_count
        }

    except Exception as e:
        print(f"[browse_url] Failed to fetch {url}: {e}")
        return {
            "url": url,
            "success": False,
            "title": "",
            "description": "",
            "content_preview": "",
            "content_type": "unknown",
            "word_count": 0,
            "error": str(e)
        }


def filter_resources_by_quality(
    resources: List[Dict],
    min_quality_score: float = 0.5,
    resource_type: str = None,
    tool_context: "ToolContext" = None
) -> Dict:
    """Filter a list of resources by quality score and optionally by type.

    Takes a list of resources (videos or articles) and filters them based
    on their quality scores. Useful for ensuring only high-quality resources
    are included in recommendations.

    Args:
        resources: List of resource dicts (from search_youtube or search_web)
        min_quality_score: Minimum quality score to include (0.0-1.0, default 0.5)
        resource_type: Optional filter by type ("video" or "article")
        tool_context: ADK tool context for state access (optional)

    Returns:
        dict with:
        - 'filtered': list of resources meeting the criteria
        - 'removed_count': int number of resources filtered out
        - 'average_quality': float average quality score of filtered results

    Example:
        >>> results = search_youtube("Python tutorial")
        >>> filter_resources_by_quality(results["results"], min_quality_score=0.7)
        {
            "filtered": [...],  # Only high-quality videos
            "removed_count": 2,
            "average_quality": 0.82
        }
    """
    filtered = []

    for resource in resources:
        # Check quality score
        quality = resource.get("quality_score", 0.5)
        if quality < min_quality_score:
            continue

        # Check type if specified
        if resource_type and resource.get("type") != resource_type:
            continue

        filtered.append(resource)

    removed_count = len(resources) - len(filtered)
    avg_quality = sum(r.get("quality_score", 0.5) for r in filtered) / len(filtered) if filtered else 0

    print(f"[filter_resources_by_quality] Kept {len(filtered)}/{len(resources)} resources (min_score={min_quality_score})")

    return {
        "filtered": filtered,
        "removed_count": removed_count,
        "average_quality": round(avg_quality, 2)
    }


# Legacy function for backward compatibility with runner.py
def find_session_resources(
    main_topic: str,
    session_topic: str,
    num_videos: int = 2,
    num_articles: int = 1,
    tool_context: "ToolContext" = None
) -> Dict:
    """Find learning resources for a study session (legacy convenience function).

    This is a convenience function that combines search_youtube and search_web.
    For more control, use the individual tools directly.

    Args:
        main_topic: Main learning topic (e.g., "Python")
        session_topic: Specific session topic (e.g., "Python Functions")
        num_videos: Number of videos to find (default 2)
        num_articles: Number of articles to find (default 1)
        tool_context: ADK tool context for state access (optional)

    Returns:
        dict with 'videos' and 'articles' lists
    """
    # Search for videos
    video_results = search_youtube(f"{session_topic} tutorial", max_results=num_videos + 2)
    videos = video_results.get("results", [])
    quality_videos = [v for v in videos if v.get("quality_score", 0) >= 0.4]
    final_videos = quality_videos[:num_videos] if quality_videos else videos[:num_videos]

    # Search for articles
    article_results = search_web(f"{session_topic} guide tutorial", max_results=num_articles + 2)
    articles = article_results.get("results", [])
    quality_articles = [a for a in articles if a.get("quality_score", 0) >= 0.3]
    final_articles = quality_articles[:num_articles] if quality_articles else articles[:num_articles]

    return {
        "videos": final_videos,
        "articles": final_articles
    }
