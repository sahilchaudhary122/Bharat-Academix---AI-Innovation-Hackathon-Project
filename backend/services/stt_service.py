import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY is not configured.")

client = genai.Client(api_key=api_key)


def transcribe_audio(input_file: str) -> str:
    """
    Transcribe an audio file.

    Primary:
        gemini-3.5-transcribe

    Fallback:
        gemini-3.5-flash-lite

    The fallback is used when the dedicated transcription model
    returns an empty response.
    """

    input_path = Path(input_file)

    if not input_path.exists():
        raise FileNotFoundError(
            f"Input audio file not found: {input_file}"
        )

    try:
        # ----------------------------------------------------
        # Upload audio
        # ----------------------------------------------------

        audio_file = client.files.upload(
            file=str(input_path)
        )

        # ----------------------------------------------------
        # PRIMARY STT
        # ----------------------------------------------------

        print(
            "Trying Gemini 3.5 Transcribe..."
        )

        interaction = client.interactions.create(
            model="gemini-3.5-transcribe",
            input=[
                {
                    "type": "audio",
                    "uri": audio_file.uri,
                    "mime_type": audio_file.mime_type,
                }
            ],
        )

        transcription = (
            interaction.output_text or ""
        ).strip()

        if transcription:
            print(
                "Primary STT successful."
            )

            return transcription

        print(
            "Primary STT returned empty text."
        )

        # ----------------------------------------------------
        # FALLBACK STT
        # ----------------------------------------------------

        print(
            "Using Gemini 3.5 Flash-Lite fallback..."
        )

        fallback = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=[
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": (
                                "Transcribe the speech in this audio "
                                "exactly. Return only the spoken words "
                                "and nothing else."
                            )
                        },
                        {
                            "file_data": {
                                "file_uri": audio_file.uri,
                                "mime_type": audio_file.mime_type,
                            }
                        },
                    ],
                }
            ],
        )

        fallback_text = (
            fallback.text or ""
        ).strip()

        if fallback_text:
            print(
                "Fallback STT successful."
            )

            return fallback_text

        raise RuntimeError(
            "Both Gemini transcription methods returned empty text."
        )

    except Exception as e:
        raise RuntimeError(
            f"Gemini transcription failed: {str(e)}"
        ) from e