# StudySync: AI-Powered Personalized Learning for Working Professionals

## Track: Agents for Good (Education)

---

## The Problem

**Self-directed learning is broken for working professionals.**

Working professionals who want to upskill face a frustrating paradox: they have access to more learning resources than ever before (YouTube tutorials, online courses, documentation, articles), yet most fail to complete their learning goals. Why?

1. **Information Overload**: Searching "learn Python" returns millions of results. Which resources are actually good? Which are appropriate for your level?

2. **No Personalization**: Generic courses teach everyone the same way, regardless of prior experience. Beginners waste time on basics they already know; advanced learners miss foundational gaps.

3. **Schedule Chaos**: Working professionals have unpredictable schedules. Static course timelines don't adapt to real-life commitments.

4. **No Accountability**: Without structured checkpoints, it's easy to abandon learning when motivation dips.

5. **Resource Fragmentation**: Quality content is scattered across platforms. Learners spend more time *finding* resources than actually *learning*.

The result? **70% of online learners never complete their courses.** For working professionals juggling careers and personal lives, this number is even higher.

---

## The Solution: StudySync

**StudySync is a multi-agent AI system that acts as your personal learning architect.**

Rather than giving you another course, StudySync creates a *complete, personalized learning experience* tailored to your knowledge level, available time, and learning goals. It combines the intelligence of multiple specialized AI agents working together to:

1. **Assess your current proficiency** through adaptive questioning
2. **Generate a custom curriculum** structured for your level
3. **Create a realistic study schedule** that fits your life
4. **Curate real learning resources** (actual YouTube videos, articles, documentation)
5. **Test your understanding** with module-specific quizzes
6. **Track your progress** and adapt as you learn

### Why Agents?

This problem is fundamentally **multi-faceted**—no single prompt or model can solve it well. Each aspect requires specialized reasoning:

- **Proficiency Assessment** needs educational psychology expertise
- **Curriculum Design** requires domain knowledge and pedagogical structure
- **Scheduling** demands constraint satisfaction and calendar awareness
- **Resource Discovery** needs web search and quality evaluation
- **Assessment Generation** requires understanding of learning objectives

By decomposing the problem into specialized agents that collaborate, StudySync achieves results that no monolithic approach could match. Each agent is an expert in its domain, and the orchestrator coordinates them into a cohesive learning experience.

---

## Architecture

### Multi-Agent System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    StudySync Orchestrator                        │
│              (Coordinates workflow, manages state)               │
└─────────────────────────────────────────────────────────────────┘
                                │
            ┌───────────────────┼───────────────────┐
            │                   │                   │
            ▼                   ▼                   ▼
    ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
    │   User       │   │  Curriculum  │   │  Scheduler   │
    │   Profiler   │   │    Agent     │   │    Agent     │
    │    Agent     │   │              │   │              │
    └──────────────┘   └──────────────┘   └──────────────┘
            │                   │                   │
            │                   │                   │
            ▼                   ▼                   ▼
    ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
    │  Assessment  │   │  Resources   │   │   Calendar   │
    │    Agent     │   │  Collator    │   │   Service    │
    │              │   │    Agent     │   │              │
    └──────────────┘   └──────────────┘   └──────────────┘
