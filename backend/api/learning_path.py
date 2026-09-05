from fastapi import APIRouter, HTTPException, Depends

from services.learning_path_service import generate_learning_path
from api.dependencies import get_current_student


router = APIRouter(
    prefix="/api/student",
    tags=["Learning Path"],
)


@router.get("/learning-path/{student_id}")
def get_learning_path(student_id: str, student: dict = Depends(get_current_student)):
    try:
        return generate_learning_path(student["id"])

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate learning path: {str(exc)}",
        )
