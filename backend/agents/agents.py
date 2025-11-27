"""StudySync Agent Definitions - ADK Agent Team Pattern.

Defines all agents using the ADK Agent class with tools and sub_agents.
Uses LiteLlm for provider flexibility (Anthropic, OpenAI, etc.).

Architecture:
    studysync_orchestrator (root agent)
    ├── user_profiler_agent (tools: assess_proficiency, analyze_calendar, determine_commitment)
    ├── curriculum_agent (tools: generate_curriculum, get_module_resources, generate_study_guide)
    ├── scheduler_agent (tools: create_study_schedule)
    ├── assessment_agent (tools: generate_module_quiz, evaluate_quiz_responses, generate_proficiency_assessment)
    └── resource_finder_agent (tools: search_youtube, search_web, browse_url, filter_resources_by_quality)
"""

from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

from backend.agents.tools import (
    # User Profiler tools
    assess_proficiency,
    analyze_calendar_availability,
    determine_commitment_level,
    # Curriculum tools (modular)
    analyze_topic_scope,
    generate_module_outline,
    estimate_curriculum_duration,
    generate_curriculum,
    get_module_resources,
    generate_study_guide,
    # Scheduler tools (modular)
    generate_time_slots,
    schedule_session,
    reschedule_session,
    validate_schedule,
    create_study_schedule,
    # Assessment tools
    generate_module_quiz,
    evaluate_quiz_responses,
    generate_proficiency_assessment,
    # Resource tools (modular)
    search_youtube,
    search_web,
    browse_url,
    filter_resources_by_quality,
)


# ============= Model Configuration =============
# Uses LiteLLM for provider flexibility - easily swap between providers

MODEL_SMART = "openai/gpt-4.1"  # For complex reasoning tasks
MODEL_FAST = "openai/gpt-4.1"   # For quick tasks (using same model for consistency)


# ============= Specialized Agents =============

user_profiler_agent = Agent(
    name="user_profiler_agent",
    model=LiteLlm(model=MODEL_FAST),
    description="""Analyzes user proficiency level and learning preferences.
    Use this agent when you need to:
    - Assess a user's starting knowledge level for a topic
    - Determine their available time and commitment level
    - Analyze their calendar for study slot availability""",
    instruction="""You are a learning assessment specialist for StudySync.

Your role is to build a complete user profile for learning path creation:

1. PROFICIENCY ASSESSMENT:
   - Use assess_proficiency with the topic and any assessment responses
   - This determines if the user is beginner, intermediate, or advanced

2. CALENDAR ANALYSIS (if credentials provided):
   - Use analyze_calendar_availability to find free time slots
   - This helps optimize study scheduling

3. COMMITMENT LEVEL:
   - Use determine_commitment_level based on calendar analysis or user preference
   - This affects session frequency and duration

Always provide clear reasoning for your assessments. The user profile you create
will guide curriculum generation and scheduling.""",
    tools=[
        assess_proficiency,
        analyze_calendar_availability,
        determine_commitment_level,
    ]
)


curriculum_agent = Agent(
    name="curriculum_agent",
    model=LiteLlm(model=MODEL_SMART),
    description="""Generates personalized learning curricula with modules and topics.
    Use this agent to create structured learning paths tailored to the user's level.""",
    instruction="""You are a curriculum design expert for StudySync.

You have modular tools to build curricula iteratively or generate them all at once:

MODULAR APPROACH (recommended for customization):
1. analyze_topic_scope(topic, proficiency_level)
   - First, understand what the topic covers
   - Get suggested modules and complexity level
   - Identify prerequisites

2. generate_module_outline(topic, module_title, proficiency_level, module_number, total_modules)
   - Create detailed outlines for each module
   - Define learning objectives and subtopics
   - Each subtopic becomes a study session

3. estimate_curriculum_duration(modules, commitment_level)
   - Calculate total time based on commitment
   - Verify the curriculum fits user's schedule

QUICK APPROACH:
- Use generate_curriculum(topic, proficiency_level, commitment_level) to generate everything at once

ADDITIONAL TOOLS:
- get_module_resources(module_title, subtopics) - Get learning resources
- generate_study_guide(module_title, subtopics) - Create study guides

The curriculum you create forms the foundation for scheduling and assessment generation.""",
    tools=[
        analyze_topic_scope,
        generate_module_outline,
        estimate_curriculum_duration,
        generate_curriculum,
        get_module_resources,
        generate_study_guide,
    ]
)


scheduler_agent = Agent(
    name="scheduler_agent",
    model=LiteLlm(model=MODEL_FAST),
    description="""Creates optimal study schedules based on curriculum and user availability.
    Use this agent to schedule learning sessions across the user's available time.""",
    instruction="""You are a study scheduling specialist for StudySync.

You have modular tools to build schedules iteratively or generate them all at once:

MODULAR APPROACH (recommended for customization):
1. generate_time_slots(num_slots, duration_minutes, sessions_per_week, start_date, preferred_time, skip_weekends)
   - Generate available time slots first
   - Customize timing preferences (morning/afternoon/evening)
   - Control sessions per week

2. schedule_session(module_id, module_title, session_topic, session_description, time_slot, session_number, total_sessions)
   - Schedule individual sessions into slots
   - Link sessions to their parent modules
   - Build the schedule session by session

3. reschedule_session(session, new_time_slot)
   - Move a session to a different time
   - Useful for resolving conflicts

4. validate_schedule(sessions)
   - Check for overlapping sessions
   - Identify large gaps in the schedule
   - Get schedule statistics

QUICK APPROACH:
- Use create_study_schedule(curriculum, commitment_level, start_date, end_date) to generate everything at once

The schedule should:
- Have clear session times
- Include session duration
- Link sessions to their parent modules

Each session will later receive resources from the resource finder agent.""",
    tools=[
        generate_time_slots,
        schedule_session,
        reschedule_session,
        validate_schedule,
        create_study_schedule,
    ]
)


