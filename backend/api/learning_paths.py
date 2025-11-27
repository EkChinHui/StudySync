"""Learning Paths API endpoints."""

import asyncio
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List as ListType, Literal
import json

from backend.database import get_db
from backend.models import User, LearningPath, StudySession, Assessment
from backend.services.progress_tracker import create_progress_tracker, ProgressEvent

# Import the refactored LearningPathRunner (ADK Agent Team pattern)
from backend.agents.runner import LearningPathRunner
orchestrator = LearningPathRunner()
print("[API] Using ADK Agent Team orchestrator")

from datetime import datetime

router = APIRouter()


class CreateLearningPathRequest(BaseModel):
    """Request to create a learning path."""
    topic: str
    assessment_responses: Optional[ListType[dict]] = None
    use_calendar: bool = False
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    commitment_level: Optional[Literal["light", "moderate", "intensive"]] = None
    proficiency_level: Optional[Literal["beginner", "intermediate", "advanced"]] = None


class LearningPathResponse(BaseModel):
    """Learning path response."""
    id: str
    topic: str
    proficiency_level: str
    commitment_level: str
    status: str
    curriculum: dict
    schedule: ListType[dict]
    progress: dict

    class Config:
        from_attributes = True


@router.post("", response_model=dict)
async def create_learning_path(
    request: CreateLearningPathRequest,
    db: Session = Depends(get_db)
):
    """
    Create a new learning path using the multi-agent system.
    This endpoint orchestrates all agents to generate curriculum, schedule, and assessments.
    """
    try:
        # For POC: Create a demo user if none exists
        demo_user = db.query(User).filter(User.email == "demo@studysync.com").first()
        if not demo_user:
            demo_user = User(email="demo@studysync.com", hashed_password="demo")
            db.add(demo_user)
            db.commit()
            db.refresh(demo_user)

        # Run orchestrator to create complete learning path
        learning_path_data = await orchestrator.create_learning_path(
            topic=request.topic,
            calendar_credentials=None,
            assessment_responses=request.assessment_responses,
            start_date=request.start_date,
            end_date=request.end_date,
            commitment_level=request.commitment_level,
            proficiency_level=request.proficiency_level
        )

        # Save to database
        learning_path = LearningPath(
            user_id=demo_user.id,
            topic=request.topic,
            proficiency_level=learning_path_data["user_profile"]["proficiency_level"],
            commitment_level=learning_path_data["user_profile"]["commitment_level"],
            curriculum=json.dumps(learning_path_data["curriculum"]),
            schedule=json.dumps(learning_path_data["schedule"]),
            status="active"
        )

        db.add(learning_path)
        db.commit()
        db.refresh(learning_path)

        # Create study sessions
        for session_data in learning_path_data["schedule"]:
            # Parse scheduled_time string to datetime object
            scheduled_time = datetime.fromisoformat(session_data["scheduled_time"])
            
            session = StudySession(
                learning_path_id=learning_path.id,
                module_id=session_data["module_id"],
                module_title=session_data["module_title"],
                session_topic=session_data.get("session_topic"),
                description=session_data.get("session_description") or session_data.get("description"),
                learning_objectives=json.dumps(session_data.get("learning_objectives", [])),
                scheduled_time=scheduled_time,
                duration_minutes=session_data["duration_minutes"],
                resources=json.dumps(session_data.get("resources", [])),
                session_number=session_data.get("session_number")
            )
            db.add(session)

        # Create assessments (with error handling for malformed quizzes)
        for assessment_data in learning_path_data["assessments"]:
            try:
                assessment = Assessment(
                    learning_path_id=learning_path.id,
                    module_id=assessment_data["module_id"],
                    assessment_type=assessment_data["assessment_type"],
                    questions=json.dumps(assessment_data["questions"])
                )
                db.add(assessment)
            except Exception as e:
                print(f"Warning: Failed to create assessment for module {assessment_data.get('module_id')}: {e}")
                # Continue with other assessments

        db.commit()
        print(f"[API] Successfully created learning path with {len(learning_path_data['schedule'])} sessions")

        # Build response carefully to avoid serialization issues
        response_data = {
            "id": learning_path.id,
            "topic": learning_path.topic,
            "message": "Learning path created successfully",
            "curriculum": learning_path_data["curriculum"],
            "schedule": learning_path_data["schedule"][:10],  # Limit to first 10 sessions for response
            "total_sessions": len(learning_path_data["schedule"]),
            "progress": learning_path_data["progress"]
        }

        print(f"[API] Returning response for learning path {learning_path.id}")
        return response_data

    except Exception as e:
        import traceback
        print(f"[API] ERROR creating learning path:")
        print(traceback.format_exc())
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating learning path: {str(e)}")


