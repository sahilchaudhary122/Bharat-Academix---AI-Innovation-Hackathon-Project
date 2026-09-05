from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.sadtalker_service import generate_talking_avatar
from services.avatar_service import generate_avatar

router = APIRouter(
    prefix="/api/avatar",
    tags=["AI Avatar"]
)   


class AvatarVideoRequest(BaseModel):
    audio_file: str
    avatar_image: str | None = None
    size: int = 256


@router.post("/video")
def generate_avatar_video(request: AvatarVideoRequest):
    try:
        output_file = generate_talking_avatar(
            audio_file=request.audio_file,
            avatar_image=request.avatar_image,
            size=request.size,
        )

        return {
            "success": True,
            "message": "Talking AI teacher video generated successfully.",
            "output_file": output_file,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Avatar video generation failed: {str(e)}",
        )
class AvatarRequest(BaseModel):
    name: str = "AI Teacher"
    subject: str = "General Education"
    style: str = "friendly professional"

@router.post("/generate")
def create_avatar(request: AvatarRequest):

    try:
        output_file = generate_avatar(
            name=request.name,
            subject=request.subject,
            style=request.style,
        )

        return {
            "success": True,
            "message": "AI teacher avatar generated successfully.",
            "output_file": output_file,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Avatar generation failed: {str(e)}"
        )