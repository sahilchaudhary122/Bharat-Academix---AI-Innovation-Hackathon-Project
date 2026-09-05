from pydantic import BaseModel
from typing import Optional


class ProgressRequest(BaseModel):
    student_id: str
    subject: str
    topic: str
    mastery_score: float = 0
    status: str = "learning"
    strengths: Optional[str] = None
    weaknesses: Optional[str] = None


class ProgressResponse(BaseModel):
    id: str
    student_id: str
    subject: str
    topic: str
    mastery_score: float
    status: str
    strengths: Optional[str] = None
    weaknesses: Optional[str] = None
    last_assessed_at: Optional[str] = None


class ConceptProgressItem(BaseModel):
    concept: str
    attempts: int
    correct_attempts: int
    mastery_score: float
    status: str
    misconceptions: list[str] = []


class LessonConceptProgressResponse(BaseModel):
    lesson_id: str
    student_id: str
    total_concepts: int
    total_attempted_concepts: int
    mastered_concepts: int
    learning_concepts: int
    not_started_concepts: int
    average_mastery: float
    concepts: list[ConceptProgressItem]