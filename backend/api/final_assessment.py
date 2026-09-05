import json
from uuid import uuid4
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import ValidationError

from database.supabase_client import supabase

from models.final_assessment import (
    FinalAssessmentRequest,
    FinalAssessmentResponse,
    AssessmentQuestion,
    FinalAssessmentEvaluationRequest,
    FinalAssessmentEvaluationResponse,
    ConceptAssessmentResult,
    AssessmentReportResponse,
)

from services.gemini_service import generate_json_response
from services.concept_progress_service import record_concept_answer


router = APIRouter(
    prefix="/api/assessment",
    tags=["Final Assessment"],
)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_assessment_status(score: float) -> str:
    """
    Convert a numerical score into a learning status.
    """

    if score >= 85:
        return "mastered"

    if score >= 70:
        return "proficient"

    if score >= 40:
        return "learning"

    return "needs_practice"


def parse_score(value) -> float:
    """
    Safely convert an AI-generated score to a value between 0 and 100.
    """

    try:
        score = float(value)
    except (TypeError, ValueError):
        score = 0.0

    return max(0.0, min(100.0, score))


def parse_boolean(value, default: bool = False) -> bool:
    """
    Safely convert AI output into a real Python boolean.

    Handles:
        true
        false
        "true"
        "false"
        1
        0
    """

    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        normalized = value.strip().lower()

        if normalized in {"true", "yes", "1"}:
            return True

        if normalized in {"false", "no", "0"}:
            return False

    if isinstance(value, (int, float)):
        return value != 0

    return default


def parse_json_object(response_text: str, error_message: str) -> dict:
    """
    Parse an AI response that MUST be a JSON object.
    """

    try:
        parsed = json.loads(response_text)
    except (json.JSONDecodeError, TypeError):
        raise HTTPException(
            status_code=500,
            detail=error_message,
        )

    if not isinstance(parsed, dict):
        raise HTTPException(
            status_code=500,
            detail=(
                "AI returned an unexpected JSON format. "
                "Expected a JSON object."
            ),
        )

    return parsed


def parse_assessment_questions(response_text: str) -> list:
    """
    Parse assessment questions returned by Gemini.

    Gemini may return either:

        {
            "questions": [...]
        }

    or directly:

        [...]
    """

    try:
        parsed = json.loads(response_text)

    except (json.JSONDecodeError, TypeError):
        raise HTTPException(
            status_code=500,
            detail="AI returned invalid assessment JSON.",
        )

    # Gemini returned:
    #
    # [
    #     {...},
    #     {...}
    # ]
    #
    if isinstance(parsed, list):
        raw_questions = parsed

    # Gemini returned:
    #
    # {
    #     "questions": [...]
    # }
    #
    elif isinstance(parsed, dict):
        raw_questions = parsed.get("questions", [])

    else:
        raise HTTPException(
            status_code=500,
            detail="AI returned an unexpected assessment format.",
        )

    if not isinstance(raw_questions, list):
        raise HTTPException(
            status_code=500,
            detail="Assessment questions must be a list.",
        )

    if not raw_questions:
        raise HTTPException(
            status_code=500,
            detail="AI generated no assessment questions.",
        )

    questions = []

    for index, question in enumerate(raw_questions, start=1):

        if not isinstance(question, dict):
            continue

        # Ensure required fields have usable values.
        question_data = {
            "question": str(
                question.get("question", "")
            ).strip(),

            "concept": str(
                question.get("concept", "")
            ).strip(),

            "question_type": str(
                question.get("question_type", "short_answer")
            ).strip(),

            "correct_answer": str(
                question.get("correct_answer", "")
            ).strip(),

            "explanation": (
                str(question.get("explanation")).strip()
                if question.get("explanation") is not None
                else None
            ),
        }

        # Options are only included when supplied.
        options = question.get("options")

        if options is not None:

            if isinstance(options, list):
                question_data["options"] = [
                    str(option).strip()
                    for option in options
                ]

            else:
                question_data["options"] = None

        else:
            question_data["options"] = None

        # Basic validation before Pydantic validation.
        if not question_data["question"]:
            continue

        if not question_data["concept"]:
            continue

        if not question_data["correct_answer"]:
            continue

        try:
            validated_question = AssessmentQuestion.model_validate(
                question_data
            )

            questions.append(validated_question)

        except ValidationError:
            # Skip malformed AI-generated questions instead of
            # crashing the entire assessment.
            continue

    if not questions:
        raise HTTPException(
            status_code=500,
            detail="AI generated no valid assessment questions.",
        )

    return questions


