"""Schedule API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
import json

from backend.database import get_db
from backend.models import LearningPath, StudySession
from backend.services.calendar_service import generate_ics_file

router = APIRouter()


class SessionCompleteRequest(BaseModel):
    """Request to mark a session as complete."""
    notes: str = ""


@router.get("/{learning_path_id}/ics")
async def download_ics(
    learning_path_id: str,
    db: Session = Depends(get_db)
):
    """Download .ics file for the learning path schedule."""
    learning_path = db.query(LearningPath).filter(
        LearningPath.id == learning_path_id
    ).first()

    if not learning_path:
        raise HTTPException(status_code=404, detail="Learning path not found")

    # Get all sessions
    sessions = db.query(StudySession).filter(
        StudySession.learning_path_id == learning_path_id
    ).all()

    # Convert to dict format for ICS generation
    sessions_data = []
    for session in sessions:
        sessions_data.append({
            "module_title": session.module_title,
            "scheduled_time": session.scheduled_time.isoformat(),
            "duration_minutes": session.duration_minutes
        })

    # Generate ICS file
    ics_content = generate_ics_file(sessions_data)

    # Return as downloadable file
    return Response(
        content=ics_content,
        media_type="text/calendar",
        headers={
            "Content-Disposition": f"attachment; filename=studysync_{learning_path.topic.replace(' ', '_')}.ics"
        }
    )


@router.post("/sessions/{session_id}/complete")
async def complete_session(
    session_id: str,
    request: SessionCompleteRequest,
    db: Session = Depends(get_db)
):
    """Mark a study session as complete."""
    session = db.query(StudySession).filter(
        StudySession.id == session_id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.completed = True
    session.completed_at = datetime.utcnow()
    session.notes = request.notes

    db.commit()

    return {
        "message": "Session marked as complete",
        "session_id": session_id
    }


@router.get("/sessions/{session_id}")
async def get_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """Get details of a specific study session."""
    session = db.query(StudySession).filter(
        StudySession.id == session_id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "id": session.id,
        "module_id": session.module_id,
        "module_title": session.module_title,
        "scheduled_time": session.scheduled_time.isoformat(),
        "duration_minutes": session.duration_minutes,
        "resources": json.loads(session.resources) if session.resources else [],
        "completed": session.completed,
        "completed_at": session.completed_at.isoformat() if session.completed_at else None,
        "notes": session.notes
    }
