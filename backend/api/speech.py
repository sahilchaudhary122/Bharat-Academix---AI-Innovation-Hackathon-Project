from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.tts_service import generate_speech
from services.stt_service import transcribe_audio

router = APIRouter(
    prefix="/api/speech",
    tags=["Speech"]
)

class TTSRequest(BaseModel):
    text: str
    voice: str = "Kore"

@router.post("/tts")
def text_to_speech(request: TTSRequest):

    try:
        output_file = generate_speech(
            text=request.text,
            voice=request.voice
        )

        return {
            "success": True,
            "message": "Speech generated successfully.",
            "output_file": output_file
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"TTS generation failed: {str(e)}"
        )

class STTRequest(BaseModel):
    input_file: str

@router.post("/stt")
def speech_to_text(request: STTRequest):

    try:
        text = transcribe_audio(
            request.input_file
        )

        return {
            "success": True,
            "message": "Speech transcribed successfully.",
            "text": text
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"STT transcription failed: {str(e)}"
        )