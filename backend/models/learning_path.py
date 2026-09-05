from pydantic import BaseModel, Field
from typing import Optional


class LearningPathItem(BaseModel):
    topic: str
    reason: str
    difficulty: str
    priority: str


class LearningPathRecommendation(BaseModel):
    topic: str
    difficulty: str
    reason: str


class LearningPathResponse(BaseModel):
    student_id: str
    student_name: str
    grade: str
    learning_goal: Optional[str] = None
    current_level: str
    learning_path: list[LearningPathItem]
    next_recommendation: LearningPathRecommendation
