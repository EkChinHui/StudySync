# StudySync - AI-Powered Learning System

A lightweight multi-agent learning system for working professionals, featuring personalized curriculum generation, intelligent scheduling, and adaptive assessments.

## Features

- **Multi-Agent Architecture**: Coordinated AI agents for profiling, curriculum generation, scheduling, and assessments
- **Personalized Learning**: Adaptive curriculum based on proficiency level and commitment
- **Smart Scheduling**: Automated study session scheduling with calendar integration support
- **Progress Tracking**: Dashboard with completion metrics and upcoming sessions
- **AI-Generated Content**: Custom quizzes and study materials powered by Anthropic Claude

## Demo Video

https://github.com/user-attachments/assets/5bb6d0c7-7ab4-4427-9c4d-d39e6aa58ea9

## Technology Stack

### Backend
- **Python 3.12+** with `uv` package manager
- **FastAPI** for REST API
- **SQLite** for database (lightweight POC)
- **Google ADK** for multi-agent orchestration
- **Anthropic Claude** for LLM-powered content generation
- **SQLAlchemy** for ORM

### Frontend
- **React 18** with TypeScript
- **Vite** for build tooling
- **Tailwind CSS** for styling
- **React Router** for navigation
- **Axios** for API calls

## Architecture

```
StudySync/
├── backend/
│   ├── agents/              # Multi-agent system
│   │   ├── runner.py        # Orchestrates all agents
│   │   ├── agents.py        # Agent definitions
│   │   └── tools.py         # Agent tools
│   ├── api/                 # FastAPI endpoints
│   │   ├── auth.py
│   │   ├── learning_paths.py
│   │   ├── schedule.py
│   │   └── assessments.py
│   ├── services/
│   │   ├── llm_service.py
│   │   └── resource_discovery_service.py
│   ├── models.py            # SQLAlchemy models
│   ├── database.py          # DB connection
│   ├── config.py            # Configuration
│   └── main.py              # FastAPI app
├── frontend/
│   └── src/
│       ├── pages/           # React pages
│       ├── components/      # Reusable components
│       ├── api/             # API client
│       └── types/           # TypeScript types
└── pyproject.toml
```

## Getting Started

### Prerequisites

- Python 3.12+
- Node.js 20+
- npm or yarn
- Anthropic API key (for Claude)

### Backend Setup

1. **Navigate to project root**:
   ```bash
   cd StudySync
   ```

2. **Set up environment variables**:
   ```bash
   cp backend/.env.example backend/.env
   # Edit backend/.env and add your API keys:
   # - ANTHROPIC_API_KEY
   # - SECRET_KEY (generate a secure random string)
   # - Google OAuth credentials (optional for POC)
   ```

3. **Run the backend**:
   ```bash
   # From project root
   ./run_backend.sh

   # OR use direct command:
   uv run uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
   ```

   The API will be available at `http://localhost:8000`
   - API Docs: `http://localhost:8000/docs`
   - Health Check: `http://localhost:8000/health`

### Frontend Setup

1. **Navigate to frontend directory**:
   ```bash
   cd frontend
   ```

2. **Start the development server**:
   ```bash
   npm run dev
   ```

   The frontend will be available at `http://localhost:5173`

## Usage

### 1. Register/Login
- Visit `http://localhost:5173`
- Create a new account or login

### 2. Create Learning Path
- Enter a topic you want to learn (e.g., "Python Programming")
- Complete the 5-question proficiency assessment
- Select your commitment level (Light/Moderate/Intensive)
- Wait while AI agents create your personalized curriculum

### 3. Dashboard
- View your learning progress
- See upcoming study sessions
- Explore the generated curriculum modules
- Download schedule as .ics file for calendar import

### 4. Study Sessions
- Click on an upcoming session to view resources
- Complete the session and add notes
- Mark as complete when finished

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user
- `POST /api/auth/calendar/connect` - Connect Google Calendar

### Learning Paths
- `POST /api/learning-paths` - Create learning path (triggers multi-agent workflow)
- `GET /api/learning-paths` - Get user's learning paths
- `GET /api/learning-paths/{id}` - Get specific learning path
- `GET /api/learning-paths/{id}/dashboard` - Get dashboard data

### Assessments
- `POST /api/assessments/proficiency` - Get proficiency assessment
- `GET /api/assessments/quiz/{module_id}` - Get module quiz
- `POST /api/assessments/quiz/{id}/submit` - Submit quiz answers

### Schedule
- `GET /api/schedule/{learning_path_id}/ics` - Download .ics file
- `GET /api/schedule/sessions/{id}` - Get session details
- `POST /api/schedule/sessions/{id}/complete` - Mark session complete

## Multi-Agent Workflow

When a user creates a learning path, the following agents are orchestrated:

1. **User Profiler Agent**
   - Analyzes proficiency assessment responses
   - Determines user level (beginner/intermediate/advanced)
   - Calculates commitment level from available time

2. **Curriculum Agent**
   - Generates curriculum structure using Claude LLM
   - Finds learning resources for each module
   - Creates study guides when resources are unavailable

3. **Scheduler Agent**
   - Creates optimal study schedule based on commitment
   - Finds free time slots (with optional Google Calendar integration)
   - Distributes modules across weeks

4. **Assessment Agent**
   - Generates quizzes for each module
   - Evaluates user responses
   - Identifies knowledge gaps

5. **Orchestrator Agent**
   - Coordinates all agents sequentially
   - Manages error handling and fallbacks
   - Compiles complete learning path

## Configuration

### Backend Configuration (backend/.env)

```env
# Application
DEBUG=True

# Database
DATABASE_URL=sqlite:///./studysync.db

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Anthropic Claude API
ANTHROPIC_API_KEY=your-anthropic-key

# Google OAuth (Optional)
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret

# YouTube Data API (Optional)
YOUTUBE_API_KEY=your-youtube-key
```

## Troubleshooting

### Backend won't start
- Check if port 8000 is available
- Verify ANTHROPIC_API_KEY is set in .env
- Run `uv sync` to ensure dependencies are installed

### Frontend won't build
- Clear node_modules: `rm -rf node_modules && npm install`
- Check Node.js version (should be 20+)
- Verify backend is running on port 8000

### Agent workflow fails
- Check API key limits for Anthropic
- Review backend logs for errors
- Ensure database file has write permissions

### Database errors
- Delete studysync.db to reset: `rm backend/studysync.db`
- Backend will recreate on next startup

## License

This project is for educational and demonstration purposes.

---

**Built for working professionals who want to learn efficiently**
