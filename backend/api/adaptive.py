from fastapi import APIRouter, HTTPException
from models.teacher_agent import TeacherAgentRequest
from database.supabase_client import supabase
from services.stt_service import transcribe_audio
from services.teacher_agent_service import (
    get_teacher_next_step,
    orchestrate_teacher,
)

from models.adaptive import (
    EvaluateAnswerRequest,
    EvaluationResult,
    AdaptRequest,
    AdaptiveResponse,
    SpeechAnswerRequest,
    SpeechAnswerResponse,
)

from services.adaptive_service import (
    evaluate_student_answer,
    generate_adaptive_response,
)

from services.lesson_state_service import (
    record_answer,
    move_to_next_concept,
    advance_to_next_segment,
    get_lesson_state,
    record_adaptive_action,
)

from services.concept_progress_service import (
    record_concept_answer,
)


router = APIRouter(
    prefix="/api/lesson",
    tags=["Adaptive Teaching"],
)


# ============================================================
# STUDENT LANGUAGE RESOLUTION
# ============================================================

def get_student_language(
    student_id: str,
    requested_language: str | None,
) -> str:
    """
    Resolve the teaching language for a student.

    Priority:
    1. Explicit language provided in the request
    2. Student's preferred language from profile
    3. English fallback
    """

    # Explicit request language has highest priority
    if requested_language:
        return requested_language

    # Otherwise get the student's preferred language
    student_result = (
        supabase
        .table("students")
        .select("preferred_language")
        .eq("id", student_id)
        .single()
        .execute()
    )

    student = student_result.data

    if not student:
        raise ValueError("Student not found.")

    return student.get("preferred_language") or "English"


# ============================================================
# GET CURRENT TEACHER AGENT STATE
# ============================================================

@router.get("/{lesson_id}/state")
def get_teacher_state(
    lesson_id: str,
    student_id: str,
):
    """
    Return the current Teacher Agent state for a lesson.
    """

    try:
        lesson_state = get_lesson_state(
            lesson_id=lesson_id,
            student_id=student_id,
        )

        if not lesson_state:
            raise HTTPException(
                status_code=404,
                detail="Lesson state not found.",
            )

        return lesson_state

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve lesson state: {str(e)}",
        )


# ============================================================
# EVALUATE STUDENT ANSWER
# ============================================================

@router.post(
    "/evaluate",
    response_model=EvaluationResult,
)
def evaluate_answer(
    request: EvaluateAnswerRequest,
):
    """
    Evaluate the student's answer.

    Language is resolved automatically from the student profile
    when it is not explicitly provided in the request.
    """

    try:
        # -----------------------------------------------------
        # Resolve teaching language
        # -----------------------------------------------------

        language = get_student_language(
            student_id=request.student_id,
            requested_language=request.language,
        )

        # -----------------------------------------------------
        # AI answer evaluation
        # -----------------------------------------------------

        result = evaluate_student_answer(
            concept=request.concept,
            question=request.question,
            student_answer=request.student_answer,
            expected_answer=request.expected_answer,
            language=language,
            subject=request.subject,
            topic=request.topic,
            document_id=request.document_id,
        )

        concept_progress = {}

        # -----------------------------------------------------
        # Update persistent lesson state
        # -----------------------------------------------------

        if request.lesson_id:
            record_answer(
                lesson_id=request.lesson_id,
                student_id=request.student_id,
                correct=result.get("correct", False),
                score=result.get("score", 0),
                misconception_description=result.get(
                    "misconception_description"
                ),
                next_action=result.get("next_action"),
            )

            # -------------------------------------------------
            # Record performance for the specific concept
            # -------------------------------------------------

            concept_progress = record_concept_answer(
                lesson_id=request.lesson_id,
                student_id=request.student_id,
                concept=request.concept,
                correct=result.get("correct", False),
                score=result.get("score", 0),
                misconception_description=result.get(
                    "misconception_description"
                ),
            )

            # -------------------------------------------------
            # Teacher Agent progression
            # -------------------------------------------------

            next_action = result.get("next_action")

            # 1. Concept mastered → move to next concept
            if (
                concept_progress.get("status") == "mastered"
                and next_action == "NEXT_CONCEPT"
            ):
                move_to_next_concept(
                    lesson_id=request.lesson_id,
                    student_id=request.student_id,
                )

            # 2. Student is progressing → move to next segment
            elif next_action == "CONTINUE":
                advance_to_next_segment(
                    lesson_id=request.lesson_id,
                    student_id=request.student_id,
                )

            # 3. Adaptive actions are handled by /adapt
            #
            # Examples:
            # SIMPLIFY
            # REEXPLAIN
            # ANALOGY
            # EXAMPLE
            # LOWER_DIFFICULTY
            # INCREASE_DIFFICULTY
            # NEW_QUESTION

        return result

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Answer evaluation failed: {str(e)}",
        )


