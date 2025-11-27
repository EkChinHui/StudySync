# StudySync

## Problem Statement

**Self-directed learning is broken for working professionals.**

Working professionals who want to upskill face a frustrating paradox: they have access to more learning resources than ever before—YouTube tutorials, online courses, documentation, articles—yet most fail to complete their learning goals.

The challenges are clear:

- **Information Overload**: Searching "learn Python" returns millions of results. Which resources are actually good? Which are appropriate for your level?
- **No Personalization**: Generic courses teach everyone the same way. Beginners waste time on basics they already know; advanced learners miss foundational gaps.
- **Schedule Chaos**: Working professionals have unpredictable schedules. Static course timelines don't adapt to real-life commitments.
- **No Accountability**: Without structured checkpoints, it's easy to abandon learning when motivation dips.
- **Resource Fragmentation**: Quality content is scattered across platforms. Learners spend more time *finding* resources than actually *learning*.

The result? **70% of online learners never complete their courses.** For working professionals juggling careers and personal lives, this number is even higher.

---

## Why Agents?

This problem is fundamentally **multi-faceted**—no single prompt or model can solve it well. Each aspect requires specialized reasoning:

| Capability | Required Expertise |
|------------|-------------------|
| Proficiency Assessment | Educational psychology, adaptive questioning |
| Curriculum Design | Domain knowledge, pedagogical structure |
| Scheduling | Constraint satisfaction, calendar awareness |
| Resource Discovery | Web search, quality evaluation, relevance filtering |
| Assessment Generation | Learning objectives, knowledge testing |

A monolithic approach would require a single prompt to handle all of these concerns simultaneously—leading to poor results across the board.

By decomposing the problem into **specialized agents that collaborate**, StudySync achieves results that no single-prompt approach could match. Each agent is an expert in its domain, and an orchestrator coordinates them into a cohesive learning experience. This mirrors how real educational institutions work: advisors assess students, curriculum designers create courses, schedulers manage timetables, and librarians curate resources.

---

## What I Created

**StudySync is a multi-agent AI system that acts as your personal learning architect.**

Rather than giving you another course, StudySync creates a *complete, personalized learning experience* tailored to your knowledge level, available time, and learning goals.

### Architecture Overview

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
            ▼                   ▼                   ▼
    ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
    │  Assessment  │   │  Resources   │   │   Calendar   │
    │    Agent     │   │   Finder     │   │   Service    │
    └──────────────┘   └──────────────┘   └──────────────┘
```

### Agent Responsibilities

| Agent | What It Does |
|-------|--------------|
| **Orchestrator** | Coordinates the entire workflow, delegates to sub-agents, compiles final learning path |
| **User Profiler** | Assesses proficiency level through adaptive questions, analyzes availability |
| **Curriculum Agent** | Generates structured curriculum with modules, learning objectives, and subtopics |
| **Scheduler Agent** | Creates optimized study schedule respecting user constraints |
| **Assessment Agent** | Generates module quizzes, evaluates responses, tracks mastery |
| **Resources Finder** | Discovers real YouTube videos and articles, filters for quality and relevance |

### Workflow

1. **Sequential Phase**: User Profiling → Curriculum Generation → Schedule Creation
2. **Parallel Phase**: Assessment Generation and Resource Discovery run concurrently

This hybrid approach ensures dependencies are respected while maximizing efficiency.

---

## Demo

The user flow demonstrates the full agent pipeline:

1. **Topic Selection**: User enters what they want to learn (e.g., "Machine Learning")
2. **Proficiency Assessment**: Adaptive questions determine current knowledge level
3. **Commitment Configuration**: User sets available hours per week and date range
4. **Watch the Agents Work**: Real-time progress shows each agent completing its task
5. **Dashboard**: View personalized curriculum with modules and scheduled sessions
6. **Study Sessions**: Each session includes curated YouTube videos and articles
7. **Module Quizzes**: Test understanding with AI-generated assessments

---

## The Build

### Tech Stack

| Layer | Technology |
|-------|------------|
| **Agent Framework** | Google ADK (Agent Development Kit) |
| **LLM Provider** | Anthropic Claude 3.5 Sonnet (via LiteLLM) |
| **Backend** | Python 3.12, FastAPI, SQLAlchemy |
| **Frontend** | React 19, TypeScript, Vite, Tailwind CSS |
| **Database** | SQLite |

### Key Implementation Details

**Multi-Agent Coordination with ADK**
```python
user_profiler_agent = Agent(
    name="user_profiler_agent",
    model=LiteLlm(model=MODEL_FAST),
    description="Analyzes user proficiency and determines optimal learning commitment level.",
    tools=[assess_proficiency, analyze_calendar_availability, determine_commitment_level]
)
```

**15+ Custom Tools** across agents for profiling, curriculum generation, scheduling, assessment, and resource discovery.

**Real-Time Progress** via Server-Sent Events (SSE) so users see each agent's work as it happens.

**Resource Quality Filtering**: LLM-based relevance checking ensures curated resources actually match the subtopic being taught.

### Challenges Overcome

- **Resource Quality**: Initial web searches returned irrelevant results. Added LLM-based relevance filtering and domain blocklists (Wikipedia, etc.)
- **Agent Output Compatibility**: Structured tool outputs with JSON schemas ensure agents produce data the next agent can consume
- **Real-Time UX**: SSE streaming provides visibility into the multi-minute generation process

---

## If I Had More Time

- **Google Calendar Integration**: Export study sessions directly to user's calendar
- **Adaptive Rescheduling**: Agents that detect missed sessions and automatically adjust the plan
- **Learning Analytics**: Track completion rates, quiz performance trends, time spent per topic
- **Spaced Repetition**: Integrate review sessions based on forgetting curves
- **Multi-Modal Resources**: Include podcasts, interactive exercises, and practice projects
- **Deployment**: Cloud deployment via Google Cloud Run with persistent user accounts