@router.get("/create/stream")
async def create_learning_path_stream(
    topic: str,
    commitment_level: str = "moderate",
    proficiency_level: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    assessment_responses: Optional[str] = None,  # JSON-encoded string
    db: Session = Depends(get_db)
):
    """
    Create a new learning path with SSE progress streaming.

    Returns Server-Sent Events with real-time progress updates during generation.
    Assessment responses should be JSON-encoded as a query parameter.
    """
    tracker = create_progress_tracker()

    # Parse assessment responses from JSON string
    parsed_responses = None
    if assessment_responses:
        try:
            parsed_responses = json.loads(assessment_responses)
        except json.JSONDecodeError:
            pass

    # For POC: Create a demo user if none exists
    demo_user = db.query(User).filter(User.email == "demo@studysync.com").first()
    if not demo_user:
        demo_user = User(email="demo@studysync.com", hashed_password="demo")
        db.add(demo_user)
        db.commit()
        db.refresh(demo_user)

    # Result container for the background task
    result_container = {"data": None, "error": None}

    async def run_orchestrator():
        """Background task to run the orchestrator."""
        try:
            await tracker.emit_progress("profiling", "Analyzing your proficiency level...")

            learning_path_data = await orchestrator.create_learning_path(
                topic=topic,
                calendar_credentials=None,
                assessment_responses=parsed_responses,
                start_date=start_date,
                end_date=end_date,
                commitment_level=commitment_level,
                proficiency_level=proficiency_level,
                progress_callback=tracker.emit_progress
            )
            result_container["data"] = learning_path_data

            # Save to database
            learning_path = LearningPath(
                user_id=demo_user.id,
                topic=topic,
                proficiency_level=learning_path_data["user_profile"]["proficiency_level"],
                commitment_level=learning_path_data["user_profile"]["commitment_level"],
                curriculum=json.dumps(learning_path_data["curriculum"]),
                schedule=json.dumps(learning_path_data["schedule"]),
                status="active"
            )

            db.add(learning_path)
            db.commit()
            db.refresh(learning_path)

            # Create study sessions
            for session_data in learning_path_data["schedule"]:
                scheduled_time = datetime.fromisoformat(session_data["scheduled_time"])
                session = StudySession(
                    learning_path_id=learning_path.id,
                    module_id=session_data["module_id"],
                    module_title=session_data["module_title"],
                    session_topic=session_data.get("session_topic"),
                    description=session_data.get("session_description") or session_data.get("description"),
                    learning_objectives=json.dumps(session_data.get("learning_objectives", [])),
                    scheduled_time=scheduled_time,
                    duration_minutes=session_data["duration_minutes"],
                    resources=json.dumps(session_data.get("resources", [])),
                    session_number=session_data.get("session_number")
                )
                db.add(session)

            # Create assessments
            for assessment_data in learning_path_data["assessments"]:
                try:
                    assessment = Assessment(
                        learning_path_id=learning_path.id,
                        module_id=assessment_data["module_id"],
                        assessment_type=assessment_data["assessment_type"],
                        questions=json.dumps(assessment_data["questions"])
                    )
                    db.add(assessment)
                except Exception as e:
                    print(f"Warning: Failed to create assessment: {e}")

            db.commit()
            print(f"[API] SSE: Successfully saved learning path {learning_path.id}")

            # Emit completion
            await tracker.emit_complete(
                "Learning path created successfully!",
                {"learning_path_id": learning_path.id}
            )

        except Exception as e:
            import traceback
            print(f"[API] SSE ERROR: {traceback.format_exc()}")
            db.rollback()
            result_container["error"] = str(e)
            await tracker.emit_error(f"Error creating learning path: {str(e)}")

    async def event_generator():
        """Generator that yields SSE events."""
        # Start orchestrator in background
        task = asyncio.create_task(run_orchestrator())

        try:
            # Stream events from tracker
            async for event in tracker.stream():
                yield f"data: {json.dumps(event.to_dict())}\n\n"

                # Stop on completion or error
                if event.type in ("complete", "error"):
                    break

        finally:
            # Ensure task is done
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            tracker.close()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.get("", response_model=ListType[dict])
async def get_learning_paths(
    db: Session = Depends(get_db)
):
    """Get all learning paths."""
    learning_paths = db.query(LearningPath).order_by(LearningPath.created_at.desc()).all()

    result = []
    for lp in learning_paths:
        result.append({
            "id": lp.id,
            "topic": lp.topic,
            "proficiency_level": lp.proficiency_level,
            "commitment_level": lp.commitment_level,
            "status": lp.status,
            "created_at": lp.created_at.isoformat()
        })

    return result


