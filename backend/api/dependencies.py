from fastapi import Depends, HTTPException, Header, Request
from database.supabase_client import supabase

# Development only: Predefined Sahil student ID
SAHIL_STUDENT_ID = "89c9c522-65c8-4743-99e2-60bc9d181a18"

async def get_current_user(request: Request, authorization: str = Header(None)):
    # Development/Demo Bypass
    if not authorization:
        # Check if the requested resource is for Sahil's dashboard OR lesson creation
        if request.url.path in [
            f"/api/students/{SAHIL_STUDENT_ID}/dashboard",
            "/api/lesson/create"
        ]:
            # Return a dummy user object for demo purposes
            class DummyUser:
                id = "demo-user-id"
            return DummyUser()
        
    # Normal Auth Flow
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="Authorization header missing")
        token = authorization.split(" ")[1]
        user = supabase.auth.get_user(token)
        return user.user
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_student(request: Request, student_id: str = None, user = Depends(get_current_user)):
    try:
        # Dev Bypass: if request is for lesson creation, resolve Sahil as student
        if request.url.path == "/api/lesson/create":
            resolved_student_id = SAHIL_STUDENT_ID
        else:
            resolved_student_id = student_id

        # Dev Bypass: if it's Sahil, skip the user_id database check
        if resolved_student_id == SAHIL_STUDENT_ID:
            response = supabase.table("students").select("*").eq("id", resolved_student_id).single().execute()
        else:
            # Normal Auth Flow
            response = supabase.table("students").select("*").eq("id", resolved_student_id).eq("user_id", user.id).single().execute()
            
        if not response.data:
            raise HTTPException(status_code=404, detail="Student not found or access denied")
        return response.data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=404, detail="Student not found or access denied")
