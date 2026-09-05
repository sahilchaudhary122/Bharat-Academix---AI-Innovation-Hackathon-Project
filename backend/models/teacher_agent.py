from pydantic import BaseModel
from typing import Optional


class TeacherAgentRequest(BaseModel):
    student_id: str
    language: Optional[str] = None
    difficulty: Optional[str] = None