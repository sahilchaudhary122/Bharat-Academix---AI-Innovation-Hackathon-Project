from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from services.gemini_service import generate_response
from api.students import router as student_router
from api.media import router as media_router
from api.lessons import router as lesson_router
from api.progress import router as progress_router
from api.assessment import router as assessment_router
from api.dashboard import router as dashboard_router
from api.speech import router as speech_router
from api.avatar import router as avatar_router
from api.visuals import router as visual_router
from api.video import router as video_router
from pathlib import Path
from fastapi.staticfiles import StaticFiles


app = FastAPI(
    title="Personal AI Teacher API",
    description="Backend API for the Personal AI Teacher",
    version="1.0.0",
)

MEDIA_DIR = Path(__file__).resolve().parent / "media" / "generated"

app.mount(
    "/media",
    StaticFiles(directory=str(MEDIA_DIR)),
    name="media"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
app.include_router(media_router)
app.include_router(progress_router)
app.include_router(assessment_router)
app.include_router(dashboard_router)
app.include_router(speech_router)
app.include_router(avatar_router)
app.include_router(visual_router)
app.include_router(video_router)
