import os
from dotenv import load_dotenv
from google import genai
from models.lesson import LessonRequest, LessonPlan

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY is not configured.")

client = genai.Client(api_key=api_key)

def generate_response(prompt: str) -> str:
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt,
    )

    return response.text

def generate_json_response(prompt: str) -> str:
    """
    Generate a JSON response using Gemini.

    Temporary 503/UNAVAILABLE errors are retried automatically.
    """

    import time

    max_attempts = 3
    delay_seconds = 2

    last_error = None

    for attempt in range(1, max_attempts + 1):

        try:
            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                },
            )

            if not response.text:
                raise RuntimeError(
                    "Gemini returned an empty response."
                )

            return response.text

        except Exception as e:

            last_error = e

            error_text = str(e)

            # Retry only temporary service-availability errors.
            temporary_error = (
                "503" in error_text
                or "UNAVAILABLE" in error_text
                or "high demand" in error_text
            )

            if not temporary_error:
                raise

            # If this was the last attempt, stop retrying.
            if attempt == max_attempts:
                break

            # Exponential backoff:
            # attempt 1 -> 2 seconds
            # attempt 2 -> 4 seconds
            time.sleep(delay_seconds)

            delay_seconds *= 2

    raise RuntimeError(
        "Gemini is temporarily unavailable after "
        f"{max_attempts} attempts. "
        f"Last error: {last_error}"
    )
    
def create_lesson_plan(
    request: LessonRequest,
    student_context=None
) -> LessonPlan:

    if student_context is None:
        student_context = {}

    prompt = f"""
You are an expert personalized AI teacher.

Create a personalized learning lesson for the following student.

STUDENT INFORMATION:
{student_context.get("student", {})}

PERSONAL LEARNING PREFERENCES:
Teaching style: {student_context.get("student", {}).get("teaching_style", "balanced")}
Available learning time: {student_context.get("student", {}).get("available_time") or request.available_time_minutes} minutes
Desired depth: {student_context.get("student", {}).get("desired_depth", "standard")}

CURRENT STUDENT PROGRESS:
{student_context.get("progress", [])}

PREVIOUS ASSESSMENTS:
{student_context.get("previous_assessments", [])}

PREVIOUS LESSONS:
{student_context.get("previous_lessons", [])}


CURRENT LESSON REQUEST:
Student name: {request.student_name}
Grade: {request.grade}
Subject: {request.subject}
Topic: {request.topic}
Current knowledge level: {request.current_level}
Preferred language: {request.language}
Learning goal: {request.learning_goal}
Available time: {request.available_time_minutes} minutes

LEARNING OBJECTIVE REQUIREMENTS:

The lesson plan's learning_objectives field is the canonical list
of learning objectives for this lesson.

Every segment MUST reference one of these objectives using
objective_index.

The index is zero-based.

Example:

learning_objectives:
[
    "Understand scalar and vector quantities",
    "Calculate distance and displacement",
    "Calculate average speed and velocity"
]

Valid segment mapping:

objective_index = 0 → scalar and vector quantities
objective_index = 1 → distance and displacement
objective_index = 2 → average speed and velocity

Multiple segments may use the same objective_index.

PERSONALIZATION REQUIREMENTS:

1. Analyze the student's current progress before creating the lesson.

2. Use previous assessment results to identify concepts the student
   understands and concepts where the student needs improvement.

3. Pay special attention to the student's weaknesses and misconceptions.

4. Use the student's strengths to build confidence and connect new
   concepts with things the student already understands.

5. Avoid unnecessarily repeating previous lessons unless repetition
   is useful for correcting a weakness or misconception.

6. Adapt the difficulty to the student's actual performance.

7. Focus the lesson on the student's learning goal.

8. Use simple and clear language appropriate for the student's grade
   and current knowledge level.

9. Divide the lesson into small learning segments.

10. Include explanations and examples.

11. Keep the total lesson within the student's available learning time.

12. Adapt the teaching approach to the student's teaching style.

13. Adapt the depth and detail of explanations to the student's desired depth.

14. If the teaching style is visual, emphasize diagrams, visual descriptions,
    demonstrations, and structured visual explanations.

15. If the teaching style is example_based, emphasize worked examples,
    real-world examples, and step-by-step demonstrations.

16. If the teaching style is conceptual, emphasize intuitive explanations,
    relationships between concepts, and why the ideas work.

17. If the teaching style is practice_based, emphasize guided practice,
    progressively harder questions, and problem-solving activities.

18. If the teaching style is balanced, combine explanations, examples,
    demonstrations, and practice.

19. Respect the student's available learning time when deciding the number
    and duration of lesson segments.

20. For basic depth, keep explanations concise and focus on essential ideas.

21. For standard depth, provide clear explanations, examples, and practice.

22. For deep depth, provide more detailed reasoning, connections,
    examples, and challenging practice while still respecting the
    available learning time.

23. End with a short assessment or practice activity.


SEGMENT STRUCTURE REQUIREMENTS:

13. Every teaching segment MUST be linked to exactly one learning
    objective using objective_index.

14. objective_index MUST be zero-based:
    0 = first learning objective,
    1 = second learning objective,
    2 = third learning objective, and so on.

15. Use the learning_objectives field as the canonical list of
    concepts/objectives to teach.

16. A learning objective may contain multiple teaching segments.
    Segments for the same objective should form a coherent sequence.

17. Do NOT treat every teaching segment as a new concept.
    Segments such as explanation, analogy, example, practice,
    question, correction, and assessment are teaching activities
    belonging to a learning objective.

18. The segment concept should describe the specific concept being
    taught within its assigned learning objective.

19. Order the segments according to the natural teaching flow:
    introduction/concept → explanation → example/demonstration →
    question/practice → evaluation/correction when appropriate.

20. Ensure that the final teaching segments provide coverage of
    the learning objectives within the available lesson time.


OUTPUT REQUIREMENT:

21. Return ONLY the structured lesson plan matching the LessonPlan schema.
"""

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": LessonPlan,
        },
    )

    return response.parsed

def translate_text(text: str, target_language: str) -> str:
    """
    Translate educational text into the requested language
    using Gemini.
    """

    if not text.strip():
        raise ValueError("Text cannot be empty.")

    if not target_language.strip():
        raise ValueError("Target language cannot be empty.")

    prompt = f"""
Translate the following educational content into {target_language}.

Requirements:
1. Preserve the original meaning.
2. Use simple and clear language suitable for students.
3. Keep formulas, numbers, units, and technical terms accurate.
4. Do not add explanations that are not present in the original.
5. Return only the translated text.

TEXT:
{text}
"""

    return generate_response(prompt).strip()