from pydantic import BaseModel, Field
from typing import Optional


class StudentCreate(BaseModel):
    name: str
    grade: str
    preferred_language: str = "English"
    current_level: str = "beginner"
    learning_goals: Optional[str] = None

    teaching_style: str = "balanced"
    available_time: Optional[int] = Field(
        default=None,
        gt=0,
        le=180,
    )
    desired_depth: str = "standard"


class StudentResponse(BaseModel):
    id: str
    name: str
    grade: str
    preferred_language: str
    current_level: str
    learning_goals: Optional[str] = None

    teaching_style: str
    available_time: Optional[int] = None
    desired_depth: str