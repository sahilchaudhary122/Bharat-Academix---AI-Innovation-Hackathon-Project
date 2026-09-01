from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from models.assessment import AssessmentRequest, AssessmentResponse
from database.supabase_client import supabase


router = APIRouter(
    prefix="/api/assessment",
    tags=["Assessment"]
)


def calculate_mastery(assessments: list) -> float:
    """
    Calculate mastery from all available assessment scores.

    Each assessment contributes equally to the student's
    current mastery for the topic.
    """

    scores = []

    for assessment in assessments:
        score = assessment.get("score")

        if score is not None:
            try:
                score = float(score)
                score = max(0.0, min(1.0, score))
                scores.append(score)
            except (TypeError, ValueError):
                continue

    if not scores:
        return 0.0

    return round(sum(scores) / len(scores), 2)


def determine_status(mastery: float) -> str:
    """
    Convert mastery score into an understandable learning status.
    """

    if mastery >= 0.85:
        return "mastered"

    if mastery >= 0.70:
        return "proficient"

    if mastery >= 0.40:
        return "learning"

    return "needs_practice"


def build_strengths(assessments: list) -> str | None:
    """
    Extract useful positive feedback from correct assessments.
    """

    strengths = []

    for assessment in assessments:
        if assessment.get("is_correct") is True:
            feedback = assessment.get("feedback")

            if feedback and feedback.strip():
                strengths.append(feedback.strip())

    if not strengths:
        return None

    # Remove duplicates while preserving order.
    unique_strengths = list(dict.fromkeys(strengths))

    return "; ".join(unique_strengths[-3:])


def build_weaknesses(assessments: list) -> str | None:
    """
    Identify weaknesses from incorrect answers and misconceptions.
    """

    weaknesses = []

    for assessment in assessments:
        is_correct = assessment.get("is_correct")
        misconception = assessment.get("misconception")

        if is_correct is False:
            if misconception and misconception.strip():
                weaknesses.append(misconception.strip())
            else:
                weaknesses.append("Needs more practice with this topic.")

    if not weaknesses:
        return None

    unique_weaknesses = list(dict.fromkeys(weaknesses))

    return "; ".join(unique_weaknesses[-3:])


def find_progress_record(
    student_id: str,
    subject: str,
    topic: str,
):
    """
    Find the existing progress record for this student/topic.
    """

    result = (
        supabase
        .table("student_progress")
        .select("*")
        .eq("student_id", student_id)
        .eq("subject", subject)
        .eq("topic", topic)
        .limit(1)
        .execute()
    )

    if result.data:
        return result.data[0]

    return None


def update_student_progress(
    request: AssessmentRequest,
) -> dict:
    """
    Recalculate and persist adaptive learning progress.
    """

    # Get every assessment for this student and topic.
    assessment_result = (
        supabase
        .table("assessment_results")
        .select("*")
        .eq("student_id", request.student_id)
        .eq("subject", request.subject)
        .eq("topic", request.topic)
        .execute()
    )

    assessments = assessment_result.data or []

    mastery = calculate_mastery(assessments)
    status = determine_status(mastery)

    strengths = build_strengths(assessments)
    weaknesses = build_weaknesses(assessments)

    assessed_at = datetime.now(timezone.utc).isoformat()

    existing_progress = find_progress_record(
        request.student_id,
        request.subject,
        request.topic,
    )

    progress_data = {
        "student_id": request.student_id,
        "subject": request.subject,
        "topic": request.topic,
        "mastery_score": mastery,
        "status": status,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "last_assessed_at": assessed_at,
    }

    if existing_progress:
        result = (
            supabase
            .table("student_progress")
            .update(progress_data)
            .eq("id", existing_progress["id"])
            .execute()
        )
    else:
        result = (
            supabase
            .table("student_progress")
            .insert(progress_data)
            .execute()
        )

    if not result.data:
        raise Exception("Failed to update student progress.")

    return result.data[0]


@router.post("", response_model=AssessmentResponse)
def create_assessment(request: AssessmentRequest):

    try:
        # ---------------------------------------------------------
        # 1. Save assessment result
        # ---------------------------------------------------------

        result = (
            supabase
            .table("assessment_results")
            .insert(request.model_dump())
            .execute()
        )

        if not result.data:
            raise HTTPException(
                status_code=500,
                detail="Failed to create assessment"
            )

        assessment = result.data[0]

        # ---------------------------------------------------------
        # 2. Automatically update adaptive progress
        # ---------------------------------------------------------

        update_student_progress(request)

        # ---------------------------------------------------------
        # 3. Return the saved assessment
        # ---------------------------------------------------------

        return assessment

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create assessment: {str(e)}"
        )
