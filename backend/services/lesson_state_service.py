from typing import Any, Dict, Optional

from database.supabase_client import supabase

def create_lesson_state(
    lesson_id: str,
    student_id: str,
    subject: str,
    topic: str,
    current_concept: str,
    difficulty: str = "beginner",
) -> Dict[str, Any]:
    """
    Create the initial state for a lesson.

    For objective-aware lessons, the first segment's
    objective_index determines the initial learning objective.

    Older lessons without objective_index remain supported.
    """

    lesson_result = (
        supabase
        .table("lessons")
        .select("learning_objectives, lesson_content")
        .eq("id", lesson_id)
        .single()
        .execute()
    )

    if not lesson_result.data:
        raise RuntimeError("Lesson does not exist.")

    lesson_data = lesson_result.data

    learning_objectives = (
        lesson_data.get("learning_objectives") or []
    )

    lesson_content = (
        lesson_data.get("lesson_content") or {}
    )

    segments = lesson_content.get("segments") or []

    initial_concept = current_concept
    initial_segment_index = 0

    if segments:
        first_segment = segments[0]

        objective_index = first_segment.get("objective_index")

        # New objective-aware lesson.
        if (
            objective_index is not None
            and isinstance(objective_index, int)
            and 0 <= objective_index < len(learning_objectives)
        ):
            initial_concept = learning_objectives[objective_index]

        else:
            # Backward-compatible fallback for old lessons.
            initial_concept = (
                first_segment.get("concept")
                or first_segment.get("title")
                or current_concept
            )

    elif learning_objectives:
        initial_concept = learning_objectives[0]

    data = {
        "lesson_id": lesson_id,
        "student_id": student_id,
        "subject": subject,
        "topic": topic,
        "current_concept": initial_concept,
        "current_segment": "introduction",
        "current_segment_index": initial_segment_index,
        "difficulty": difficulty,
        "attempts": 0,
        "correct_attempts": 0,
        "mastery_score": 0,
        "misconceptions": [],
        "last_action": None,
        "completed": False,
    }

    result = (
        supabase
        .table("lesson_state")
        .insert(data)
        .execute()
    )

    if not result.data:
        raise RuntimeError("Failed to create lesson state.")

    return result.data[0]


def get_lesson_state(
    lesson_id: str,
    student_id: str,
) -> Optional[Dict[str, Any]]:
    """
    Retrieve the current lesson state.
    """

    result = (
        supabase
        .table("lesson_state")
        .select("*")
        .eq("lesson_id", lesson_id)
        .eq("student_id", student_id)
        .limit(1)
        .execute()
    )

    if not result.data:
        return None

    return result.data[0]


