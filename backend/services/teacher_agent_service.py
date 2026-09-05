from typing import Any, Dict, Optional

from database.supabase_client import supabase
from services.lesson_state_service import (
    get_lesson_state,
    update_lesson_state,
)


# ============================================================
# GET NEXT TEACHER STEP
# ============================================================

def get_teacher_next_step(
    lesson_id: str,
    student_id: str,
) -> Dict[str, Any]:
    """
    Determine what the Teacher Agent should present next.

    This function uses:
    - lesson content
    - learning objectives
    - persistent lesson state
    - current segment index
    - current concept
    - difficulty
    - previous adaptive action

    It does not call the LLM.
    """

    # ---------------------------------------------------------
    # 1. Get current lesson state
    # ---------------------------------------------------------

    lesson_state = get_lesson_state(
        lesson_id=lesson_id,
        student_id=student_id,
    )

    if not lesson_state:
        raise ValueError("Lesson state not found.")

    # If lesson is already completed
    if lesson_state.get("completed"):
        return {
            "action": "COMPLETE",
            "lesson_id": lesson_id,
            "student_id": student_id,
            "message": (
                "Lesson completed. "
                "The student can proceed to the final assessment."
            ),
            "lesson_state": lesson_state,
        }

    # ---------------------------------------------------------
    # 2. Fetch lesson content
    # ---------------------------------------------------------

    lesson_result = (
        supabase
        .table("lessons")
        .select(
            "id, subject, topic, title, "
            "learning_objectives, lesson_content"
        )
        .eq("id", lesson_id)
        .single()
        .execute()
    )

    lesson = lesson_result.data

    if not lesson:
        raise ValueError("Lesson not found.")

    learning_objectives = (
        lesson.get("learning_objectives") or []
    )

    lesson_content = lesson.get("lesson_content") or {}

    segments = lesson_content.get("segments") or []

    if not segments:
        raise ValueError(
            "No lesson segments found for this lesson."
        )

    # ---------------------------------------------------------
    # 3. Determine current segment
    # ---------------------------------------------------------

    current_index = lesson_state.get(
        "current_segment_index",
        0,
    )

    if current_index < 0:
        current_index = 0

    if current_index >= len(segments):
        return {
            "action": "COMPLETE",
            "lesson_id": lesson_id,
            "student_id": student_id,
            "concept": lesson_state.get(
                "current_concept"
            ),
            "segment_type": "summary",
            "segment_index": current_index,
            "difficulty": lesson_state.get(
                "difficulty",
                "beginner",
            ),
            "content": None,
            "lesson_state": lesson_state,
        }

    segment = segments[current_index]

    # ---------------------------------------------------------
    # 4. Determine objective
    # ---------------------------------------------------------

    objective_index = segment.get(
        "objective_index"
    )

    if (
        isinstance(objective_index, int)
        and 0 <= objective_index < len(learning_objectives)
    ):
        objective = learning_objectives[
            objective_index
        ]
    else:
        objective = lesson_state.get(
            "current_concept"
        )

    # ---------------------------------------------------------
    # 5. Determine segment type
    # ---------------------------------------------------------

    segment_type = segment.get(
        "type",
        lesson_state.get(
            "current_segment",
            "introduction",
        ),
    )

    # Keep persistent state synchronized with the actual
    # segment selected by current_segment_index.
    if lesson_state.get("current_segment") != segment_type:
        lesson_state = update_lesson_state(
            lesson_id=lesson_id,
            student_id=student_id,
            updates={
                "current_segment": segment_type,
            },
        )

    # ---------------------------------------------------------
    # 6. Build Teacher Agent response
    # ---------------------------------------------------------

    return {
        "action": "PRESENT_SEGMENT",
        "lesson_id": lesson_id,
        "student_id": student_id,
        "subject": lesson.get("subject"),
        "topic": lesson.get("topic"),
        "title": lesson.get("title"),
        "concept": objective,
        "segment_type": segment_type,
        "segment_index": current_index,
        "objective_index": objective_index,
        "difficulty": lesson_state.get(
            "difficulty",
            "beginner",
        ),
        "content": {
            "title": segment.get("title"),
            "concept": segment.get("concept"),
            "explanation": segment.get(
                "explanation"
            ),
            "duration_minutes": segment.get(
                "duration_minutes"
            ),
        },
        "lesson_state": lesson_state,
    }


# ============================================================
# MAIN TEACHER AGENT ORCHESTRATION
# ============================================================

def orchestrate_teacher(
    lesson_id: str,
    student_id: str,
    language: str = "English",
    difficulty: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Main Teacher Agent orchestration entry point.

    Determines what the teacher should present next by using
    the persistent lesson state and lesson content.

    This function does not call the LLM.
    """

    lesson_state = get_lesson_state(
        lesson_id=lesson_id,
        student_id=student_id,
    )

    if not lesson_state:
        raise ValueError("Lesson state not found.")

    # ---------------------------------------------------------
    # Completed lesson
    # ---------------------------------------------------------

    if lesson_state.get("completed"):
        return {
            "action": "COMPLETE",
            "lesson_id": lesson_id,
            "student_id": student_id,
            "language": language,
            "message": (
                "Lesson completed. "
                "The student can proceed to the final assessment."
            ),
            "lesson_state": lesson_state,
        }

    # ---------------------------------------------------------
    # Get current teaching step
    # ---------------------------------------------------------

    next_step = get_teacher_next_step(
        lesson_id=lesson_id,
        student_id=student_id,
    )

    # ---------------------------------------------------------
    # Use requested difficulty if provided.
    # Otherwise preserve persistent difficulty.
    # ---------------------------------------------------------

    effective_difficulty = (
        difficulty
        if difficulty
        else lesson_state.get(
            "difficulty",
            "beginner",
        )
    )

    next_step["difficulty"] = effective_difficulty

    # ---------------------------------------------------------
    # Determine whether the teacher is waiting for an answer
    # ---------------------------------------------------------

    segment_type = next_step.get(
        "segment_type",
        "",
    ).lower()

    if segment_type in {
        "question",
        "practice",
        "assessment",
    }:
        next_step["teacher_status"] = "WAITING_FOR_STUDENT"
        next_step["message"] = (
            "Present this question or practice activity "
            "and wait for the student's answer."
        )
    else:
        next_step["teacher_status"] = "TEACHING"
        next_step["message"] = (
            "Present this teaching segment to the student."
        )

    # ---------------------------------------------------------
    # Attach resolved teaching language
    # ---------------------------------------------------------

    next_step["language"] = language

    return next_step