from typing import Any, Dict, Optional

from database.supabase_client import supabase


def get_concept_progress(
    lesson_id: str,
    student_id: str,
    concept: str,
) -> Optional[Dict[str, Any]]:
    """
    Get progress for a specific concept.
    """

    result = (
        supabase
        .table("concept_progress")
        .select("*")
        .eq("lesson_id", lesson_id)
        .eq("student_id", student_id)
        .eq("concept", concept)
        .limit(1)
        .execute()
    )

    if not result.data:
        return None

    return result.data[0]


def calculate_status(mastery_score: float) -> str:
    """
    Determine concept learning status from mastery score.
    """

    if mastery_score >= 85:
        return "mastered"

    return "learning"


def record_concept_answer(
    lesson_id: str,
    student_id: str,
    concept: str,
    correct: bool,
    score: float,
    misconception_description: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Record an answer for a specific concept.

    Each concept maintains its own attempts, correct attempts,
    mastery score, misconceptions, and learning status.
    """

    existing = get_concept_progress(
        lesson_id=lesson_id,
        student_id=student_id,
        concept=concept,
    )

    score = max(0, min(100, float(score)))

    if existing:
        attempts = existing.get("attempts", 0) + 1
        correct_attempts = existing.get("correct_attempts", 0)

        if correct:
            correct_attempts += 1

        previous_mastery = float(
            existing.get("mastery_score", 0)
        )

        mastery_score = (
            (previous_mastery * (attempts - 1)) + score
        ) / attempts

        misconceptions = existing.get("misconceptions") or []

        if (
            misconception_description
            and misconception_description not in misconceptions
        ):
            misconceptions.append(misconception_description)

        status = calculate_status(mastery_score)

        updates = {
            "attempts": attempts,
            "correct_attempts": correct_attempts,
            "mastery_score": round(mastery_score, 2),
            "misconceptions": misconceptions,
            "status": status,
        }

        result = (
            supabase
            .table("concept_progress")
            .update(updates)
            .eq("id", existing["id"])
            .execute()
        )

    else:
        attempts = 1
        correct_attempts = 1 if correct else 0

        mastery_score = score
        status = calculate_status(mastery_score)

        misconceptions = []

        if misconception_description:
            misconceptions.append(
                misconception_description
            )

        data = {
            "lesson_id": lesson_id,
            "student_id": student_id,
            "concept": concept,
            "attempts": attempts,
            "correct_attempts": correct_attempts,
            "mastery_score": round(mastery_score, 2),
            "misconceptions": misconceptions,
            "status": status,
        }

        result = (
            supabase
            .table("concept_progress")
            .insert(data)
            .execute()
        )

    if not result.data:
        raise RuntimeError(
            "Failed to save concept progress."
        )

    return result.data[0]

def get_lesson_concept_progress(
    lesson_id: str,
    student_id: str,
) -> list[Dict[str, Any]]:
    """
    Get progress for all concepts attempted in a lesson.
    """

    result = (
        supabase
        .table("concept_progress")
        .select("*")
        .eq("lesson_id", lesson_id)
        .eq("student_id", student_id)
        .order("created_at")
        .execute()
    )

    return result.data or []


def get_lesson_progress_summary(
    lesson_id: str,
    student_id: str,
) -> Dict[str, Any]:
    """
    Generate an overall progress summary for a lesson.
    """

    # Get all learning objectives for this lesson.
    lesson_result = (
        supabase
        .table("lessons")
        .select("learning_objectives")
        .eq("id", lesson_id)
        .single()
        .execute()
    )

    if not lesson_result.data:
        raise RuntimeError("Lesson does not exist.")

    objectives = lesson_result.data.get("learning_objectives") or []

    # Get concepts that the student has already attempted.
    progress = get_lesson_concept_progress(
        lesson_id=lesson_id,
        student_id=student_id,
    )

    # Make lookup by concept.
    progress_by_concept = {
        item["concept"]: item
        for item in progress
    }

    # Build progress for every learning objective.
    concepts = []

    for objective in objectives:
        existing = progress_by_concept.get(objective)

        if existing:
            concepts.append(existing)
        else:
            concepts.append(
                {
                    "concept": objective,
                    "attempts": 0,
                    "correct_attempts": 0,
                    "mastery_score": 0,
                    "status": "not_started",
                    "misconceptions": [],
                }
            )

    mastered = [
        item for item in concepts
        if item.get("status") == "mastered"
    ]

    learning = [
        item for item in concepts
        if item.get("status") == "learning"
    ]

    not_started = [
        item for item in concepts
        if item.get("status") == "not_started"
    ]

    attempted = [
        item for item in concepts
        if item.get("attempts", 0) > 0
    ]

    # Keep average mastery based only on attempted concepts.
    if attempted:
        average_mastery = (
            sum(
                float(item.get("mastery_score", 0))
                for item in attempted
            )
            / len(attempted)
        )
    else:
        average_mastery = 0

    return {
        "total_concepts": len(concepts),
        "total_attempted_concepts": len(attempted),
        "mastered_concepts": len(mastered),
        "learning_concepts": len(learning),
        "not_started_concepts": len(not_started),
        "average_mastery": round(average_mastery, 2),
        "concepts": concepts,
    }