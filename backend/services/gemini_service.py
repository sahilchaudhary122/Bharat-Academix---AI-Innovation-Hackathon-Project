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

11. Keep the total lesson within the available time.

12. End with a short assessment or practice activity.

13. Return ONLY the structured lesson plan matching the LessonPlan schema.
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