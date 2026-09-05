import json
from typing import Any, Dict

from services.gemini_service import generate_response
from services.rag_service import get_grounded_context
from services.concept_progress_service import get_concept_progress

VALID_ACTIONS = {
    "CONTINUE",
    "SIMPLIFY",
    "REEXPLAIN",
    "ANALOGY",
    "EXAMPLE",
    "LOWER_DIFFICULTY",
    "INCREASE_DIFFICULTY",
    "NEW_QUESTION",
    "NEXT_CONCEPT",
}


def _extract_json(text: str) -> Dict[str, Any]:
    """
    Safely extract a JSON object from an LLM response.
    """

    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1:
        raise ValueError("AI response did not contain valid JSON.")

    return json.loads(text[start:end + 1])


def evaluate_student_answer(
    concept: str,
    question: str,
    student_answer: str,
    expected_answer: str,
    language: str = "English",
    subject: str = "",
    topic: str = "",
    document_id: str | None = None,
) -> Dict[str, Any]:
    """
    Evaluate conceptual understanding using uploaded learning material
    when a document_id is provided.
    """

    # Retrieve relevant content from the student's uploaded material
    rag = get_grounded_context(
        query=f"""
    Subject: {subject}
    Topic: {topic}
    Concept: {concept}
    Question: {question}
    Student answer: {student_answer}
    """,
        document_id=document_id,
        match_count=5,
    )
    
    prompt = f"""
You are an expert AI teacher and educational evaluator.

Evaluate the student's answer based on conceptual understanding.

Do NOT use exact string matching.

SUBJECT:
{subject}

TOPIC:
{topic}

CONCEPT:
{concept}

QUESTION:
{question}

EXPECTED ANSWER:
{expected_answer}

STUDENT ANSWER:
{student_answer}

TEACHING LANGUAGE:
{language}

UPLOADED LEARNING MATERIAL:
{rag["context"]}

Use the uploaded learning material as the primary source
when evaluating the student's understanding.

        Evaluate:
1. Whether the student's underlying concept is correct.
2. How complete the student's understanding is.
3. Whether a misconception is present.
4. What specifically the student misunderstood.
5. What teaching action should happen next.

NEXT ACTION RULES:

- If the student demonstrates strong conceptual understanding,
  has no meaningful misconception, and the score is 85 or higher,
  choose "NEXT_CONCEPT".

- If the student is mostly correct but has a minor gap,
  choose "EXAMPLE", "ANALOGY", or "NEW_QUESTION" instead of
  immediately moving to the next concept.

- If the student shows partial understanding or has a meaningful
  misconception, choose "REEXPLAIN", "SIMPLIFY", or "ANALOGY".

- If the student's understanding is weak, choose "REEXPLAIN"
  or "SIMPLIFY".

- Do not choose "NEXT_CONCEPT" when a major misconception is present.

The goal is to ensure that the student has demonstrated sufficient
understanding before progressing to the next learning objective.
SCORING:

90-100:
Strong conceptual understanding.

70-89:
Mostly correct with minor gaps.

40-69:
Partial understanding.

1-39:
Major misunderstanding.

0:
No meaningful understanding.

NEXT ACTION OPTIONS:

CONTINUE
SIMPLIFY
REEXPLAIN
ANALOGY
EXAMPLE
LOWER_DIFFICULTY
INCREASE_DIFFICULTY
NEW_QUESTION
NEXT_CONCEPT

If the student has a genuine misconception, identify it explicitly.

Return ONLY valid JSON:

{{
  "correct": true,
  "score": 85,
  "concept": "{concept}",
  "misconception": false,
  "misconception_description": null,
  "feedback": "Clear feedback explaining what the student understood and what could be improved.",
  "next_action": "CONTINUE"
}}
"""

    response = generate_response(prompt)

    result = _extract_json(response)

    result["concept"] = concept

    if result.get("next_action") not in VALID_ACTIONS:
        result["next_action"] = "REEXPLAIN"

    return result


