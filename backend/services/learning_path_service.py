from typing import Any, Dict
from difflib import SequenceMatcher
from database.supabase_client import supabase


def _infer_target_subject(
    learning_goal: str | None,
    lessons: list[dict],
) -> str | None:
    """
    Infer the student's target subject from the learning goal.

    If the goal explicitly mentions a subject, use that subject.
    Otherwise, fall back to the most recently used lesson subject.
    """

    goal = (learning_goal or "").lower()

    # Common subject keywords.
    subject_keywords = {
        "physics": "Physics",
        "chemistry": "Chemistry",
        "biology": "Biology",
        "computer science": "Computer Science",
        "programming": "Computer Science",
        "math": "Mathematics",
        "mathematics": "Mathematics",
    }

    for keyword, subject in subject_keywords.items():
        if keyword in goal:
            return subject

    # Fallback: most recent lesson subject.
    for lesson in reversed(lessons):
        subject = lesson.get("subject")

        if subject:
            return subject

    return None


def _get_priority(
    mastery_score: float | None,
    status: str | None,
) -> tuple[str, str]:

    mastery = float(mastery_score or 0)

    if status == "mastered" or mastery >= 85:
        return (
            "low",
            "This concept is already mastered.",
        )

    if mastery >= 70:
        return (
            "medium",
            "This concept is partially mastered and "
            "needs more practice.",
        )

    if mastery > 0:
        return (
            "high",
            "This concept needs more practice to improve "
            "mastery.",
        )

    return (
        "high",
        "This concept has not been attempted yet.",
    )

def _is_similar_concept(
    concept: str,
    existing_concepts: list[str],
    threshold: float = 0.78,
) -> bool:
    """
    Detect concepts that are almost identical in wording.
    """

    normalized = concept.lower().strip()

    for existing in existing_concepts:

        existing_normalized = existing.lower().strip()

        similarity = SequenceMatcher(
            None,
            normalized,
            existing_normalized,
        ).ratio()

        if similarity >= threshold:
            return True

    return False


class SeenConcepts:
    """Track concepts that have already been seen while ignoring duplicates and near-duplicates."""

    def __init__(self) -> None:
        self._concepts: list[str] = []

    def add(self, concept: str) -> bool:
        """Add a concept and return True if it was newly accepted."""
        cleaned = (concept or "").strip()

        if not cleaned:
            return False

        if self.contains(cleaned):
            return False

        self._concepts.append(cleaned)
        return True

    def contains(self, concept: str) -> bool:
        """Check whether the concept or a near-duplicate has already been seen."""
        cleaned = (concept or "").strip()

        if not cleaned:
            return False

        return _is_similar_concept(cleaned, self._concepts)

    def __iter__(self):
        return iter(self._concepts)

    def __len__(self) -> int:
        return len(self._concepts)

    def clear(self) -> None:
        self._concepts.clear()

    def as_list(self) -> list[str]:
        return list(self._concepts)


