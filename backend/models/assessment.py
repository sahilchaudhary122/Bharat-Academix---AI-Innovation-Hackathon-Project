from pydantic import BaseModel
from typing import Optional

class AssessmentRequest(BaseModel):
    student_id: str
    lesson_id: Optional[str] = None
    subject: str
    topic: str
    question: str
    student_answer: Optional[str] = None
    correct_answer: Optional[str] = None
    is_correct: Optional[bool] = None
    score: Optional[float] = None
    feedback: Optional[str] = None
    misconception: Optional[str] = None

class AssessmentResponse(BaseModel):
    id: str
    student_id: str
    lesson_id: Optional[str] = None
    subject: str
    topic: str
    question: str
    student_answer: Optional[str] = None
    correct_answer: Optional[str] = None
    is_correct: Optional[bool] = None
    score: Optional[float] = None
    feedback: Optional[str] = None
    misconception: Optional[str] = None