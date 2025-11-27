"""Assessments API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict
from datetime import datetime
import json

from backend.database import get_db
from backend.models import LearningPath, Assessment
from backend.agents.tools import generate_proficiency_assessment, evaluate_quiz_responses

router = APIRouter()


class ProficiencyAssessmentRequest(BaseModel):
    """Request to get proficiency assessment."""
    topic: str


class SubmitQuizRequest(BaseModel):
    """Request to submit quiz answers."""
    responses: Dict[str, str]  # Map of question_id to answer


@router.post("/proficiency")
async def get_proficiency_assessment_endpoint(
    request: ProficiencyAssessmentRequest
):
    """Get proficiency assessment questions for a topic."""
    try:
        result = generate_proficiency_assessment(request.topic)
        return {
            "topic": request.topic,
            "questions": result.get("questions", [])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating assessment: {str(e)}")


@router.get("/quiz/{module_id}")
async def get_module_quiz(
    module_id: str,
    learning_path_id: str,
    db: Session = Depends(get_db)
):
    """Get quiz for a specific module."""
    learning_path = db.query(LearningPath).filter(
        LearningPath.id == learning_path_id
    ).first()

    if not learning_path:
        raise HTTPException(status_code=404, detail="Learning path not found")

    # Get assessment for this module
    assessment = db.query(Assessment).filter(
        Assessment.learning_path_id == learning_path_id,
        Assessment.module_id == module_id,
        Assessment.assessment_type == "module_quiz"
    ).first()

    if not assessment:
        raise HTTPException(status_code=404, detail="Quiz not found for this module")

    questions = json.loads(assessment.questions) if assessment.questions else []

    # Get module title from curriculum
    module_title = module_id  # Default to module_id
    curriculum = json.loads(learning_path.curriculum) if learning_path.curriculum else {}
    for module in curriculum.get("modules", []):
        if module.get("module_id") == module_id:
            module_title = module.get("title", module_id)
            break

    return {
        "assessment_id": assessment.id,
        "module_id": module_id,
        "module_title": module_title,
        "questions": questions,
        "completed": assessment.completed,
        "score": assessment.score if assessment.completed else None
    }


@router.post("/quiz/{assessment_id}/submit")
async def submit_quiz(
    assessment_id: str,
    request: SubmitQuizRequest,
    db: Session = Depends(get_db)
):
    """Submit quiz responses and get evaluation."""
    # Get assessment
    assessment = db.query(Assessment).filter(
        Assessment.id == assessment_id
    ).first()

    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    # Get quiz data
    quiz_data = {
        "module_id": assessment.module_id,
        "module_title": assessment.module_id,  # Simplified for POC
        "assessment_type": assessment.assessment_type,
        "questions": json.loads(assessment.questions) if assessment.questions else []
    }

    # Evaluate quiz using tool function
    try:
        evaluation = evaluate_quiz_responses(quiz_data, request.responses)

        # Save results
        assessment.user_responses = json.dumps(request.responses)
        assessment.score = evaluation["score"]
        assessment.completed = True
        assessment.completed_at = datetime.utcnow()

        db.commit()

        return {
            "assessment_id": assessment_id,
            "score": evaluation["score"],
            "correct_count": evaluation["correct_count"],
            "total_questions": evaluation["total_questions"],
            "passed": evaluation["passed"],
            "results": evaluation["results"],
            "knowledge_gaps": evaluation.get("knowledge_gaps", [])
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error evaluating quiz: {str(e)}")
