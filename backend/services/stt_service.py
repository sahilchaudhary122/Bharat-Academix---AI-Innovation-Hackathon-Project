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
    Transcribe an audio file using Gemini 3.5 Transcribe.
    """

    input_path = Path(input_file)

    if not input_path.exists():
        raise FileNotFoundError(
            f"Input audio file not found: {input_file}"
        )

    try:
        # Upload audio to Gemini Files API
        audio_file = client.files.upload(
            file=str(input_path)
        )

        # Send uploaded audio to Gemini transcription model
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

        # Gemini Transcribe returns transcription here
        transcription = interaction.output_text

        if not transcription:
            raise RuntimeError(
                "Gemini did not return a transcription."
            )

        return transcription.strip()

    except Exception as e:
        raise RuntimeError(
            f"Gemini transcription failed: {str(e)}"
        )