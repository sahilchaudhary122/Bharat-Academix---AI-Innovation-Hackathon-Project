from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from media.media_service import (
    convert_audio_to_mp3,
    extract_audio_from_video,
    merge_audio_with_video,
)
from services.gemini_service import translate_text
class MergeRequest(BaseModel):
    video_file: str
    audio_file: str
class TranslationRequest(BaseModel):
    text: str = Field(min_length=1)
    target_language: str = Field(min_length=1)

router = APIRouter(
    prefix="/api/media",
    tags=["Media"]
)


class AudioRequest(BaseModel):
    input_file: str


class VideoAudioRequest(BaseModel):
    video_file: str


class MergeRequest(BaseModel):
    video_file: str
    audio_file: str


@router.post("/convert-audio")
def convert_audio(request: AudioRequest):

    try:
        output_file = convert_audio_to_mp3(
            request.input_file
        )

        return {
            "success": True,
            "message": "Audio converted successfully.",
            "output_file": output_file
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Audio conversion failed: {str(e)}"
        )


@router.post("/extract-audio")
def extract_audio(request: VideoAudioRequest):

    try:
        output_file = extract_audio_from_video(
            request.video_file
        )

        return {
            "success": True,
            "message": "Audio extracted successfully.",
            "output_file": output_file
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Audio extraction failed: {str(e)}"
        )


@router.post("/merge")
def merge_media(request: MergeRequest):

    try:
        output_file = merge_audio_with_video(
            request.video_file,
            request.audio_file
        )

        return {
            "success": True,
            "message": "Audio and video merged successfully.",
            "output_file": output_file
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Media merge failed: {str(e)}"
        )

@router.post("/translate-text")
def translate_media_text(request: TranslationRequest):

    try:
        translated_text = translate_text(
            request.text,
            request.target_language
        )

        return {
            "success": True,
            "message": "Text translated successfully.",
            "target_language": request.target_language,
            "translated_text": translated_text
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Translation failed: {str(e)}"
        )