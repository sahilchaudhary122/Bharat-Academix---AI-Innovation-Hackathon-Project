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

def create_lesson_plan(request: LessonRequest) -> LessonPlan:

    prompt = f"""
You are an expert personalized AI teacher.
Create a personalized learning lesson for the following student.
Student name: {request.student_name}
Grade: {request.grade}
Subject: {request.subject}
Topic: {request.topic}
Current knowledge level: {request.current_level}
Preferred language: {request.language}
Learning goal: {request.learning_goal}
Available time: {request.available_time_minutes} minutes

Requirements:

1. Adapt the explanation to the student's grade and knowledge level.
2. Use simple and clear language.
3. Focus on the student's learning goal.
4. Divide the lesson into small learning segments.
5. Include explanations and examples.
6. Keep the total lesson within the available time.
7. End with a short assessment or practice activity.
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