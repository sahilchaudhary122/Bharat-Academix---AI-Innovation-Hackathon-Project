from pydantic import BaseModel, Field
from typing import Optional


class AssessmentQuestion(BaseModel):
    question: str
    concept: str
    question_type: str
    options: Optional[list[str]] = None
    correct_answer: str
    explanation: Optional[str] = None


class FinalAssessmentRequest(BaseModel):
    student_id: str
    lesson_id: str
    subject: str
    topic: str
    number_of_questions: int = Field(
        default=5,
        ge=3,
        le=20,
    )
    language: str = "English"


class FinalAssessmentResponse(BaseModel):
    assessment_id: str
    student_id: str
    lesson_id: str
    subject: str
    topic: str
    questions: list[AssessmentQuestion]


class AssessmentAnswer(BaseModel):
    question: str
    concept: str
    student_answer: str
    correct_answer: str


class FinalAssessmentEvaluationRequest(BaseModel):
    student_id: str
    lesson_id: str
    subject: str
    topic: str
    answers: list[AssessmentAnswer]


class ConceptAssessmentResult(BaseModel):
    concept: str
    score: float = Field(ge=0, le=100)
    status: str
    misconception: Optional[str] = None


class FinalAssessmentEvaluationResponse(BaseModel):
    student_id: str
    lesson_id: str
    subject: str
    topic: str
    overall_score: float = Field(ge=0, le=100)
    status: str
    total_questions: int
    correct_answers: int
    concept_results: list[ConceptAssessmentResult]
    strengths: list[str]
    weaknesses: list[str]
    personalized_feedback: str


class AssessmentReportResponse(BaseModel):
    student_id: str
    lesson_id: str
    subject: str
    topic: str

    overall_score: float = Field(ge=0, le=100)
    status: str

    total_questions: int
    correct_answers: int

    strengths: list[str]
    weaknesses: list[str]
    misconceptions: list[str]

    concept_results: list[ConceptAssessmentResult]

    personalized_feedback: str