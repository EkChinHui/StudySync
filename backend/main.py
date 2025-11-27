"""FastAPI main application for StudySync backend."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.database import init_db
from backend.api import auth, learning_paths, schedule, assessments

# Create FastAPI app
app = FastAPI(
    title="StudySync API",
    description="Multi-agent learning system for working professionals",
    version="1.0.0"
)

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database tables on startup."""
    init_db()
    print("Database initialized!")

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(learning_paths.router, prefix="/api/learning-paths", tags=["Learning Paths"])
app.include_router(schedule.router, prefix="/api/schedule", tags=["Schedule"])
app.include_router(assessments.router, prefix="/api/assessments", tags=["Assessments"])

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to StudySync API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