def generate_adaptive_response(
    concept: str,
    question: str,
    student_answer: str,
    evaluation: Dict[str, Any],
    language: str = "English",
    difficulty: str = "beginner",
    subject: str = "",
    topic: str = "",
    document_id: str | None = None,
    lesson_state: Dict[str, Any] | None = None,
    student_id: str | None = None,
    lesson_id: str | None = None,
) -> Dict[str, Any]:
    """
    Generate the next teaching action based on evaluation,
    misconception information and student performance.
    """
    concept_progress = None

    if lesson_id and student_id:
        concept_progress = get_concept_progress(
            lesson_id=lesson_id,
            student_id=student_id,
            concept=concept,
        )
    rag = get_grounded_context(
        query=f"""
    Subject: {subject}
    Topic: {topic}
    Concept: {concept}
    Question: {question}
    Student answer: {student_answer}
    Misconception: {evaluation.get("misconception_description")}
    """,
        document_id=document_id,
        match_count=5,
    )
    state_context = lesson_state or {}

    current_concept = state_context.get(
        "current_concept",
        concept,
    )

    current_segment = state_context.get(
        "current_segment",
        "introduction",
    )

    attempts = state_context.get(
        "attempts",
        0,
    )

    correct_attempts = state_context.get(
        "correct_attempts",
        0,
    )

    mastery_score = state_context.get(
        "mastery_score",
        0,
    )

    misconceptions = state_context.get(
        "misconceptions",
        [],
    )

    last_action = state_context.get(
        "last_action",
    )
    concept_progress_context = (
        json.dumps(
            concept_progress,
            ensure_ascii=False,
            indent=2,
        )
        if concept_progress
        else "No previous progress recorded for this concept."
    )
    prompt = f"""
You are an adaptive AI teacher.

Your job is to decide how to teach the student NEXT.

Do not simply repeat the previous explanation.

CURRENT CONCEPT:
{concept}

PREVIOUS QUESTION:
{question}

STUDENT ANSWER:
{student_answer}

EVALUATION:
{json.dumps(evaluation, ensure_ascii=False, indent=2)}

CURRENT DIFFICULTY:
{difficulty}

PERSISTENT LESSON STATE:

CONCEPT-SPECIFIC PROGRESS:
{concept_progress_context}

CURRENT CONCEPT:
{current_concept}

CURRENT SEGMENT:
{current_segment}

TOTAL ATTEMPTS:
{attempts}

CORRECT ATTEMPTS:
{correct_attempts}

CURRENT MASTERY SCORE:
{mastery_score}

KNOWN MISCONCEPTIONS:
{json.dumps(misconceptions, ensure_ascii=False)}

LAST TEACHING ACTION:
{last_action}

TEACHING LANGUAGE:
{language}

SUBJECT:
{subject}

TOPIC:
{topic}

UPLOADED LEARNING MATERIAL:
{rag["context"]}

Use the uploaded learning material as the primary source.

Do not introduce information that contradicts the uploaded material.
Use concept-specific progress when deciding the next teaching action.

The concept progress is more specific than overall lesson progress.
Pay particular attention to:
- mastery score
- number of attempts
- correct attempts
- learning status
- recorded misconceptions

If the concept is still being learned, do not move on simply because
the latest answer contains some correct information.

If the concept is mastered and the current evaluation confirms strong
understanding, progression may be appropriate.
Use the persistent lesson state to personalize the next teaching step.

Do not assume the student is starting from zero.

If the current concept has already been attempted:
- consider the student's mastery score,
- consider previous attempts,
- consider known misconceptions,
- avoid unnecessarily repeating the same teaching strategy.

If a misconception is already recorded:
- address that misconception directly,
- use a different explanation or analogy when appropriate.

Keep the teaching focused on the current concept unless the student
has demonstrated sufficient mastery to progress.

ADAPTIVE RULES:

If there is a misconception:
- Correct the misconception constructively.
- Prefer a different explanation.
- Use an analogy when useful.
- Give a concrete example.
- Ask a new question to verify understanding.

If understanding is partial:
- Simplify the concept.
- Explain the missing part.
- Give an example.
- Ask another question.

If understanding is strong:
- Do not unnecessarily repeat the concept.
- Increase difficulty where appropriate.
- Continue to the next concept when ready.

The student should feel like they are being taught by a real teacher.

Choose ONE action:

CONTINUE
SIMPLIFY
REEXPLAIN
ANALOGY
EXAMPLE
LOWER_DIFFICULTY
INCREASE_DIFFICULTY
NEW_QUESTION
NEXT_CONCEPT

Return ONLY valid JSON:

{{
  "action": "ANALOGY",
  "concept": "{concept}",
  "strategy": "Describe the teaching strategy used.",
  "explanation": "The new explanation.",
  "example": "A concrete example.",
  "next_question": "A new question that tests understanding.",
  "difficulty": "{difficulty}"
}}
"""

    response = generate_response(prompt)

    result = _extract_json(response)

    if result.get("action") not in VALID_ACTIONS:
        result["action"] = "REEXPLAIN"

    result["concept"] = concept

    return result
