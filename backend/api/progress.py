from fastapi import APIRouter, HTTPException
from models.progress import ProgressRequest, ProgressResponse
from database.supabase_client import supabase

router = APIRouter(
    prefix="/api/progress",
    tags=["Progress"]
)

@router.post("", response_model=ProgressResponse)
def create_progress(request: ProgressRequest):
    try:
        result = (
            supabase
            .table("student_progress")
            .insert(request.model_dump())
            .execute()
        )

        if not result.data:
            raise HTTPException(
                status_code=500,
                detail="Failed to create progress"
            )

        return result.data[0]

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create progress: {str(e)}"
        )