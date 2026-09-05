from fastapi import APIRouter, HTTPException, Depends
from models.progress import (
    ProgressRequest,
    ProgressResponse,
    LessonConceptProgressResponse,
)
from services.concept_progress_service import (
    get_lesson_progress_summary,
)
from database.supabase_client import supabase
from api.dependencies import get_current_student

router = APIRouter(
    prefix="/api/progress",
    tags=["Progress"]
)

@router.post("/{student_id}", response_model=ProgressResponse)
def create_progress(student_id: str, request: ProgressRequest, student: dict = Depends(get_current_student)):
    try:
        progress_data = request.model_dump()
        progress_data["student_id"] = student["id"]
        result = (
            supabase
            .table("student_progress")
            .insert(progress_data)
            .execute()
        )

        if not result.data:
            raise HTTPException(
                status_code=500,
                detail="Failed to create progress"
            )

        return result.data[0]

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create progress: {str(e)}"
        )

@router.get(
    "/lesson/{lesson_id}",
    response_model=LessonConceptProgressResponse,
)
def get_lesson_concept_progress(
    lesson_id: str,
    student = Depends(get_current_student),
):
    try:
        summary = get_lesson_progress_summary(
            lesson_id=lesson_id,
            student_id=student["id"],
        )

        return {
            "lesson_id": lesson_id,
            "student_id": student["id"],
            "total_concepts": summary["total_concepts"],
            "total_attempted_concepts": summary["total_attempted_concepts"],
            "mastered_concepts": summary["mastered_concepts"],
            "learning_concepts": summary["learning_concepts"],
            "not_started_concepts": summary["not_started_concepts"],
            "average_mastery": summary["average_mastery"],
            "concepts": summary["concepts"],
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve lesson concept progress: {str(e)}",
        )