import os
import base64
import wave
import uuid
import subprocess
import shutil
from pathlib import Path

from dotenv import load_dotenv
from google import genai


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY is not configured.")

client = genai.Client(api_key=api_key)


# ============================================================
# MEDIA DIRECTORY
# ============================================================

MEDIA_DIR = (
    Path(__file__).resolve().parent.parent
    / "media"
    / "generated"
)

MEDIA_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# WAV HELPER
# ============================================================

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


# ============================================================
# GEMINI TTS
# ============================================================

def _generate_gemini_speech(
    text: str,
    voice: str = "Kore",
) -> str:
    """
    Generate speech using Gemini TTS.
    """

    interaction = client.interactions.create(
        model="gemini-3.1-flash-tts-preview",
        input=(
            "Synthesize the following text as natural, "
            "clear educational speech:\n\n"
            f"{text}"
        ),
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

    filename = f"gemini_tts_{uuid.uuid4()}.wav"

    return _save_wav(
        filename,
        audio_data
    )


# ============================================================
# LOCAL MACOS TTS FALLBACK
# ============================================================

def _generate_macos_speech(
    text: str,
) -> str:
    """
    Generate speech locally using macOS `say`.

    This is a fallback when Gemini TTS is unavailable
    or the Gemini quota has been exceeded.
    """

    say_path = shutil.which("say")

    if not say_path:
        raise RuntimeError(
            "macOS 'say' command is not available."
        )

    ffmpeg_path = shutil.which("ffmpeg")

    if not ffmpeg_path:
        raise RuntimeError(
            "ffmpeg is required for local TTS fallback."
        )

    unique_id = uuid.uuid4()

    aiff_path = MEDIA_DIR / f"local_tts_{unique_id}.aiff"
    wav_path = MEDIA_DIR / f"local_tts_{unique_id}.wav"

    try:

        # ----------------------------------------------------
        # Generate speech using macOS speech engine
        # ----------------------------------------------------

        subprocess.run(
            [
                say_path,
                "-o",
                str(aiff_path),
                text,
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        # ----------------------------------------------------
        # Convert AIFF → WAV
        # ----------------------------------------------------

        subprocess.run(
            [
                ffmpeg_path,
                "-y",
                "-i",
                str(aiff_path),
                "-ar",
                "24000",
                "-ac",
                "1",
                "-sample_fmt",
                "s16",
                str(wav_path),
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        if not wav_path.exists():
            raise RuntimeError(
                "Local TTS WAV file was not created."
            )

        return str(wav_path)

    finally:

        # Remove temporary AIFF file
        if aiff_path.exists():
            try:
                aiff_path.unlink()
            except OSError:
                pass


# ============================================================
# PUBLIC TTS FUNCTION
# ============================================================

def generate_speech(
    text: str,
    voice: str = "Kore",
) -> str:
    """
    Generate speech for the given text.

    Primary:
        Gemini TTS

    Fallback:
        macOS local `say`

    The function always returns a WAV path when successful.
    """

    if not text or not text.strip():
        raise ValueError(
            "Text cannot be empty for TTS."
        )

    # --------------------------------------------------------
    # Try Gemini first
    # --------------------------------------------------------

    try:

        print(
            "[TTS] Trying Gemini TTS..."
        )

        output_path = _generate_gemini_speech(
            text=text,
            voice=voice,
        )

        print(
            f"[TTS] Gemini TTS successful: {output_path}"
        )

        return output_path

    except Exception as gemini_error:

        error_text = str(gemini_error)

        print(
            "[TTS] Gemini TTS failed."
        )

        print(
            f"[TTS] Gemini error: {error_text}"
        )

        # ----------------------------------------------------
        # Fallback to local macOS TTS
        # ----------------------------------------------------

        print(
            "[TTS] Falling back to macOS local TTS..."
        )

        try:

            output_path = _generate_macos_speech(
                text=text,
            )

            print(
                f"[TTS] Local TTS successful: {output_path}"
            )

            return output_path

        except Exception as local_error:

            raise RuntimeError(
                "Both Gemini TTS and local macOS TTS failed. "
                f"Gemini error: {gemini_error}. "
                f"Local TTS error: {local_error}"
            ) from local_error