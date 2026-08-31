from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.video_service import generate_video
from services.animation_service import generate_ai_animation


router = APIRouter(
    prefix="/api/video",
    tags=["Video Generation"]
)


class VideoRequest(BaseModel):
    visual_file: str
    audio_file: str | None = None
    duration_seconds: int = Field(
        default=10,
        gt=0,
        le=300
    )


class AnimationRequest(BaseModel):
    subject: str
    topic: str
    grade: str
    concept: str


@router.post("/generate")
def create_video(request: VideoRequest):

    try:
        output_file = generate_video(
            visual_file=request.visual_file,
            audio_file=request.audio_file,
            duration_seconds=request.duration_seconds,
        )

        filename = Path(output_file).name

        return {
            "success": True,
            "message": "Educational video generated successfully.",
            "output_file": f"/media/{filename}",
            "video_url": f"/media/{filename}",
            "duration_seconds": request.duration_seconds,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Video generation failed: {str(e)}"
        )


@router.post("/generate-animation")
def create_animation(request: AnimationRequest):

    try:
        output_file, plan = generate_ai_animation(
            subject=request.subject,
            topic=request.topic,
            grade=request.grade,
            concept=request.concept,
        )

        filename = Path(output_file).name

        return {
            "success": True,
            "message": "AI animated learning video generated successfully.",
            "output_file": f"/media/{filename}",
            "video_url": f"/media/{filename}",
            "plan": plan,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"AI animation generation failed: {str(e)}"
        )