# ============================================================
# STUDENT PROGRESS
# ============================================================

def update_final_assessment_progress(
    student_id: str,
    subject: str,
    topic: str,
    overall_score: float,
    results: list[ConceptAssessmentResult],
) -> dict:
    """
    Update the student's overall progress after a final assessment.
    """

    status = get_assessment_status(overall_score)

    strengths = list(
        dict.fromkeys(
            result.concept
            for result in results
            if result.score >= 85
        )
    )

    weaknesses = list(
        dict.fromkeys(
            result.concept
            for result in results
            if result.score < 70
        )
    )

    progress_data = {
        "student_id": student_id,
        "subject": subject,
        "topic": topic,
        "mastery_score": overall_score,
        "status": status,
        "strengths": (
            ", ".join(strengths)
            if strengths
            else None
        ),
        "weaknesses": (
            ", ".join(weaknesses)
            if weaknesses
            else None
        ),
        "last_assessed_at": datetime.now(
            timezone.utc
        ).isoformat(),
    }

    existing = (
        supabase
        .table("student_progress")
        .select("id")
        .eq("student_id", student_id)
        .eq("subject", subject)
        .eq("topic", topic)
        .limit(1)
        .execute()
    )

    if existing.data:

        result = (
            supabase
            .table("student_progress")
            .update(progress_data)
            .eq("id", existing.data[0]["id"])
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
        raise RuntimeError(
            "Failed to update student progress after final assessment."
        )

    return result.data[0]


# ============================================================
# GENERATE FINAL ASSESSMENT
# ============================================================

@router.post(
    "/generate",
    response_model=FinalAssessmentResponse,
)
def generate_final_assessment(
    request: FinalAssessmentRequest,
):
    """
    Generate a final assessment for a completed lesson.

    Questions are based on the lesson objectives and content.
    """

    try:

        # ----------------------------------------------------
        # Load lesson
        # ----------------------------------------------------

        lesson_result = (
            supabase
            .table("lessons")
            .select(
                "id, student_id, subject, topic, "
                "learning_objectives, lesson_content"
            )
            .eq("id", request.lesson_id)
            .single()
            .execute()
        )

        if not lesson_result.data:
            raise HTTPException(
                status_code=404,
                detail="Lesson not found.",
            )

        lesson = lesson_result.data

        # ----------------------------------------------------
        # Verify ownership
        # ----------------------------------------------------

        if lesson.get("student_id") != request.student_id:
            raise HTTPException(
                status_code=403,
                detail="Lesson does not belong to this student.",
            )

        # ----------------------------------------------------
        # Use the actual lesson subject/topic
        # ----------------------------------------------------

        subject = lesson.get("subject") or request.subject
        topic = lesson.get("topic") or request.topic

        # ----------------------------------------------------
        # Extract learning objectives
        # ----------------------------------------------------

        objectives = lesson.get(
            "learning_objectives"
        ) or []

        if not isinstance(objectives, list):
            objectives = [str(objectives)]

        # ----------------------------------------------------
        # Extract lesson segments safely
        # ----------------------------------------------------

        lesson_content = lesson.get(
            "lesson_content"
        ) or {}

        if isinstance(lesson_content, dict):

            segments = (
                lesson_content.get("segments")
                or []
            )

        elif isinstance(lesson_content, list):

            segments = lesson_content

        else:

            segments = []

        # ----------------------------------------------------
        # Build AI prompt
        # ----------------------------------------------------

        prompt = f"""
You are an expert assessment designer for a personalized AI teacher.

Create a final assessment for a student who has completed a lesson.

SUBJECT:
{subject}

TOPIC:
{topic}

LANGUAGE:
{request.language}

LEARNING OBJECTIVES:
{json.dumps(objectives, ensure_ascii=False)}

LESSON CONTENT:
{json.dumps(segments, ensure_ascii=False)}

NUMBER OF QUESTIONS:
{request.number_of_questions}

ASSESSMENT REQUIREMENTS:

1. Cover the important learning objectives from the lesson.

2. Do not focus only on one objective.

3. Use a mixture of question types where appropriate:
   - conceptual
   - short answer
   - problem solving
   - application
   - explain in own words

4. Questions must test understanding, not memorization alone.

5. Questions should match the student's educational level
   and the difficulty of the lesson.

6. Each question MUST contain:

   - question
   - concept
   - question_type
   - correct_answer
   - explanation

7. Use options only for multiple-choice questions.

8. Do not include options for questions that do not need them.

9. The correct answer must be clear enough for an evaluator
   to judge the student's response.

10. Generate EXACTLY {request.number_of_questions} questions.

11. Do not create questions about information that is not
    present in the lesson content or learning objectives.

12. Return ONLY valid JSON.

The response may be either:

[
    {{
        "question": "...",
        "concept": "...",
        "question_type": "...",
        "options": ["...", "..."],
        "correct_answer": "...",
        "explanation": "..."
    }}
]

OR:

{{
    "questions": [
        {{
            "question": "...",
            "concept": "...",
            "question_type": "...",
            "options": ["...", "..."],
            "correct_answer": "...",
            "explanation": "..."
        }}
    ]
}}
"""

        # ----------------------------------------------------
        # Generate using Gemini JSON mode
        # ----------------------------------------------------

        response = generate_json_response(prompt)

        # ----------------------------------------------------
        # Parse questions safely
        # ----------------------------------------------------

        questions = parse_assessment_questions(response)

        # ----------------------------------------------------
        # Ensure requested number of questions
        # ----------------------------------------------------

        if len(questions) < request.number_of_questions:

            raise HTTPException(
                status_code=500,
                detail=(
                    f"AI generated only {len(questions)} valid "
                    f"questions, but {request.number_of_questions} "
                    f"were requested."
                ),
            )

        # Keep exactly the requested number.
        questions = questions[
            :request.number_of_questions
        ]

        # ----------------------------------------------------
        # Generate assessment ID
        # ----------------------------------------------------

        assessment_id = str(uuid4())

        return FinalAssessmentResponse(
            assessment_id=assessment_id,
            student_id=request.student_id,
            lesson_id=request.lesson_id,
            subject=subject,
            topic=topic,
            questions=questions,
        )

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to generate final assessment: "
                f"{str(e)}"
            ),
        )