# ============================================================
# GENERATE ADAPTIVE TEACHING RESPONSE
# ============================================================

@router.post(
    "/adapt",
    response_model=AdaptiveResponse,
)
def adapt_lesson(
    request: AdaptRequest,
):
    """
    Generate an adaptive teaching response.

    Language is resolved automatically from the student profile
    when it is not explicitly provided in the request.
    """

    try:
        # -----------------------------------------------------
        # Resolve teaching language
        # -----------------------------------------------------

        language = get_student_language(
            student_id=request.student_id,
            requested_language=request.language,
        )

        # -----------------------------------------------------
        # Get current lesson state
        # -----------------------------------------------------

        lesson_state = None

        if request.lesson_id:
            lesson_state = get_lesson_state(
                lesson_id=request.lesson_id,
                student_id=request.student_id,
            )

        # -----------------------------------------------------
        # Generate adaptive response
        # -----------------------------------------------------

        result = generate_adaptive_response(
            concept=request.concept,
            question=request.question,
            student_answer=request.student_answer,
            evaluation=request.evaluation.model_dump(),
            language=language,
            difficulty=(
                lesson_state.get(
                    "difficulty",
                    request.difficulty,
                )
                if lesson_state
                else request.difficulty
            ),
            subject=request.subject,
            topic=request.topic,
            document_id=request.document_id,
            lesson_state=lesson_state,
            student_id=request.student_id,
            lesson_id=request.lesson_id,
        )

        # -----------------------------------------------------
        # Save adaptive action to lesson state
        # -----------------------------------------------------

        if request.lesson_id:
            record_adaptive_action(
                lesson_id=request.lesson_id,
                student_id=request.student_id,
                action=result.get(
                    "action",
                    "REEXPLAIN",
                ),
                difficulty=result.get("difficulty"),
            )

        return result

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Adaptive response failed: {str(e)}",
        )


# ============================================================
# GET NEXT TEACHER STEP
# ============================================================

@router.get("/{lesson_id}/next")
def get_next_teacher_step(
    lesson_id: str,
    student_id: str,
):
    """
    Return the next teaching step selected by the Teacher Agent.
    """

    try:
        return get_teacher_next_step(
            lesson_id=lesson_id,
            student_id=student_id,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e),
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to determine next teaching step: {str(e)}",
        )


# ============================================================
# ADVANCE TO NEXT LESSON SEGMENT
# ============================================================

@router.post("/{lesson_id}/next-segment")
def advance_teacher_segment(
    lesson_id: str,
    student_id: str,
):
    """
    Advance the Teacher Agent to the next lesson segment.
    """

    try:
        return advance_to_next_segment(
            lesson_id=lesson_id,
            student_id=student_id,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e),
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to advance lesson segment: "
                f"{str(e)}"
            ),
        )


# ============================================================
# MAIN TEACHER AGENT
# ============================================================

@router.post("/{lesson_id}/teacher")
def teacher_agent(
    lesson_id: str,
    request: TeacherAgentRequest,
):
    """
    Main Teacher Agent orchestration endpoint.

    Uses the explicitly provided language when available.
    Otherwise, uses the student's preferred language from
    the student profile.
    """

    try:
        # -----------------------------------------------------
        # Resolve teaching language
        # -----------------------------------------------------

        language = get_student_language(
            student_id=request.student_id,
            requested_language=request.language,
        )

        # -----------------------------------------------------
        # Run Teacher Agent
        # -----------------------------------------------------

        return orchestrate_teacher(
            lesson_id=lesson_id,
            student_id=request.student_id,
            language=language,
            difficulty=request.difficulty,
        )

    except HTTPException:
        raise

    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e),
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Teacher Agent failed: {str(e)}",
        )
        
# ============================================================
# SPEECH ANSWER → STT → EVALUATION → ADAPTATION
# ============================================================

