"""SQLAlchemy database models for StudySync."""

from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from backend.database import Base


def generate_uuid():
    """Generate UUID as string."""
    return str(uuid.uuid4())


class User(Base):
    """User model."""
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=True)
    google_calendar_token = Column(Text, nullable=True)  # Encrypted JSON
    google_refresh_token = Column(Text, nullable=True)
    preferences = Column(Text, nullable=True)  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    learning_paths = relationship("LearningPath", back_populates="user")


class LearningPath(Base):
    """Learning path model."""
    __tablename__ = "learning_paths"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    topic = Column(String, nullable=False)
    proficiency_level = Column(String, nullable=False)  # beginner, intermediate, advanced
    commitment_level = Column(String, nullable=False)  # light, moderate, intensive
    curriculum = Column(Text, nullable=False)  # JSON string
    schedule = Column(Text, nullable=True)  # JSON string
    status = Column(String, default="active")  # active, completed, paused
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="learning_paths")
    sessions = relationship("StudySession", back_populates="learning_path")
    assessments = relationship("Assessment", back_populates="learning_path")


class StudySession(Base):
    """Study session model."""
    __tablename__ = "study_sessions"

    id = Column(String, primary_key=True, default=generate_uuid)
    learning_path_id = Column(String, ForeignKey("learning_paths.id"), nullable=False)
    module_id = Column(String, nullable=False)
    module_title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    scheduled_time = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, default=30)
    resources = Column(Text, nullable=True)  # JSON string
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)

    # Relationships
    learning_path = relationship("LearningPath", back_populates="sessions")


class Assessment(Base):
    """Assessment/Quiz model."""
    __tablename__ = "assessments"

    id = Column(String, primary_key=True, default=generate_uuid)
    learning_path_id = Column(String, ForeignKey("learning_paths.id"), nullable=False)
    module_id = Column(String, nullable=True)
    assessment_type = Column(String, nullable=False)  # proficiency, quick_check, module_quiz
    questions = Column(Text, nullable=False)  # JSON string
    user_responses = Column(Text, nullable=True)  # JSON string
    score = Column(Float, nullable=True)
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    learning_path = relationship("LearningPath", back_populates="assessments")