# ============================================================
# EVALUATE FINAL ASSESSMENT
# ============================================================

@router.post(
    "/evaluate",
    response_model=FinalAssessmentEvaluationResponse,
)
def evaluate_final_assessment(
    request: FinalAssessmentEvaluationRequest,
):
    """
    Evaluate the student's final assessment.

    The AI evaluates each answer conceptually and produces
    personalized feedback.
    """

    try:

        # ----------------------------------------------------
        # Load lesson
        # ----------------------------------------------------

        lesson_result = (
            supabase
            .table("lessons")
            .select(
                "id, student_id, subject, topic, "
                "learning_objectives"
            )
            .eq("id", request.lesson_id)
            .single()
            .execute()
        )

        if not lesson_result.data:
            raise HTTPException(
                status_code=404,
                detail="Lesson not found.",
            )

        lesson = lesson_result.data

        # ----------------------------------------------------
        # Verify ownership
        # ----------------------------------------------------

        if lesson.get("student_id") != request.student_id:
            raise HTTPException(
                status_code=403,
                detail="Lesson does not belong to this student.",
            )

        # ----------------------------------------------------
        # Validate answers
        # ----------------------------------------------------

        if not request.answers:

            raise HTTPException(
                status_code=400,
                detail="No assessment answers were provided.",
            )

        results = []

        # ----------------------------------------------------
        # Evaluate each answer
        # ----------------------------------------------------

        for answer in request.answers:

            prompt = f"""
You are an expert AI teacher evaluating a student's answer.

SUBJECT:
{request.subject}

TOPIC:
{request.topic}

CONCEPT:
{answer.concept}

QUESTION:
{answer.question}

EXPECTED ANSWER:
{answer.correct_answer}

STUDENT ANSWER:
{answer.student_answer}

Evaluate the student's conceptual understanding.

Return ONLY valid JSON:

{{
    "correct": true,
    "score": 0,
    "misconception": null,
    "feedback": "short personalized feedback"
}}

Rules:

1. Compare the student's answer with the expected answer.

2. Do not require the student's wording to exactly match
   the expected answer.

3. Judge conceptual understanding rather than exact wording.

4. Give partial credit when the answer demonstrates partial
   understanding.

5. Identify a misconception when the student's reasoning
   reveals one.

6. The score must be between 0 and 100.

7. "correct" should normally be true when the score is 50
   or higher and false when the score is below 50.

8. Keep feedback constructive and educational.

9. "misconception" must be either a short string describing
   the misconception or null.
"""

            # ------------------------------------------------
            # Generate evaluation
            # ------------------------------------------------

            evaluation_text = generate_json_response(
                prompt
            )

            # ------------------------------------------------
            # Parse evaluation object
            # ------------------------------------------------

            evaluation = parse_json_object(
                evaluation_text,
                "AI returned invalid evaluation JSON.",
            )

            # ------------------------------------------------
            # Score
            # ------------------------------------------------

            score = parse_score(
                evaluation.get("score", 0)
            )

            # ------------------------------------------------
            # Correctness
            # ------------------------------------------------

            correct = parse_boolean(
                evaluation.get("correct"),
                default=(score >= 50),
            )

            # ------------------------------------------------
            # Misconception
            # ------------------------------------------------

            misconception = evaluation.get(
                "misconception"
            )

            if misconception is not None:

                misconception = str(
                    misconception
                ).strip()

                if not misconception:
                    misconception = None

            # ------------------------------------------------
            # Feedback
            # ------------------------------------------------

            feedback_text = evaluation.get(
                "feedback"
            )

            if feedback_text is None:
                feedback_text = (
                    "Review this concept and try the "
                    "question again."
                )

            feedback_text = str(
                feedback_text
            ).strip()

            # ------------------------------------------------
            # Update concept-level progress
            # ------------------------------------------------

            record_concept_answer(
                lesson_id=request.lesson_id,
                student_id=request.student_id,
                concept=answer.concept,
                correct=correct,
                score=score,
                misconception_description=misconception,
            )

            # ------------------------------------------------
            # Concept status
            # ------------------------------------------------

            concept_status = get_assessment_status(
                score
            )

            results.append(
                ConceptAssessmentResult(
                    concept=answer.concept,
                    score=score,
                    status=concept_status,
                    misconception=misconception,
                )
            )

            # ------------------------------------------------
            # Store assessment result
            # ------------------------------------------------

            insert_result = (
                supabase
                .table("assessment_results")
                .insert(
                    {
                        "student_id": request.student_id,
                        "lesson_id": request.lesson_id,
                        "subject": request.subject,
                        "topic": request.topic,
                        "concept": answer.concept,
                        "question": answer.question,
                        "student_answer": answer.student_answer,
                        "correct_answer": answer.correct_answer,
                        "is_correct": correct,
                        "score": score,
                        "feedback": feedback_text,
                        "misconception": misconception,
                    }
                )
                .execute()
            )

            if not insert_result.data:

                raise RuntimeError(
                    "Failed to save assessment result."
                )

        # ----------------------------------------------------
        # Overall score
        # ----------------------------------------------------

        overall_score = round(
            sum(
                result.score
                for result in results
            )
            / len(results),
            2,
        )

        # ----------------------------------------------------
        # Correct answers
        # ----------------------------------------------------

        correct_answers = sum(
            1
            for result in results
            if result.score >= 50
        )

        # ----------------------------------------------------
        # Overall status
        # ----------------------------------------------------

        overall_status = get_assessment_status(
            overall_score
        )

        # ----------------------------------------------------
        # Strengths
        # ----------------------------------------------------

        strengths = list(
            dict.fromkeys(
                result.concept
                for result in results
                if result.score >= 85
            )
        )

        # ----------------------------------------------------
        # Weaknesses
        # ----------------------------------------------------

        weaknesses = list(
            dict.fromkeys(
                result.concept
                for result in results
                if result.score < 70
            )
        )

        # ----------------------------------------------------
        # Update student progress
        # ----------------------------------------------------

        update_final_assessment_progress(
            student_id=request.student_id,
            subject=request.subject,
            topic=request.topic,
            overall_score=overall_score,
            results=results,
        )

        # ----------------------------------------------------
        # Personalized feedback
        # ----------------------------------------------------

        feedback = (
            f"You scored {overall_score:.1f}% "
            "on the final assessment. "
        )

        if strengths:

            feedback += (
                "You demonstrated strong understanding of: "
                + ", ".join(strengths)
                + ". "
            )

        if weaknesses:

            feedback += (
                "You should continue practising: "
                + ", ".join(weaknesses)
                + "."
            )

        else:

            feedback += (
                "You demonstrated a strong understanding "
                "of the assessed concepts."
            )

        # ----------------------------------------------------
        # Return evaluation
        # ----------------------------------------------------

        return FinalAssessmentEvaluationResponse(
            student_id=request.student_id,
            lesson_id=request.lesson_id,
            subject=request.subject,
            topic=request.topic,
            overall_score=overall_score,
            status=overall_status,
            total_questions=len(results),
            correct_answers=correct_answers,
            concept_results=results,
            strengths=strengths,
            weaknesses=weaknesses,
            personalized_feedback=feedback,
        )

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to evaluate final assessment: "
                f"{str(e)}"
            ),
        )


