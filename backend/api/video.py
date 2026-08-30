from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.video_service import generate_video


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


@router.post("/generate")
def create_video(request: VideoRequest):

    try:
        output_file = generate_video(
            visual_file=request.visual_file,
            audio_file=request.audio_file,
            duration_seconds=request.duration_seconds,
        )

        return {
            "success": True,
            "message": "Educational video generated successfully.",
            "output_file": output_file,
            "duration_seconds": request.duration_seconds,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Video generation failed: {str(e)}"
        )
