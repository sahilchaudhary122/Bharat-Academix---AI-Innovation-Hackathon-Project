from fastapi import FastAPI
from pydantic import BaseModel
from api.students import router as student_router
from services.gemini_service import generate_response
from api.lessons import router as lesson_router
from api.progress import router as progress_router
from api.assessment import router as assessment_router
from api.dashboard import router as dashboard_router

app = FastAPI(
    title="Personal AI Teacher API",
    description="Backend API for the Personal AI Teacher",
    version="1.0.0",
)


class AITestRequest(BaseModel):
    prompt: str


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "Personal AI Teacher",
    }


@app.post("/api/test-ai")
def test_ai(request: AITestRequest):
    response = generate_response(request.prompt)

    return {
        "response": response
    }


app.include_router(lesson_router)
app.include_router(student_router)
app.include_router(progress_router)
app.include_router(assessment_router)
app.include_router(dashboard_router)