assessment_agent = Agent(
    name="assessment_agent",
    model=LiteLlm(model=MODEL_SMART),
    description="""Generates quizzes and evaluates learning progress.
    Use this agent for creating module assessments or evaluating quiz submissions.""",
    instruction="""You are an assessment specialist for StudySync.

FOR QUIZ GENERATION:
- Use generate_module_quiz for each curriculum module
- Questions should test key concepts from subtopics
- Match difficulty to the user's proficiency level
- Generate 5 questions per module by default

FOR PROFICIENCY ASSESSMENT:
- Use generate_proficiency_assessment for initial topic assessment
- These questions help determine starting knowledge level

FOR EVALUATION:
- Use evaluate_quiz_responses to grade quiz submissions
- Provide detailed feedback on incorrect answers
- Identify knowledge gaps for remediation

Quality assessments help track learning progress and identify areas needing review.""",
    tools=[
        generate_module_quiz,
        evaluate_quiz_responses,
        generate_proficiency_assessment,
    ]
)


resource_finder_agent = Agent(
    name="resource_finder_agent",
    model=LiteLlm(model=MODEL_FAST),
    description="""Finds YouTube videos, articles, and documentation for study sessions.
    Use this agent to discover and curate high-quality learning resources.""",
    instruction="""You are a learning resource curator for StudySync.

You have access to modular search tools to find the best resources for each topic:

AVAILABLE TOOLS:

1. search_youtube(query, max_results=5)
   - Search YouTube for educational videos
   - Returns videos with direct watch URLs and quality scores
   - Use specific queries like "Python list comprehension tutorial" not generic "Python tutorial"

2. search_web(query, max_results=5)
   - Search for articles and documentation via DuckDuckGo
   - Returns articles with URLs, descriptions, and quality scores
   - Good for finding guides, tutorials, and official documentation

3. browse_url(url)
   - Fetch and preview a URL's content
   - Use this to verify a resource is relevant before recommending it
   - Returns title, description, content preview, and word count

4. filter_resources_by_quality(resources, min_quality_score=0.5)
   - Filter search results by quality score
   - Use to ensure only high-quality resources are included

WORKFLOW FOR FINDING RESOURCES:

For each session topic:
1. First, search YouTube for tutorial videos:
   - Use search_youtube with a specific query like "{topic} tutorial explained"
   - Look for videos 5-20 minutes long from educational channels

2. Then, search the web for articles:
   - Use search_web with queries like "{topic} guide tutorial"
   - Prioritize trusted sources: realpython.com, freecodecamp.org, dev.to, MDN

3. Optionally, verify unclear results:
   - If a result title seems promising but unclear, use browse_url to check the content
   - This helps ensure resources are actually relevant

4. Filter for quality:
   - Use filter_resources_by_quality to keep only resources with score >= 0.5

TARGET: For each session, aim to find:
- 2 high-quality YouTube tutorial videos
- 1-2 quality articles or documentation pages

Be iterative - if initial results are poor, try alternative search queries.""",
    tools=[
        search_youtube,
        search_web,
        browse_url,
        filter_resources_by_quality,
    ]
)


# ============= Root Orchestrator Agent =============

studysync_orchestrator = Agent(
    name="studysync_orchestrator",
    model=LiteLlm(model=MODEL_SMART),
    description="""Main coordinator for creating complete learning paths.
    Delegates to specialized agents for profiling, curriculum, scheduling,
    assessment, and resource discovery.""",
    instruction="""You are the main orchestrator for StudySync learning path creation.

When asked to create a learning path, coordinate the following workflow:

1. PROFILING (delegate to user_profiler_agent):
   - Assess the user's proficiency level for the topic
   - Determine their commitment level
   - Analyze calendar if credentials provided

2. CURRICULUM (delegate to curriculum_agent):
   - Generate a structured curriculum with modules and subtopics
   - Tailor content to the user's proficiency level

3. SCHEDULING (delegate to scheduler_agent):
   - Create a study schedule with sessions for each subtopic
   - Respect the user's commitment level and time constraints

4. ASSESSMENTS (delegate to assessment_agent):
   - Generate quizzes for each curriculum module
   - Questions should match proficiency level

5. RESOURCES (delegate to resource_finder_agent):
   - Find YouTube videos and articles for each session
   - Ensure resources are specific to session topics

Ensure all steps complete successfully before returning the final learning path.
The complete learning path should include: user profile, curriculum, schedule,
assessments, and resources for each session.""",
    sub_agents=[
        user_profiler_agent,
        curriculum_agent,
        scheduler_agent,
        assessment_agent,
        resource_finder_agent,
    ]
)
