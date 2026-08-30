from fastapi import APIRouter, HTTPException
from models.lesson import LessonRequest, LessonPlan
from services.gemini_service import create_lesson_plan
from database.supabase_client import supabase

router = APIRouter(
    prefix="/api/lesson",
    tags=["Lesson"]
)


@router.post("/create", response_model=LessonPlan)
def create_lesson(request: LessonRequest):
    try:
        # 1. Find the student ID
        student_response = (
            supabase
            .table("students")
            .select("*")
            .eq("name", request.student_name)
            .limit(1)
            .execute()
        )

        if not student_response.data:
            raise HTTPException(
                status_code=404,
                detail=f"Student '{request.student_name}' not found."
            )

        student = student_response.data[0]
        student_id = student["id"]

        # 2. Get student's current progress
        progress_response = (
            supabase
            .table("student_progress")
            .select("*")
            .eq("student_id", student_id)
            .execute()
        )

        progress = progress_response.data or []

        # 3. Get student's previous assessments
        assessment_response = (
            supabase
            .table("assessment_results")
            .select("*")
            .eq("student_id", student_id)
            .order("created_at", desc=True)
            .execute()
        )

        assessments = assessment_response.data or []

        # 4. Get student's previous lessons
        lessons_response = (
            supabase
            .table("lessons")
            .select("*")
            .eq("student_id", student_id)
            .order("created_at", desc=True)
            .execute()
        )

        previous_lessons = lessons_response.data or []

        # 5. Build student learning context
        student_context = {
            "student": student,
            "progress": progress,
            "previous_assessments": assessments,
            "previous_lessons": previous_lessons
        }

        # 6. Generate personalized lesson using Gemini
        lesson = create_lesson_plan(
            request,
            student_context
        )

        # 7. Save generated lesson in Supabase
        lesson_data = {
            "student_id": student_id,
            "subject": lesson.subject,
            "topic": lesson.topic,
            "title": lesson.title,
            "difficulty": lesson.difficulty,
            "language": lesson.language,
            "total_duration_minutes": lesson.total_duration_minutes,
            "learning_objectives": lesson.learning_objectives,
        }

        lesson_response = (
            supabase
            .table("lessons")
            .insert(lesson_data)
            .execute()
        )

        if not lesson_response.data:
            raise Exception("Failed to save lesson to Supabase.")

        # 8. Return generated lesson
        return lesson

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create lesson: {str(e)}"
        )