```

### Agent Descriptions

| Agent | Purpose | Tools |
|-------|---------|-------|
| **Orchestrator** | Coordinates the entire workflow, delegates to sub-agents, compiles final learning path | Sub-agent delegation |
| **User Profiler** | Assesses proficiency level, analyzes calendar availability, determines commitment capacity | `assess_proficiency`, `analyze_calendar_availability`, `determine_commitment_level` |
| **Curriculum Agent** | Generates structured learning curriculum with modules, objectives, and subtopics | `generate_curriculum`, `get_module_resources`, `generate_study_guide` |
| **Scheduler Agent** | Creates optimized study schedule respecting user constraints | `create_study_schedule` |
| **Assessment Agent** | Generates proficiency tests and module quizzes, evaluates responses | `generate_module_quiz`, `evaluate_quiz_responses`, `generate_proficiency_assessment` |
| **Resources Collator** | Finds real YouTube videos and articles with direct URLs | `search_youtube_videos`, `search_web_articles`, `find_session_resources` |

### Workflow Execution

1. **Sequential Phase**: User Profiling → Curriculum Generation → Schedule Creation
2. **Parallel Phase**: Assessment Generation ∥ Resource Discovery (run concurrently via `asyncio.gather`)

This hybrid approach ensures dependencies are respected while maximizing efficiency.

---

## Key Concepts Demonstrated

### 1. Multi-Agent System with LLM-Powered Agents

All six agents are powered by LLMs via Google ADK's `Agent` class with `LiteLlm` for model flexibility:

```python
# From backend/agents/agents.py
user_profiler_agent = Agent(
    name="user_profiler_agent",
    model=LiteLlm(model=MODEL_FAST),
    description="Analyzes user proficiency and determines optimal learning commitment level.",
    instruction="...",
    tools=[assess_proficiency, analyze_calendar_availability, determine_commitment_level]
)
```

### 2. Sequential Agent Coordination

The orchestrator follows a strict sequence where each phase depends on the previous:

```python
# From backend/agents/orchestrator.py
# Step 1: User Profiling
user_profile = await self.user_profiler.run(topic=topic, ...)

# Step 2: Curriculum Generation (depends on user_profile)
curriculum = await self.curriculum_agent.run(topic=topic, user_profile=user_profile, ...)

# Step 3: Schedule (depends on curriculum)
schedule = await self.scheduler_agent.run(curriculum=curriculum, user_profile=user_profile, ...)
```

### 3. Parallel Agent Execution

Schedule generation and assessment generation run concurrently since both only depend on the curriculum:

```python
# From backend/agents/orchestrator.py
schedule, assessments = await asyncio.gather(
    generate_schedule(),
    generate_all_assessments()
)
```

### 4. Custom Tools (15+ Tools)

Each agent has specialized tools for its domain:

- **Profiling Tools**: `assess_proficiency`, `analyze_calendar_availability`, `determine_commitment_level`
- **Curriculum Tools**: `generate_curriculum`, `get_module_resources`, `generate_study_guide`
- **Scheduling Tools**: `create_study_schedule`
- **Assessment Tools**: `generate_module_quiz`, `evaluate_quiz_responses`, `generate_proficiency_assessment`
- **Resource Tools**: `search_youtube_videos`, `search_web_articles`, `find_session_resources`

### 5. Sessions & State Management

Using ADK's `InMemorySessionService` for session management:

```python
# From backend/agents/runner.py
class LearningPathRunner:
    def __init__(self):
        self.session_service = InMemorySessionService()

    async def create_learning_path_with_agents(self, ...):
        session = await self.session_service.create_session(
            app_name=self.APP_NAME,
            user_id=user_id,
            session_id=session_id,
            state=initial_state
        )
```

State is passed through `ToolContext` and persisted across agent interactions.

### 6. Observability & Logging

Real-time progress tracking with Server-Sent Events (SSE) for frontend updates:

```python
# Progress callback system
async def emit(phase: str, message: str, data: Optional[Dict] = None):
    if progress_callback:
        await progress_callback(phase, message, data)

