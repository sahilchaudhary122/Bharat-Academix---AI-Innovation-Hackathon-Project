from pydantic import BaseModel, Field
from typing import List, Optional


class LessonState(BaseModel):
    lesson_id: str
    student_id: str

    subject: str
    topic: str

    current_concept: str
    current_segment: str = "introduction"
    current_segment_index: int = Field(default=0, ge=0)

    difficulty: str = "beginner"

    attempts: int = 0
    correct_attempts: int = 0

    mastery_score: float = Field(default=0, ge=0, le=100)

    misconceptions: List[str] = []

    last_action: Optional[str] = None

    completed: bool = False
