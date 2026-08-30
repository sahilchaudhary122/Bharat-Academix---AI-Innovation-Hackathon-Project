from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.avatar_service import generate_avatar

router = APIRouter(
    prefix="/api/avatar",
    tags=["AI Avatar"]
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