import os
import base64
import wave
import uuid
from pathlib import Path
from dotenv import load_dotenv
from google import genai

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY is not configured.")

client = genai.Client(api_key=api_key)

MEDIA_DIR = (
    Path(__file__).resolve().parent.parent
    / "media"
    / "generated"
)

MEDIA_DIR.mkdir(parents=True, exist_ok=True)


def _save_wav(
    filename: str,
    pcm_data: bytes,
    channels: int = 1,
    sample_rate: int = 24000,
    sample_width: int = 2,
):
    """
    Save raw PCM audio as a WAV file.
    """

    output_path = MEDIA_DIR / filename

    with wave.open(str(output_path), "wb") as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(sample_width)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm_data)

    return str(output_path)


def generate_speech(
    text: str,
    voice: str = "Kore",
) -> str:
    """
    Convert text into speech using Gemini TTS.
    """

    interaction = client.interactions.create(
        model="gemini-3.1-flash-tts-preview",
        input=f"Synthesize the following text as natural speech:\n\n{text}",
        response_format={
            "type": "audio"
        },
        generation_config={
            "speech_config": [
                {
                    "voice": voice
                }
            ]
        },
    )

    if not interaction.output_audio:
        raise RuntimeError("Gemini did not return audio.")

    audio_data = base64.b64decode(
        interaction.output_audio.data
    )

    filename = f"{uuid.uuid4()}.wav"

    return _save_wav(
        filename,
        audio_data
    )