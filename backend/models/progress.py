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