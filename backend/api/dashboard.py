from fastapi import APIRouter, HTTPException
from database.supabase_client import supabase

router = APIRouter(
    prefix="/api/students",
    tags=["Dashboard"]
)

@router.get("/{student_id}/dashboard")
def get_student_dashboard(student_id: str):

    try:
        # 1. Get student information
        student_result = (
            supabase
            .table("students")
            .select("*")
            .eq("id", student_id)
            .execute()
        )

        if not student_result.data:
            raise HTTPException(
                status_code=404,
                detail="Student not found"
            )

        # 2. Get student progress
        progress_result = (
            supabase
            .table("student_progress")
            .select("*")
            .eq("student_id", student_id)
            .execute()
        )

        # 3. Get student's lessons
        lessons_result = (
            supabase
            .table("lessons")
            .select("*")
            .eq("student_id", student_id)
            .execute()
        )

        # 4. Get student's assessments
        assessment_result = (
            supabase
            .table("assessment_results")
            .select("*")
            .eq("student_id", student_id)
            .execute()
        )

        # 5. Return complete dashboard
        return {
            "student": student_result.data[0],
            "progress": progress_result.data or [],
            "assessments": assessment_result.data or [],
            "lessons": lessons_result.data or []
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load student dashboard: {str(e)}"
        )