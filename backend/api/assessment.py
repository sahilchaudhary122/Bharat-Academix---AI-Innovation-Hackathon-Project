from fastapi import APIRouter, HTTPException
from models.assessment import AssessmentRequest, AssessmentResponse
from database.supabase_client import supabase

router = APIRouter(
    prefix="/api/assessment",
    tags=["Assessment"]
)

@router.post("", response_model=AssessmentResponse)
def create_assessment(request: AssessmentRequest):
    try:
        result = (
            supabase
            .table("assessment_results")
            .insert(request.model_dump())
            .execute()
        )

        if not result.data:
            raise HTTPException(
                status_code=500,
                detail="Failed to create assessment"
            )

        return result.data[0]

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create assessment: {str(e)}"
        )