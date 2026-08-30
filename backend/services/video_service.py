import subprocess
import uuid
from pathlib import Path


MEDIA_DIR = (
    Path(__file__).resolve().parent.parent
    / "media"
    / "generated"
)

MEDIA_DIR.mkdir(parents=True, exist_ok=True)


def convert_svg_to_png(svg_path: Path) -> Path:
    """
    Convert an SVG educational visual into PNG.
    """

    png_path = MEDIA_DIR / f"visual_{uuid.uuid4()}.png"

    command = [
        "rsvg-convert",
        "-w",
        "1280",
        "-h",
        "720",
        "-o",
        str(png_path),
        str(svg_path),
    ]

    print("Converting SVG to PNG...")
    print("SVG:", svg_path)
    print("PNG:", png_path)

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(
            "rsvg-convert failed:\n"
            + result.stderr
        )

    if not png_path.exists():
        raise RuntimeError(
            "PNG file was not created."
        )

    print("SVG successfully converted to PNG.")

    return png_path


def generate_video(
    visual_file: str,
    audio_file: str | None = None,
    duration_seconds: int = 300,
) -> str:

    print("\n========== VIDEO GENERATION ==========")
    print("Visual:", visual_file)
    print("Audio:", audio_file)
    print("Duration:", duration_seconds)

    
    # Check visual
    

    visual_path = Path(visual_file)

    if not visual_path.exists():
        raise FileNotFoundError(
            f"Visual file not found: {visual_path}"
        )

    
    # Check audio
    

    audio_path = None

    if audio_file:

        audio_path = Path(audio_file)

        if not audio_path.exists():
            raise FileNotFoundError(
                f"Audio file not found: {audio_path}"
            )

    
    # Convert SVG → PNG
    

    if visual_path.suffix.lower() == ".svg":

        visual_path = convert_svg_to_png(
            visual_path
        )

    
    # Output video
    

    output_path = (
        MEDIA_DIR
        / f"video_{uuid.uuid4()}.mp4"
    )

    
    # With audio
    

    if audio_path:

        command = [
            "ffmpeg",
            "-y",

            # Loop image
            "-loop",
            "1",

            # Image
            "-i",
            str(visual_path),

            # Audio
            "-i",
            str(audio_path),

            # Video duration
            "-t",
            str(duration_seconds),

            # Video
            "-r",
            "30",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-pix_fmt",
            "yuv420p",

            # Audio
            "-c:a",
            "aac",
            "-b:a",
            "128k",

            # End when audio ends
            "-shortest",

            # Web playback
            "-movflags",
            "+faststart",

            str(output_path),
        ]

    
    # Without audio
    

    else:

        command = [
            "ffmpeg",
            "-y",

            "-loop",
            "1",

            "-i",
            str(visual_path),

            "-t",
            str(duration_seconds),

            "-r",
            "30",

            "-c:v",
            "libx264",

            "-preset",
            "veryfast",

            "-pix_fmt",
            "yuv420p",

            "-movflags",
            "+faststart",

            str(output_path),
        ]

    print("\nRunning FFmpeg...")
    print(" ".join(command))

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )

    
    # FFmpeg error
    

    if result.returncode != 0:

        print("\n========== FFMPEG ERROR ==========")
        print(result.stderr)

        raise RuntimeError(
            "FFmpeg failed:\n"
            + result.stderr
        )

    
    # Verify MP4
    

    if not output_path.exists():

        raise RuntimeError(
            "FFmpeg completed but MP4 was not created."
        )

    file_size = output_path.stat().st_size

    if file_size == 0:

        raise RuntimeError(
            "MP4 was created but is empty."
        )

    print("\n========== VIDEO SUCCESS ==========")
    print("Video:", output_path)
    print("Size:", file_size, "bytes")

    return str(output_path)