def update_lesson_state(
    lesson_id: str,
    student_id: str,
    updates: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Update the student's lesson state.
    """

    result = (
        supabase
        .table("lesson_state")
        .update(updates)
        .eq("lesson_id", lesson_id)
        .eq("student_id", student_id)
        .execute()
    )

    if not result.data:
        raise RuntimeError("Lesson state was not found or could not be updated.")

    return result.data[0]


def record_answer(
    lesson_id: str,
    student_id: str,
    correct: bool,
    score: float,
    misconception_description: Optional[str] = None,
    next_action: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Record an answer and update lesson performance.

    Mastery is calculated using the running average of answer scores
    instead of replacing mastery with only the latest score.
    """

    state = get_lesson_state(
        lesson_id=lesson_id,
        student_id=student_id,
    )

    if not state:
        raise RuntimeError("Lesson state does not exist.")

    attempts = state.get("attempts", 0) + 1
    correct_attempts = state.get("correct_attempts", 0)

    if correct:
        correct_attempts += 1

    # Previous mastery and attempts are used to calculate
    # a running average with the new score.
    previous_mastery = float(state.get("mastery_score", 0))

    if attempts == 1:
        mastery_score = float(score)
    else:
        mastery_score = (
            (previous_mastery * (attempts - 1)) + float(score)
        ) / attempts

    mastery_score = max(
        0,
        min(100, mastery_score),
    )

    misconceptions = state.get("misconceptions") or []

    if misconception_description:
        if misconception_description not in misconceptions:
            misconceptions.append(misconception_description)

    updates = {
        "attempts": attempts,
        "correct_attempts": correct_attempts,
        "mastery_score": round(mastery_score, 2),
        "misconceptions": misconceptions,
        "last_action": next_action,
        "current_segment": "evaluation",
    }

    return update_lesson_state(
        lesson_id=lesson_id,
        student_id=student_id,
        updates=updates,
    )


def update_segment(
    lesson_id: str,
    student_id: str,
    segment: str,
) -> Dict[str, Any]:
    """
    Update the current lesson segment.
    """

    return update_lesson_state(
        lesson_id=lesson_id,
        student_id=student_id,
        updates={
            "current_segment": segment,
        },
    )

def record_adaptive_action(
    lesson_id: str,
    student_id: str,
    action: str,
    difficulty: str | None = None,
) -> Dict[str, Any]:
    """
    Save the latest adaptive teaching action, update the
    current lesson segment, and optionally update difficulty.
    """

    segment_map = {
        "CONTINUE": "explanation",
        "SIMPLIFY": "re_explanation",
        "REEXPLAIN": "re_explanation",
        "ANALOGY": "analogy",
        "EXAMPLE": "example",
        "LOWER_DIFFICULTY": "explanation",
        "INCREASE_DIFFICULTY": "explanation",
        "NEW_QUESTION": "question",
        "NEXT_CONCEPT": "introduction",
    }

    segment = segment_map.get(action, "explanation")

    updates = {
        "last_action": action,
        "current_segment": segment,
    }

    if difficulty:
        updates["difficulty"] = difficulty

    return update_lesson_state(
        lesson_id=lesson_id,
        student_id=student_id,
        updates=updates,
    )

def update_concept(
    lesson_id: str,
    student_id: str,
    concept: str,
) -> Dict[str, Any]:
    """
    Move the student to a new concept.
    """

    return update_lesson_state(
        lesson_id=lesson_id,
        student_id=student_id,
        updates={
            "current_concept": concept,
            "current_segment": "introduction",
        },
    )

def move_to_next_concept(
    lesson_id: str,
    student_id: str,
) -> Dict[str, Any]:
    """
    Move the Teacher Agent to the next learning objective.

    Multiple teaching segments can belong to the same objective.
    When the current objective is mastered, this function skips
    remaining segments belonging to that objective and moves to
    the first segment of the next objective.

    Older lessons without objective_index use the previous
    segment-by-segment behavior for backward compatibility.
    """

    state = get_lesson_state(
        lesson_id=lesson_id,
        student_id=student_id,
    )

    if not state:
        raise RuntimeError("Lesson state does not exist.")

    lesson_result = (
        supabase
        .table("lessons")
        .select("learning_objectives, lesson_content")
        .eq("id", lesson_id)
        .single()
        .execute()
    )

    if not lesson_result.data:
        raise RuntimeError("Lesson does not exist.")

    lesson_data = lesson_result.data

    learning_objectives = (
        lesson_data.get("learning_objectives") or []
    )

    lesson_content = (
        lesson_data.get("lesson_content") or {}
    )

    segments = lesson_content.get("segments") or []

    if not segments:
        raise RuntimeError(
            "This lesson does not contain teaching segments."
        )

    current_index = int(
        state.get("current_segment_index", 0)
    )

    if current_index >= len(segments):
        return complete_lesson(
            lesson_id=lesson_id,
            student_id=student_id,
        )

    current_segment = segments[current_index]

    current_objective_index = current_segment.get("objective_index")
        # ---------------------------------------------------------
    # Do not skip interactive segments before evaluation
    # ---------------------------------------------------------

    current_segment_type = (
        current_segment.get("type", "")
        .lower()
    )

    interactive_segments = {
        "question",
        "practice",
        "assessment",
    }

    if current_segment_type in interactive_segments:
        # These segments require a student response first.
        # They may only advance after evaluation has produced
        # an action such as CONTINUE.
        if state.get("last_action") != "CONTINUE":
            return state
    # ---------------------------------------------------------
    # New objective-aware lesson
    # ---------------------------------------------------------
    if (
        current_objective_index is not None
        and isinstance(current_objective_index, int)
    ):
        next_segment_index = None
        next_objective_index = None

        # Find the first segment belonging to a NEW objective.
        for index in range(current_index + 1, len(segments)):
            segment = segments[index]
            segment_objective_index = segment.get("objective_index")

            if (
                isinstance(segment_objective_index, int)
                and segment_objective_index > current_objective_index
            ):
                next_segment_index = index
                next_objective_index = segment_objective_index
                break

        # No later objective exists.
        if next_segment_index is None:
            return complete_lesson(
                lesson_id=lesson_id,
                student_id=student_id,
            )

        if (
            next_objective_index is not None
            and next_objective_index < len(learning_objectives)
        ):
            next_concept = learning_objectives[
                next_objective_index
            ]
        else:
            next_segment = segments[next_segment_index]

            next_concept = (
                next_segment.get("concept")
                or next_segment.get("title")
                or f"Objective {next_objective_index + 1}"
            )

        return update_lesson_state(
            lesson_id=lesson_id,
            student_id=student_id,
            updates={
                "current_concept": next_concept,
                "current_segment_index": next_segment_index,
                "current_segment": "introduction",
                "last_action": "NEXT_CONCEPT",
            },
        )

    # ---------------------------------------------------------
    # Backward compatibility for old lessons
    # ---------------------------------------------------------
    next_index = current_index + 1

    if next_index >= len(segments):
        return complete_lesson(
            lesson_id=lesson_id,
            student_id=student_id,
        )

    next_segment = segments[next_index]

    next_concept = (
        next_segment.get("concept")
        or next_segment.get("title")
        or f"Segment {next_index + 1}"
    )

    return update_lesson_state(
        lesson_id=lesson_id,
        student_id=student_id,
        updates={
            "current_concept": next_concept,
            "current_segment_index": next_index,
            "current_segment": "introduction",
            "last_action": "NEXT_CONCEPT",
        },
    )
    
def advance_to_next_segment(
    lesson_id: str,
    student_id: str,
) -> Dict[str, Any]:
    """
    Move the lesson state to the next segment.

    This function advances only within the current learning
    objective. Moving to a new concept is handled separately
    by move_to_next_concept().
    """

    # ---------------------------------------------------------
    # 1. Get current lesson state
    # ---------------------------------------------------------

    state = get_lesson_state(
        lesson_id=lesson_id,
        student_id=student_id,
    )

    if not state:
        raise ValueError("Lesson state not found.")

    if state.get("completed"):
        return state

    # ---------------------------------------------------------
    # 2. Get lesson content
    # ---------------------------------------------------------

    lesson_result = (
        supabase
        .table("lessons")
        .select("lesson_content")
        .eq("id", lesson_id)
        .single()
        .execute()
    )

    lesson = lesson_result.data

    if not lesson:
        raise ValueError("Lesson not found.")

    lesson_content = lesson.get("lesson_content") or {}
    segments = lesson_content.get("segments") or []

    if not segments:
        raise ValueError(
            "No lesson segments found."
        )

    # ---------------------------------------------------------
    # 3. Calculate next segment
    # ---------------------------------------------------------
    current_index = state.get(
        "current_segment_index",
        0,
    )

    # ---------------------------------------------------------
    # 4. Get current segment
    # ---------------------------------------------------------

    if current_index < 0:
        current_index = 0

    if current_index >= len(segments):
        return complete_lesson(
            lesson_id=lesson_id,
            student_id=student_id,
        )

    current_segment = segments[current_index]

    current_segment_type = (
        current_segment.get("type", "")
        .lower()
    )

    # ---------------------------------------------------------
    # 5. Do not skip interactive segments
    # ---------------------------------------------------------

    interactive_segments = {
        "question",
        "practice",
        "assessment",
    }

    current_state = state or {}

    if current_segment_type in interactive_segments:
        # The student must answer first.
        #
        # /evaluate records the AI decision in last_action.
        # CONTINUE and NEXT_CONCEPT both mean the
        # interactive segment has been successfully handled.
        if current_state.get("last_action") not in {
            "CONTINUE",
            "NEXT_CONCEPT",
        }:
            return current_state

    # ---------------------------------------------------------
    # 6. Calculate next segment
    # ---------------------------------------------------------

    next_index = current_index + 1

    # ---------------------------------------------------------
    # 7. End of lesson
    # ---------------------------------------------------------

    if next_index >= len(segments):
        return complete_lesson(
            lesson_id=lesson_id,
            student_id=student_id,
        )

    # ---------------------------------------------------------
    # 8. Get next segment
    # ---------------------------------------------------------

    next_segment = segments[next_index]

    current_objective_index = current_segment.get(
        "objective_index"
    )

    next_objective_index = next_segment.get(
        "objective_index"
    )

   # ---------------------------------------------------------
# 9. Allow progression across learning objectives
# ---------------------------------------------------------

# A lesson is a sequence of teaching segments.
# Moving from one objective to the next is allowed.
# Interactive segments are still protected by the
# evaluation check above.
    # ---------------------------------------------------------
    # 10. Determine next segment type
    # ---------------------------------------------------------

    next_segment_type = next_segment.get(
        "type",
        "explanation",
    )

    # ---------------------------------------------------------
    # 11. Update state
    # ---------------------------------------------------------

    return update_lesson_state(
        lesson_id=lesson_id,
        student_id=student_id,
        updates={
            "current_segment_index": next_index,
            "current_segment": next_segment_type,
            "current_concept": (
                next_segment.get("concept")
                or next_segment.get("title")
                or state.get("current_concept")
        ),
        "last_action": "NEXT_SEGMENT",
    }
    )

def complete_lesson(
    lesson_id: str,
    student_id: str,
) -> Dict[str, Any]:
    """
    Mark the lesson as completed.
    """

    return update_lesson_state(
        lesson_id=lesson_id,
        student_id=student_id,
        updates={
            "completed": True,
            "current_segment": "summary",
        },
    )
