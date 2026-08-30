from pydantic import BaseModel
class StudentCreate(BaseModel):
    name: str
    grade: str
    preferred_language: str = "English"
    current_level: str = "beginner"
    learning_goals: str | None = None

class StudentResponse(BaseModel):
    id: str
    name: str
    grade: str
    preferred_language: str
    current_level: str
    learning_goals: str | None