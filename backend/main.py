from fastapi import FastAPI
from pydantic import BaseModel

from services.gemini_service import generate_response
from api.lessons import router as lesson_router


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