def generate_learning_path(
    student_id: str,
) -> Dict[str, Any]:
    """
    Generate a subject-aware personalized learning path.
    """

    # ---------------------------------------------------------
    # 1. Get student profile
    # ---------------------------------------------------------

    student_result = (
        supabase
        .table("students")
        .select(
            "id, name, grade, preferred_language, "
            "current_level, learning_goals"
        )
        .eq("id", student_id)
        .single()
        .execute()
    )

    if not student_result.data:
        raise ValueError("Student not found.")

    student = student_result.data

    # ---------------------------------------------------------
    # 2. Get previous lessons
    # ---------------------------------------------------------

    lessons_result = (
        supabase
        .table("lessons")
        .select(
            "id, subject, topic, title, difficulty, "
            "learning_objectives, created_at"
        )
        .eq("student_id", student_id)
        .order("created_at")
        .execute()
    )

    lessons = lessons_result.data or []

    # ---------------------------------------------------------
    # 3. Determine target subject
    # ---------------------------------------------------------

    target_subject = _infer_target_subject(
        student.get("learning_goals"),
        lessons,
    )

    # ---------------------------------------------------------
    # 4. Filter lessons to target subject
    # ---------------------------------------------------------

    if target_subject:
        subject_lessons = [
            lesson
            for lesson in lessons
            if (
                lesson.get("subject", "").lower()
                == target_subject.lower()
            )
        ]
    else:
        subject_lessons = lessons

    # ---------------------------------------------------------
    # 5. Get concept progress
    # ---------------------------------------------------------

    progress_result = (
        supabase
        .table("concept_progress")
        .select(
            "lesson_id, concept, attempts, "
            "correct_attempts, mastery_score, "
            "status, misconceptions"
        )
        .eq("student_id", student_id)
        .execute()
    )

    progress = progress_result.data or []

    # ---------------------------------------------------------
    # 6. Build concept progress lookup
    # ---------------------------------------------------------

    progress_by_concept = {}

    for item in progress:
        concept = item.get("concept")

        if concept:
            progress_by_concept[concept.strip().lower()] = item

    # ---------------------------------------------------------
    # 7. Build subject-aware learning path
    # ---------------------------------------------------------

    learning_path = []

    # Used to prevent duplicate or near-duplicate concepts.
    seen_concepts = SeenConcepts()

    for lesson in subject_lessons:

        topic = lesson.get("topic") or "Unknown Topic"

        difficulty = lesson.get(
            "difficulty"
        ) or student.get(
            "current_level",
            "beginner",
        )

        objectives = lesson.get(
            "learning_objectives"
        ) or []

        for objective in objectives:

            if not objective:
                continue

            objective = objective.strip()

            # Skip duplicate or near-duplicate concepts.
            if seen_concepts.contains(objective):
                continue

            seen_concepts.add(objective)

            concept_progress = progress_by_concept.get(
                objective.lower()
            )
            if concept_progress:

                priority, reason = _get_priority(
                    concept_progress.get("mastery_score"),
                    concept_progress.get("status"),
                )

            else:

                priority = "high"
                reason = (
                    "This concept has not been attempted yet."
                )

            learning_path.append(
                {
                    "topic": objective,
                    "reason": reason,
                    "difficulty": difficulty,
                    "priority": priority,
                }
            )

    # ---------------------------------------------------------
    # 8. Prioritize concepts
    # ---------------------------------------------------------

    priority_order = {
        "high": 0,
        "medium": 1,
        "low": 2,
    }

    learning_path.sort(
        key=lambda item: priority_order.get(
            item["priority"],
            3,
        )
    )
    # Keep the learning path focused.
# The full lesson history remains stored in the database.
    MAX_PATH_ITEMS = 15

    learning_path = learning_path[:MAX_PATH_ITEMS]

    # ---------------------------------------------------------
    # 9. Find next recommendation
    # ---------------------------------------------------------

    next_item = None

    for item in learning_path:

        if item["priority"] in {"high", "medium"}:
            next_item = item
            break

    if next_item:

        next_recommendation = {
            "topic": next_item["topic"],
            "difficulty": next_item["difficulty"],
            "reason": next_item["reason"],
        }

    elif learning_path:

        # All concepts are mastered.
        next_recommendation = {
            "topic": learning_path[0]["topic"],
            "difficulty": learning_path[0]["difficulty"],
            "reason": (
                "The available concepts are already mastered. "
                "The student can move to a new topic or "
                "higher difficulty level."
            ),
        }

    else:

        # No previous lessons for this subject.
        next_recommendation = {
            "topic": (
                student.get("learning_goals")
                or "Start a new learning topic"
            ),
            "difficulty": student.get(
                "current_level",
                "beginner",
            ),
            "reason": (
                "There are no previous lessons for the "
                "student's target subject. Start a new "
                "lesson based on the learning goal."
            ),
        }

    # ---------------------------------------------------------
    # 10. Return personalized learning path
    # ---------------------------------------------------------

    return {
        "student_id": student["id"],
        "student_name": student["name"],
        "grade": student["grade"],
        "learning_goal": student.get("learning_goals"),
        "current_level": student.get(
            "current_level",
            "beginner",
        ),
        "learning_path": learning_path,
        "next_recommendation": next_recommendation,
    }