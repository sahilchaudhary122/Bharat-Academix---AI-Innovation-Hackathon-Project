import os
import subprocess
import uuid
from pathlib import Path


# Project paths
BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent

SADTALKER_DIR = PROJECT_ROOT / "SadTalker"
SADTALKER_PYTHON = os.getenv("SADTALKER_PYTHON_PATH", "/opt/anaconda3/envs/sadtalker/bin/python")

CHECKPOINT_DIR = SADTALKER_DIR / "checkpoints"
RESULT_DIR = BACKEND_DIR / "media" / "generated"

DEFAULT_AVATAR = SADTALKER_DIR / "inputs" / "ai_teacher.png"


def generate_talking_avatar(
    audio_file: str,
    avatar_image: str | None = None,
    size: int = 256,
) -> str:

    audio_path = Path(audio_file)

    if not audio_path.exists():
        raise FileNotFoundError(
            f"Audio file not found: {audio_path}"
        )

    if avatar_image:
        avatar_path = Path(avatar_image)
    else:
        avatar_path = DEFAULT_AVATAR

    if not avatar_path.exists():
        raise FileNotFoundError(
            f"Avatar image not found: {avatar_path}"
        )

    if not SADTALKER_DIR.exists():
        raise FileNotFoundError(
            f"SadTalker directory not found: {SADTALKER_DIR}"
        )

    if not CHECKPOINT_DIR.exists():
        raise FileNotFoundError(
            f"SadTalker checkpoints not found: {CHECKPOINT_DIR}"
        )

    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    job_id = str(uuid.uuid4())

    job_result_dir = RESULT_DIR / f"sadtalker_{job_id}"
    job_result_dir.mkdir(parents=True, exist_ok=True)

    command = [
        SADTALKER_PYTHON,
        str(SADTALKER_DIR / "inference.py"),

        "--driven_audio",
        str(audio_path),

        "--source_image",
        str(avatar_path),

        "--checkpoint_dir",
        str(CHECKPOINT_DIR),

        "--result_dir",
        str(job_result_dir),

        "--preprocess",
        "full",

        "--size",
        str(size),

        "--still",
    ]

    print("Running SadTalker...")
    print(" ".join(command))

    try:
        result = subprocess.run(
            command,
            cwd=str(SADTALKER_DIR),
            capture_output=True,
            text=True,
            check=False,
        )

        print(result.stdout)

        if result.returncode != 0:
            print(result.stderr)

            raise RuntimeError(
                "SadTalker failed.\n"
                f"STDOUT:\n{result.stdout}\n"
                f"STDERR:\n{result.stderr}"
            )

    except Exception as e:
        raise RuntimeError(
            f"SadTalker execution failed: {str(e)}"
        ) from e

    videos = list(job_result_dir.glob("*.mp4"))

    if not videos:
        raise RuntimeError(
            "SadTalker completed but no MP4 video was generated."
        )

    generated_video = videos[0]

    # Copy final video to the normal generated-media directory
    final_filename = f"avatar_video_{job_id}.mp4"
    final_path = RESULT_DIR / final_filename

    generated_video.replace(final_path)

    return str(final_path)