# ============================================================
# ASSESSMENT REPORT
# ============================================================

@router.get(
    "/report/{lesson_id}",
    response_model=AssessmentReportResponse,
)
def get_assessment_report(
    lesson_id: str,
    student_id: str,
):
    """
    Return the assessment report for a student's lesson.
    """

    try:

        # ----------------------------------------------------
        # Verify lesson
        # ----------------------------------------------------

        lesson_result = (
            supabase
            .table("lessons")
            .select(
                "id, student_id, subject, topic"
            )
            .eq("id", lesson_id)
            .single()
            .execute()
        )

        if not lesson_result.data:

            raise HTTPException(
                status_code=404,
                detail="Lesson not found.",
            )

        lesson = lesson_result.data

        if lesson.get("student_id") != student_id:

            raise HTTPException(
                status_code=403,
                detail="Lesson does not belong to this student.",
            )

        # ----------------------------------------------------
        # Get assessment results
        # ----------------------------------------------------

        assessment_result = (
            supabase
            .table("assessment_results")
            .select(
                "question, concept, student_answer, "
                "correct_answer, is_correct, score, "
                "feedback, misconception"
            )
            .eq("lesson_id", lesson_id)
            .eq("student_id", student_id)
            .execute()
        )

        assessments = (
            assessment_result.data or []
        )

        if not assessments:

            raise HTTPException(
                status_code=404,
                detail=(
                    "No assessment results found "
                    "for this lesson."
                ),
            )

        # ----------------------------------------------------
        # Calculate scores
        # ----------------------------------------------------

        scores = []

        for assessment in assessments:

            score = assessment.get("score")

            if score is None:
                continue

            scores.append(
                parse_score(score)
            )

        if scores:

            overall_score = round(
                sum(scores) / len(scores),
                2,
            )

        else:

            overall_score = 0.0

        # ----------------------------------------------------
        # Overall status
        # ----------------------------------------------------

        status = get_assessment_status(
            overall_score
        )

        # ----------------------------------------------------
        # Correct answer count
        # ----------------------------------------------------

        correct_answers = sum(
            1
            for assessment in assessments
            if parse_boolean(
                assessment.get("is_correct"),
                default=False,
            )
        )

        # ----------------------------------------------------
        # Concept results
        # ----------------------------------------------------

        concept_results = []

        strengths = []
        weaknesses = []
        misconceptions = []

        for assessment in assessments:

            score_value = assessment.get(
                "score"
            )

            if score_value is None:
                continue

            score = parse_score(
                score_value
            )

            concept = (
                assessment.get("concept")
                or "Unknown Concept"
            )

            feedback_text = (
                assessment.get("feedback")
            )

            misconception = (
                assessment.get("misconception")
            )

            concept_status = get_assessment_status(
                score
            )

            concept_results.append(
                ConceptAssessmentResult(
                    concept=concept,
                    score=score,
                    status=concept_status,
                    misconception=misconception,
                )
            )

            if score >= 85:

                if (
                    feedback_text
                    and feedback_text not in strengths
                ):
                    strengths.append(
                        feedback_text
                    )

            elif score < 70:

                if (
                    feedback_text
                    and feedback_text not in weaknesses
                ):
                    weaknesses.append(
                        feedback_text
                    )

            if (
                misconception
                and misconception not in misconceptions
            ):
                misconceptions.append(
                    misconception
                )

        # ----------------------------------------------------
        # Personalized report feedback
        # ----------------------------------------------------

        feedback = (
            f"You scored {overall_score:.1f}% "
            "on your final assessment. "
        )

        if status == "mastered":

            feedback += (
                "Excellent work. You have demonstrated "
                "strong understanding of the assessed concepts."
            )

        elif status == "proficient":

            feedback += (
                "Good work. You understand most of the concepts, "
                "but a little more practice will strengthen "
                "your mastery."
            )

        elif status == "learning":

            feedback += (
                "You are making progress. Review the weaker "
                "concepts and practise a few more problems."
            )

        else:

            feedback += (
                "You need more practice with the assessed "
                "concepts. Review the explanations and try "
                "the questions again."
            )

        # ----------------------------------------------------
        # Return report
        # ----------------------------------------------------

        return AssessmentReportResponse(
            student_id=student_id,
            lesson_id=lesson_id,
            subject=lesson.get("subject", ""),
            topic=lesson.get("topic", ""),
            overall_score=overall_score,
            status=status,
            total_questions=len(assessments),
            correct_answers=correct_answers,
            strengths=strengths,
            weaknesses=weaknesses,
            misconceptions=misconceptions,
            concept_results=concept_results,
            personalized_feedback=feedback,
        )

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to generate assessment report: "
                f"{str(e)}"
            ),
        )