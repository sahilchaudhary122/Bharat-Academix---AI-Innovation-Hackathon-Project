from fastapi import APIRouter, HTTPException

from models.lesson import LessonRequest, LessonPlan
from services.gemini_service import create_lesson_plan


router = APIRouter(
    prefix="/api/lesson",
    tags=["Lesson"]
)


@router.post("/create", response_model=LessonPlan)
def create_lesson(request: LessonRequest):
    try:
        return create_lesson_plan(request)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create lesson: {str(e)}"
        )