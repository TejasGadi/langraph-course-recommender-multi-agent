from typing import List, Optional, Dict
from pydantic import BaseModel

class StudentProfile(BaseModel):
    name: str
    educational_level: str
    age: int
    course_interests: List[str]
    course_mode: str  # online/offline/hybrid/any
    daily_hours: int
    preferred_timing: str  # morning, afternoon, evening
    max_duration_months: int
    language: List[str] = ["English"]
    certification_needed: bool = False
    location_preference: str = "any"  # online, offline, hybrid, any