await emit("profiling", "Analyzing your learning profile...")
await emit("curriculum", f"Created curriculum with {len(modules)} modules", {...})
```

Comprehensive logging throughout the agent workflow:
```python
print(f"[Orchestrator] Starting user profiling for topic: {topic}")
print(f"[Orchestrator] User profile: {user_profile['proficiency_level']}")
print(f"[Orchestrator] Curriculum generated with {len(curriculum.get('modules', []))} modules")
```

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Agent Framework** | Google ADK (Agent Development Kit) |
| **LLM Provider** | OpenAI GPT-4.1 / Anthropic Claude (via LiteLLM) |
| **Backend** | Python 3.12+, FastAPI, SQLAlchemy |
| **Frontend** | React 19, TypeScript, Vite, Tailwind CSS |
| **Database** | SQLite with SQLAlchemy ORM |
| **Package Management** | uv (Python), npm (JavaScript) |

---

## Project Journey

### Challenges Faced

1. **Agent Coordination Complexity**: Ensuring agents receive the right context and produce compatible outputs required careful prompt engineering and structured tool outputs.

2. **Resource Quality**: Initial attempts to find learning resources returned search URLs instead of direct content links. Solved by implementing web scraping for YouTube and DuckDuckGo to extract actual video/article URLs.

3. **Real-Time Progress**: Users needed visibility into the multi-step generation process. Implemented SSE streaming to show progress as each agent completes its work.

4. **Schedule Optimization**: Balancing user constraints (start/end dates, commitment level) with curriculum requirements required sophisticated constraint satisfaction logic.

### What I Learned

- **Agent decomposition** is more art than science—finding the right granularity for each agent's responsibilities
- **Tool design** significantly impacts agent effectiveness—tools should be atomic and well-documented
- **State management** across agents requires careful planning to avoid context loss
- **Parallel execution** can dramatically improve UX but adds complexity to error handling

---

## Setup Instructions

### Prerequisites

- Python 3.12+
- Node.js 18+
- uv (Python package manager)
- npm

### Backend Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/studysync.git
cd studysync

# Install Python dependencies
uv sync

# Configure environment
cp backend/.env.example backend/.env
# Edit backend/.env and add your API keys:
# - OPENAI_API_KEY or ANTHROPIC_API_KEY (required)
# - SECRET_KEY (required for auth)

# Start the backend
./run_backend.sh
# Or: uv run uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The application will be available at:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

---

## Demo Walkthrough

1. **Topic Selection**: Enter a learning topic (e.g., "Python Programming")
2. **Proficiency Assessment**: Answer adaptive questions to determine your level
3. **Commitment Configuration**: Set your available time and schedule constraints
4. **Watch the Agents Work**: Real-time progress as each agent completes its task
5. **Dashboard**: View your personalized curriculum, schedule, and progress
6. **Study Sessions**: Access curated resources for each learning session
7. **Module Quizzes**: Test your understanding and track mastery

---

## Future Enhancements

- **Long-term Memory**: Persist learning patterns across sessions using Memory Bank
- **Google Calendar Integration**: Sync study sessions with user's calendar
- **Adaptive Rescheduling**: Agents that respond to missed sessions and adjust plans
- **Learning Analytics**: Deeper insights into learning patterns and effectiveness
- **Deployment**: Cloud deployment via Google Cloud Run or Agent Engine

---

## Repository Structure

```
StudySync/
├── backend/
│   ├── agents/
│   │   ├── agents.py          # Agent definitions with ADK
│   │   ├── tools.py           # 15+ custom tool functions
│   │   ├── runner.py          # High-level workflow runner
│   │   └── orchestrator.py    # Legacy orchestrator
│   ├── api/                   # FastAPI route handlers
│   ├── services/
│   │   ├── llm_service.py     # LLM integration via LiteLLM
│   │   └── resource_discovery_service.py
│   ├── models.py              # SQLAlchemy database models
│   └── main.py                # FastAPI application entry
├── frontend/
│   └── src/
│       ├── pages/             # React page components
│       └── api/               # API client
├── CLAUDE.md                  # Development instructions
└── README.md                  # This file
```

---

## Acknowledgments

Built during the **Google & Kaggle 5-Day AI Agents Intensive** (November 2025). Special thanks to the course instructors for the comprehensive introduction to agent architectures, tool design, and the Agent Development Kit.

---

## License

MIT License - See LICENSE file for details.
