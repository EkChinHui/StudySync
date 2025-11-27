# StudySync Demo Video Script
**Target Duration: 2:30 - 2:45**

---

## INTRO (0:00 - 0:10)
**[VISUAL: StudySync logo/title card]**

> "Hi, I'm [Your Name], and this is StudySync—an AI-powered learning system that creates personalized study plans using multiple collaborating agents."

---

## PROBLEM STATEMENT (0:10 - 0:40)
**[VISUAL: Show statistics, frustrated learner stock imagery, or screen recordings of overwhelming search results]**

> "Here's a problem: 70% of online learners never finish their courses. And for working professionals? It's even worse.
>
> Why? Because learning today is broken. Search 'learn Python' and you get millions of results. Which ones are good? Which match YOUR level?
>
> Generic courses don't adapt to what you already know. They don't fit your schedule. And without structure, it's easy to give up.
>
> Working professionals need something different—a personal learning architect that understands their level, respects their time, and keeps them on track."

---

## WHY AGENTS? (0:40 - 1:05)
**[VISUAL: Show the architecture diagram with agents highlighted as you mention each one]**

> "This isn't a single-prompt problem. Creating a great learning experience requires MULTIPLE types of expertise:
>
> - Assessing what you already know
> - Designing a curriculum that builds logically
> - Scheduling sessions that fit your life
> - Finding quality resources—real videos and articles
> - And testing your understanding along the way
>
> No single AI prompt does all of this well. So I built a team of specialized agents, each an expert in one area, coordinated by an orchestrator.
>
> Think of it like having a team of tutors—a curriculum designer, a scheduler, a resource curator, and a quiz master—all working together just for you."

---

## ARCHITECTURE (1:05 - 1:30)
**[VISUAL: Animated or static architecture diagram showing the flow]**

> "Here's how it works:
>
> The **Orchestrator** coordinates everything. First, the **User Profiler Agent** assesses your proficiency and availability.
>
> Then, the **Curriculum Agent** generates a structured learning path tailored to your level.
>
> Next, the **Scheduler Agent** creates a realistic study schedule.
>
> Finally—and this is key—the **Assessment Agent** and **Resources Collator** run in PARALLEL, generating quizzes and finding real YouTube videos and articles simultaneously.
>
> Each agent has custom tools. The profiler has three tools, the curriculum agent has three, assessments has three, and resources has three more. Fifteen tools total, all working together."

---

## DEMO (1:30 - 2:15)
**[VISUAL: Screen recording of the actual application]**

> "Let me show you.
>
> **[Screen: Onboarding page]**
> I enter my topic—let's say 'Machine Learning.'
>
> **[Screen: Assessment questions]**
> StudySync asks me a few questions to gauge my level. I select 'Intermediate' and answer the proficiency questions.
>
> **[Screen: Commitment selection with dates]**
> Then I set my schedule—I'll choose 'Moderate' commitment, starting next week.
>
> **[Screen: Progress messages appearing in real-time]**
> Now watch the agents work. You can see real-time updates: 'Analyzing profile...' 'Generating curriculum...' 'Creating schedule...' 'Finding resources...'
>
> **[Screen: Dashboard]**
> And here's my personalized dashboard. Four modules, fifteen study sessions, all scheduled around my availability.
>
> **[Screen: Session detail with resources]**
> Each session has curated resources—actual YouTube tutorials and articles, not search links.
>
> **[Screen: Quiz page]**
> And module quizzes to test my understanding and track progress."

---

## THE BUILD (2:15 - 2:35)
**[VISUAL: Tech stack logos or code snippets]**

> "I built this with:
> - **Google ADK** for the agent framework
> - **LiteLLM** for model flexibility—supporting both OpenAI and Anthropic
> - **FastAPI** for the backend with real-time SSE streaming
> - **React and TypeScript** for the frontend
> - And **SQLite** for persistence
>
> The agents use the ADK's sub-agent delegation pattern, with InMemorySessionService for state management across the workflow."

---

## CLOSING (2:35 - 2:45)
**[VISUAL: Return to dashboard or logo]**

> "StudySync shows how multi-agent systems can solve real problems in education—creating personalized learning experiences that were previously only available through expensive private tutoring.
>
> Thanks for watching!"

---

## PRODUCTION NOTES

### Visuals to Prepare:
1. **Title card** with StudySync logo
2. **Problem section**: Stock footage of overwhelmed learner, or screen recording scrolling through YouTube/Google search results
3. **Architecture diagram**: The ASCII diagram from the writeup, converted to a clean graphic
4. **Screen recordings**:
   - Onboarding flow (topic → assessment → commitment)
   - Real-time progress messages
   - Dashboard overview
   - Session detail with resources
   - Quiz interface
5. **Tech stack**: Logos for Google ADK, FastAPI, React, TypeScript, SQLite

### Timing Tips:
- Practice reading aloud—aim for natural pace
- Screen recordings should show smooth, successful flows
- Have the demo pre-loaded to avoid loading delays
- Consider background music (subtle, royalty-free)

### Recording Tips:
- Use a quality microphone
- Record voiceover separately from screen capture for flexibility
- Keep demo data interesting (real topics, not "test")
- Ensure screen resolution is high and text is readable
