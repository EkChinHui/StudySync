"""StudySync agents package.

Exports agent definitions and runner for learning path creation.

Architecture (ADK Agent Team Pattern):
    studysync_orchestrator (root agent)
    ├── user_profiler_agent
    ├── curriculum_agent
    ├── scheduler_agent
    ├── assessment_agent
    └── resource_finder_agent

Usage:
    from backend.agents import LearningPathRunner

    runner = LearningPathRunner()
    learning_path = await runner.create_learning_path(topic="Python programming")
"""

from backend.agents.agents import (
    user_profiler_agent,
    curriculum_agent,
    scheduler_agent,
    assessment_agent,
    resource_finder_agent,
    studysync_orchestrator,
)
from backend.agents.runner import LearningPathRunner

# Also export commonly used tools for direct access
from backend.agents.tools import (
    assess_proficiency,
    generate_curriculum,
    create_study_schedule,
    generate_module_quiz,
    evaluate_quiz_responses,
    generate_proficiency_assessment,
    find_session_resources,
)

__all__ = [
    # Agents
    "user_profiler_agent",
    "curriculum_agent",
    "scheduler_agent",
    "assessment_agent",
    "resource_finder_agent",
    "studysync_orchestrator",
    # Runner
    "LearningPathRunner",
    # Commonly used tools
    "assess_proficiency",
    "generate_curriculum",
    "create_study_schedule",
    "generate_module_quiz",
    "evaluate_quiz_responses",
    "generate_proficiency_assessment",
    "find_session_resources",
]
