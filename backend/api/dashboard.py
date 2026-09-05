from fastapi import APIRouter, HTTPException, Depends
from database.supabase_client import supabase
from api.dependencies import get_current_student

router = APIRouter(
    prefix="/api/students",
    tags=["Dashboard"]
)

@router.get("/{student_id}/dashboard")
def get_student_dashboard(student_id: str, student: dict = Depends(get_current_student)):

    try:
        # 1. Get student information (already provided by dependency)
        
        # 2. Get student progress
        progress_result = (
            supabase
            .table("student_progress")
            .select("*")
            .eq("student_id", student["id"])
            .execute()
        )

        # 3. Get student's lessons
        lessons_result = (
            supabase
            .table("lessons")
            .select("*")
            .eq("student_id", student["id"])
            .execute()
        )

        # 4. Get student's assessments
        assessment_result = (
            supabase
            .table("assessment_results")
            .select("*")
            .eq("student_id", student["id"])
            .execute()
        )

        # 5. Return complete dashboard
        return {
            "student": student,
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