@router.get("/{learning_path_id}", response_model=dict)
async def get_learning_path(
    learning_path_id: str,
    db: Session = Depends(get_db)
):
    """Get detailed information about a learning path."""
    learning_path = db.query(LearningPath).filter(
        LearningPath.id == learning_path_id
    ).first()

    if not learning_path:
        raise HTTPException(status_code=404, detail="Learning path not found")

    # Get sessions
    sessions = db.query(StudySession).filter(
        StudySession.learning_path_id == learning_path_id
    ).order_by(StudySession.scheduled_time).all()

    sessions_data = []
    for session in sessions:
        sessions_data.append({
            "id": session.id,
            "module_id": session.module_id,
            "module_title": session.module_title,
            "session_topic": session.session_topic,
            "description": session.description,
            "learning_objectives": json.loads(session.learning_objectives) if session.learning_objectives else [],
            "scheduled_time": session.scheduled_time.isoformat(),
            "duration_minutes": session.duration_minutes,
            "session_number": session.session_number,
            "completed": session.completed,
            "resources": json.loads(session.resources) if session.resources else []
        })

    # Calculate progress
    total_sessions = len(sessions)
    completed_sessions = sum(1 for s in sessions if s.completed)

    return {
        "id": learning_path.id,
        "topic": learning_path.topic,
        "proficiency_level": learning_path.proficiency_level,
        "commitment_level": learning_path.commitment_level,
        "status": learning_path.status,
        "curriculum": json.loads(learning_path.curriculum) if learning_path.curriculum else {},
        "schedule": sessions_data,
        "progress": {
            "total_sessions": total_sessions,
            "completed_sessions": completed_sessions,
            "completion_percentage": (completed_sessions / total_sessions * 100) if total_sessions > 0 else 0
        }
    }


@router.get("/{learning_path_id}/sessions", response_model=ListType[dict])
async def get_learning_path_sessions(
    learning_path_id: str,
    db: Session = Depends(get_db)
):
    """Get all sessions for a learning path."""
    sessions = db.query(StudySession).filter(
        StudySession.learning_path_id == learning_path_id
    ).order_by(StudySession.scheduled_time).all()

    return [
        {
            "id": session.id,
            "module_id": session.module_id,
            "module_title": session.module_title,
            "session_topic": session.session_topic,
            "description": session.description,
            "learning_objectives": json.loads(session.learning_objectives) if session.learning_objectives else [],
            "scheduled_time": session.scheduled_time.isoformat(),
            "duration_minutes": session.duration_minutes,
            "session_number": session.session_number,
            "completed": session.completed,
            "resources": json.loads(session.resources) if session.resources else []
        }
        for session in sessions
    ]


@router.get("/{learning_path_id}/dashboard", response_model=dict)
async def get_dashboard(
    learning_path_id: str,
    db: Session = Depends(get_db)
):
    """Get dashboard data for a learning path."""
    learning_path = db.query(LearningPath).filter(
        LearningPath.id == learning_path_id
    ).first()

    if not learning_path:
        raise HTTPException(status_code=404, detail="Learning path not found")

    # Get sessions
    sessions = db.query(StudySession).filter(
        StudySession.learning_path_id == learning_path_id
    ).order_by(StudySession.scheduled_time).all()

    # Get all assessments for this learning path
    all_assessments = db.query(Assessment).filter(
        Assessment.learning_path_id == learning_path_id,
        Assessment.assessment_type == "module_quiz"
    ).all()

    # Get completed assessments for metrics
    completed_assessments = [a for a in all_assessments if a.completed]

    # Calculate metrics
    total_sessions = len(sessions)
    completed_sessions = sum(1 for s in sessions if s.completed)
    avg_score = sum(a.score for a in completed_assessments) / len(completed_assessments) if completed_assessments else 0

    curriculum = json.loads(learning_path.curriculum) if learning_path.curriculum else {}

    # Build quiz status map by module_id
    quiz_status = {
        a.module_id: {
            "completed": a.completed,
            "score": a.score if a.completed else None
        }
        for a in all_assessments
    }

    return {
        "learning_path_id": learning_path.id,
        "topic": learning_path.topic,
        "progress": {
            "completion_percentage": (completed_sessions / total_sessions * 100) if total_sessions > 0 else 0,
            "sessions_completed": completed_sessions,
            "total_sessions": total_sessions,
            "average_quiz_score": round(avg_score, 2),
            "quizzes_taken": len(completed_assessments)
        },
        "curriculum": curriculum,
        "quiz_status": quiz_status,
        "upcoming_sessions": [
            {
                "id": s.id,
                "module_title": s.module_title,
                "session_topic": s.session_topic,
                "scheduled_time": s.scheduled_time.isoformat(),
                "duration_minutes": s.duration_minutes
            }
            for s in sessions if not s.completed
        ][:5]  # Next 5 sessions
    }
