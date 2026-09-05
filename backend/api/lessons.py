from fastapi import APIRouter, HTTPException, Depends
from models.lesson import LessonRequest, LessonPlan
from services.gemini_service import create_lesson_plan
from services.lesson_state_service import create_lesson_state
from database.supabase_client import supabase
from models.lesson import LessonRequest, LessonPlan
from api.dependencies import get_current_student

router = APIRouter(
    prefix="/api/lesson",
    tags=["Lesson"]
)


@router.post("/create", response_model=LessonPlan)
def create_lesson(request: LessonRequest, student: dict = Depends(get_current_student)):
    try:
        # Student information is provided by the dependency, not requested by name
        student_id = student["id"]

        # -----------------------------------------------------
        # Resolve lesson language
        #
        # Priority:
        # 1. Language explicitly provided in the request
        # 2. Student's preferred language from profile
        # 3. English fallback
        # -----------------------------------------------------

        language = (
            request.language
            or student.get("preferred_language")
            or "English"
        )

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

        # -----------------------------------------------------
        # Create lesson request using resolved language
        # -----------------------------------------------------

        lesson_request = request.model_copy(
            update={
                "language": language,
            }
        )

        # 6. Generate personalized lesson using Gemini
        lesson = create_lesson_plan(
            lesson_request,
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
            "lesson_content": {
                "segments": [
                    segment.model_dump()
                    for segment in lesson.segments
                ]
            },
        }

        lesson_response = (
            supabase
            .table("lessons")
            .insert(lesson_data)
            .execute()
        )

        if not lesson_response.data:
            raise Exception("Failed to save lesson to Supabase.")

        # 8. Get the newly created lesson ID
        saved_lesson = lesson_response.data[0]
        lesson_id = saved_lesson["id"]

        # 9. Initialize persistent Teacher Agent state
        initial_concept = (
            lesson.learning_objectives[0]
            if lesson.learning_objectives
            else lesson.topic
        )

        create_lesson_state(
            lesson_id=lesson_id,
            student_id=student_id,
            subject=lesson.subject,
            topic=lesson.topic,
            current_concept=initial_concept,
            difficulty=lesson.difficulty,
        )

        # Add the database lesson ID to the API response
        lesson.lesson_id = lesson_id

        # 10. Return generated lesson
        return lesson

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create lesson: {str(e)}"
        )