@router.post(
    "/speech-answer",
    response_model=SpeechAnswerResponse,
)
def process_speech_answer(
    request: SpeechAnswerRequest,
):
    """
    Process a student's spoken answer.

    Flow:

        Audio
          ↓
        STT
          ↓
        Answer Evaluation
          ↓
        Adaptive Teaching
    """

    try:
        # -----------------------------------------------------
        # 1. Convert speech to text
        # -----------------------------------------------------

        transcription = transcribe_audio(
            request.input_file
        )

        if not transcription:
            raise HTTPException(
                status_code=400,
                detail="Speech transcription returned empty text.",
            )

        # -----------------------------------------------------
        # 2. Resolve language
        # -----------------------------------------------------

        language = get_student_language(
            student_id=request.student_id,
            requested_language=request.language,
        )

        # -----------------------------------------------------
        # 3. Evaluate the transcribed answer
        # -----------------------------------------------------

        evaluation_result = evaluate_student_answer(
            concept=request.concept,
            question=request.question,
            student_answer=transcription,
            expected_answer=request.expected_answer,
            language=language,
            subject=request.subject,
            topic=request.topic,
            document_id=request.document_id,
        )

        # -----------------------------------------------------
        # 4. Update lesson state
        # -----------------------------------------------------

        if request.lesson_id:

            record_answer(
                lesson_id=request.lesson_id,
                student_id=request.student_id,
                correct=evaluation_result.get(
                    "correct",
                    False,
                ),
                score=evaluation_result.get(
                    "score",
                    0,
                ),
                misconception_description=evaluation_result.get(
                    "misconception_description"
                ),
                next_action=evaluation_result.get(
                    "next_action"
                ),
            )

            # -------------------------------------------------
            # Record concept performance
            # -------------------------------------------------

            concept_progress = record_concept_answer(
                lesson_id=request.lesson_id,
                student_id=request.student_id,
                concept=request.concept,
                correct=evaluation_result.get(
                    "correct",
                    False,
                ),
                score=evaluation_result.get(
                    "score",
                    0,
                ),
                misconception_description=evaluation_result.get(
                    "misconception_description"
                ),
            )

            next_action = evaluation_result.get(
                "next_action"
            )

            # -------------------------------------------------
            # Move to next concept if mastered
            # -------------------------------------------------

            if (
                concept_progress.get("status") == "mastered"
                and next_action == "NEXT_CONCEPT"
            ):
                move_to_next_concept(
                    lesson_id=request.lesson_id,
                    student_id=request.student_id,
                )

            # -------------------------------------------------
            # Continue current lesson
            # -------------------------------------------------

            elif next_action == "CONTINUE":
                advance_to_next_segment(
                    lesson_id=request.lesson_id,
                    student_id=request.student_id,
                )

        # -----------------------------------------------------
        # 5. Generate adaptive response when needed
        # -----------------------------------------------------

        adaptive_result = None

        adaptive_actions = {
            "SIMPLIFY",
            "REEXPLAIN",
            "ANALOGY",
            "EXAMPLE",
            "LOWER_DIFFICULTY",
            "INCREASE_DIFFICULTY",
            "NEW_QUESTION",
        }

        next_action = evaluation_result.get(
            "next_action"
        )

        if next_action in adaptive_actions:

            lesson_state = None

            if request.lesson_id:
                lesson_state = get_lesson_state(
                    lesson_id=request.lesson_id,
                    student_id=request.student_id,
                )

            adaptive_result = generate_adaptive_response(
                concept=request.concept,
                question=request.question,
                student_answer=transcription,
                evaluation=evaluation_result,
                language=language,
                difficulty=(
                    lesson_state.get(
                        "difficulty",
                        request.difficulty,
                    )
                    if lesson_state
                    else request.difficulty
                ),
                subject=request.subject,
                topic=request.topic,
                document_id=request.document_id,
                lesson_state=lesson_state,
                student_id=request.student_id,
                lesson_id=request.lesson_id,
            )

            # -------------------------------------------------
            # Save adaptive action
            # -------------------------------------------------

            if request.lesson_id:
                record_adaptive_action(
                    lesson_id=request.lesson_id,
                    student_id=request.student_id,
                    action=adaptive_result.get(
                        "action",
                        next_action,
                    ),
                    difficulty=adaptive_result.get(
                        "difficulty"
                    ),
                )

        # -----------------------------------------------------
        # 6. Return complete result
        # -----------------------------------------------------

        return SpeechAnswerResponse(
            transcription=transcription,
            evaluation=EvaluationResult(
                **evaluation_result
            ),
            adaptive_response=(
                AdaptiveResponse(
                    **adaptive_result
                )
                if adaptive_result
                else None
            ),
        )

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Speech answer processing failed: {str(e)}",
        )