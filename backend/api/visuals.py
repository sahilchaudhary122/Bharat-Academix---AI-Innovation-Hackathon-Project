from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.visual_service import generate_visual


router = APIRouter(
    prefix="/api/visuals",
    tags=["Visual Engine"]
)


class VisualRequest(BaseModel):
    subject: str
    topic: str
    grade: str
    concept: str
    style: str = "educational diagram"


@router.post("/generate")
def create_visual(request: VisualRequest):

    try:
        output_file = generate_visual(
            subject=request.subject,
            topic=request.topic,
            grade=request.grade,
            concept=request.concept,
            style=request.style,
        )

        return {
            "success": True,
            "message": "Educational visual generated successfully.",
            "subject": request.subject,
            "topic": request.topic,
            "output_file": output_file,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Visual generation failed: {str(e)}"
        )
