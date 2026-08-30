import os
import base64
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


def generate_avatar(
    name: str = "AI Teacher",
    subject: str = "General Education",
    style: str = "friendly professional"
) -> str:
    """
    Generate a virtual teacher avatar image using Gemini.
    """

    prompt = f"""
Create a high-quality virtual AI teacher avatar for an educational
learning platform.

Teacher name: {name}
Teaching subject: {subject}
Visual style: {style}

Requirements:
- Friendly and approachable teacher
- Professional educational appearance
- Head and shoulders portrait
- Looking directly at the camera
- Natural facial expression
- Clean modern classroom background
- Suitable for children and students
- No text, logos, watermarks, or labels
- Consistent character appearance
- Realistic but welcoming digital educator
"""

    interaction = client.interactions.create(
        model="gemini-3.1-flash-image",
        input=prompt,
        response_format={
            "type": "image",
            "mime_type": "image/jpeg",
            "aspect_ratio": "1:1",
            "image_size": "1K",
        },
    )

    if not interaction.output_image:
        raise RuntimeError(
            "Gemini did not return an avatar image."
        )

    image_data = base64.b64decode(
        interaction.output_image.data
    )

    filename = f"avatar_{uuid.uuid4()}.jpg"
    output_path = MEDIA_DIR / filename

    with open(output_path, "wb") as image_file:
        image_file.write(image_data)

    return str(output_path)