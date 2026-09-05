from fastapi import APIRouter, HTTPException, Depends

from models.student import StudentCreate, StudentResponse
from database.supabase_client import supabase
from api.dependencies import get_current_user, get_current_student


router = APIRouter(
    prefix="/api/students",
    tags=["Students"],
)


@router.post("", response_model=StudentResponse)
def create_student(student: StudentCreate, user = Depends(get_current_user)):
    try:
        student_data = student.model_dump()
        student_data["user_id"] = user.id
        response = (
            supabase
            .table("students")
            .insert(student_data)
            .execute()
        )

        if not response.data:
            raise HTTPException(
                status_code=500,
                detail="Failed to create student.",
            )

        return response.data[0]

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create student: {str(exc)}",
        )


@router.get("/{student_id}", response_model=StudentResponse)
def get_student(student: dict = Depends(get_current_student)):
    return student