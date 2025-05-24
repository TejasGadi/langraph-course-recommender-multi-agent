"""Base Pydantic models for the Course Recommendation System."""

from typing import List, Dict, Optional
from pydantic import BaseModel, Field

class CourseMetadata(BaseModel):
    """Model for course metadata."""
    title: str = Field(..., description="Name of the course")
    provider: str = Field(..., description="Platform or institution")
    duration: str = Field(..., description="Total length (e.g., 6 months)")
    daily_commitment: str = Field(..., description="e.g., 2 hours/day")
    start_date: str = Field(..., description="When it begins")
    schedule: str = Field(..., description="Time of day (e.g., evening)")
    mode: str = Field(..., description="Online / Offline / Hybrid")
    language: str = Field(..., description="Medium of instruction")
    prerequisites: List[str] = Field(default_factory=list, description="Required skills/knowledge")
    level: str = Field(..., description="Suitable academic level")
    cost: str = Field(..., description="Free or price in currency")
    certification: bool = Field(..., description="Whether certification is provided")
    career_outcomes: List[str] = Field(default_factory=list, description="Potential roles/careers after completion")

class StudentProfile(BaseModel):
    """Model for student profile."""
    education_level: str = Field(..., description="Current educational level")
    academic_background: List[str] = Field(default_factory=list, description="Previous academic experience")
    interests: List[str] = Field(default_factory=list, description="Subject interests")
    preferred_mode: str = Field(..., description="Online/Offline/Hybrid preference")
    availability: Dict[str, str] = Field(..., description="Time availability")
    career_goals: List[str] = Field(default_factory=list, description="Career aspirations")

class AgentResponse(BaseModel):
    """Model for agent responses."""
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Response message")
    data: Optional[Dict] = Field(default=None, description="Additional data")
    next_action: Optional[str] = Field(default=None, description="Next action to take")

class ConversationContext(BaseModel):
    """Model for maintaining conversation context."""
    student_profile: Optional[StudentProfile] = None
    discovered_courses: List[CourseMetadata] = Field(default_factory=list)
    validated_courses: List[CourseMetadata] = Field(default_factory=list)
    current_phase: str = Field(default="initial")
    chat_history: List[Dict[str, str]] = Field(default_factory=list)
    last_agent: Optional[str] = None 