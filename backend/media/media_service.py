import subprocess
from pathlib import Path
import uuid

# Base directory for generated media
MEDIA_DIR = Path(__file__).resolve().parent / "generated"
MEDIA_DIR.mkdir(parents=True, exist_ok=True)


def convert_audio_to_mp3(input_file: str) -> str:
    """
    Convert an audio file to MP3 using FFmpeg.
    """

    input_path = Path(input_file)

    if not input_path.exists():
        raise FileNotFoundError(
            f"Input audio file not found: {input_file}"
        )

    output_name = f"{uuid.uuid4()}.mp3"
    output_path = MEDIA_DIR / output_name

    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_path),
        "-vn",
        "-codec:a",
        "libmp3lame",
        "-q:a",
        "2",
        str(output_path),
    ]

    subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True
    )

    return str(output_path)


def extract_audio_from_video(input_file: str) -> str:
    """
    Extract the audio track from a video and save it as MP3.
    """

    input_path = Path(input_file)

    if not input_path.exists():
        raise FileNotFoundError(
            f"Input video file not found: {input_file}"
        )

    output_name = f"{uuid.uuid4()}.mp3"
    output_path = MEDIA_DIR / output_name

    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_path),
        "-vn",
        "-codec:a",
        "libmp3lame",
        "-q:a",
        "2",
        str(output_path),
    ]

    subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True
    )

    return str(output_path)


def merge_audio_with_video(
    video_file: str,
    audio_file: str
) -> str:
    """
    Replace/add the audio track of a video using FFmpeg.
    """

    video_path = Path(video_file)
    audio_path = Path(audio_file)

    if not video_path.exists():
        raise FileNotFoundError(
            f"Video file not found: {video_file}"
        )

    if not audio_path.exists():
        raise FileNotFoundError(
            f"Audio file not found: {audio_file}"
        )

    output_name = f"{uuid.uuid4()}.mp4"
    output_path = MEDIA_DIR / output_name

    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(video_path),
        "-i",
        str(audio_path),
        "-map",
        "0:v:0",
        "-map",
        "1:a:0",
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-shortest",
        str(output_path),
    ]

    subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True
    )

    return str(output_path)