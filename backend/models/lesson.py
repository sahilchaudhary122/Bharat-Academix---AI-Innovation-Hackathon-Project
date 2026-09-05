from pydantic import BaseModel, Field
from typing import List, Optional

class LessonRequest(BaseModel):
    student_name: str
    grade: str
    subject: str
    topic: str
    current_level: str
    language: Optional[str] = None
    learning_goal: str
    available_time_minutes: int = Field(gt=0, le=180)

class LessonSegment(BaseModel):
    type: str
    title: str
    concept: str
    objective_index: int = Field(ge=0)
    explanation: str
    duration_minutes: int

class LessonPlan(BaseModel):
    lesson_id: str | None = None
    title: str
    subject: str
    topic: str
    difficulty: str
    language: str
    total_duration_minutes: int
    learning_objectives: List[str]
    segments: List[LessonSegment]