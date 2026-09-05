
from pydantic import BaseModel, Field
from typing import Optional


class EvaluateAnswerRequest(BaseModel):
    lesson_id: Optional[str] = None
    question_id: Optional[str] = None
    student_id: str
    subject: str
    topic: str
    concept: str
    question: str
    student_answer: str = Field(min_length=1)
    expected_answer: str
    document_id: Optional[str] = None
    language: Optional[str] = None


class EvaluationResult(BaseModel):
    correct: bool
    score: float = Field(ge=0, le=100)
    concept: str
    misconception: bool
    misconception_description: Optional[str] = None
    feedback: str
    next_action: str


class AdaptRequest(BaseModel):
    lesson_id: Optional[str] = None
    student_id: str
    subject: str
    topic: str
    concept: str
    question: str
    student_answer: str
    evaluation: EvaluationResult
    document_id: Optional[str] = None
    language: Optional[str] = None
    difficulty: str = "beginner"


class AdaptiveResponse(BaseModel):
    action: str
    concept: str
    strategy: str
    explanation: str
    example: Optional[str] = None
    next_question: str
    difficulty: str

class SpeechAnswerRequest(BaseModel):
    lesson_id: Optional[str] = None
    question_id: Optional[str] = None
    student_id: str
    subject: str
    topic: str
    concept: str
    question: str
    expected_answer: str
    input_file: str
    document_id: Optional[str] = None
    language: Optional[str] = None
    difficulty: str = "beginner"


class SpeechAnswerResponse(BaseModel):
    transcription: str
    evaluation: EvaluationResult
    adaptive_response: Optional[AdaptiveResponse] = None