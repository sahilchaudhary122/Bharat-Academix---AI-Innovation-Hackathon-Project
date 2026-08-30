from fastapi import APIRouter, HTTPException
from models.student import StudentCreate, StudentResponse
from database.supabase_client import supabase

router = APIRouter(
    prefix="/api/students",
    tags=["Students"]
)

@router.post("", response_model=StudentResponse)
def create_student(student: StudentCreate):

    response = (
        supabase
        .table("students")
        .insert(student.model_dump())
        .execute()
    )

    if not response.data:
        raise HTTPException(
            status_code=500,
            detail="Failed to create student"
        )

    return response.data[0]

@router.get("/{student_id}", response_model=StudentResponse)
def get_student(student_id: str):

    response = (
        supabase
        .table("students")
        .select("*")
        .eq("id", student_id)
        .single()
        .execute()
    )

    if not response.data:
        raise HTTPException(
            status_code=404,
            detail="Student not found"
        )

    return response.data