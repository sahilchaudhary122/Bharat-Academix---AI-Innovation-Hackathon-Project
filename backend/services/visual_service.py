import os
import base64
import uuid
from pathlib import Path
from xml.sax.saxutils import escape

from dotenv import load_dotenv
from google import genai

# CONFIGURATION

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY is not configured.")

client = genai.Client(api_key=api_key)


# Generated media directory
MEDIA_DIR = (
    Path(__file__).resolve().parent.parent
    / "media"
    / "generated"
)

MEDIA_DIR.mkdir(parents=True, exist_ok=True)



# SVG FALLBACK GENERATOR


def _create_svg_fallback(
    subject: str,
    topic: str,
    grade: str,
    concept: str,
    style: str,
) -> str:
    """
    Create a topic-aware educational SVG.

    This is used when Gemini image generation is unavailable
    or the Gemini image-generation quota has been exceeded.
    """

    subject_lower = str(subject).lower().strip()
    topic_lower = str(topic).lower().strip()

    
    # Subject colors / headings
    

    if "physics" in subject_lower:
        subject_color = "#2563eb"
        visual_type = "PHYSICS CONCEPT"

    elif "math" in subject_lower:
        subject_color = "#7c3aed"
        visual_type = "MATHEMATICS CONCEPT"

    elif "biology" in subject_lower:
        subject_color = "#059669"
        visual_type = "BIOLOGY CONCEPT"

    elif "chemistry" in subject_lower:
        subject_color = "#dc2626"
        visual_type = "CHEMISTRY CONCEPT"

    elif "computer" in subject_lower:
        subject_color = "#0891b2"
        visual_type = "COMPUTER SCIENCE CONCEPT"

    else:
        subject_color = "#4f46e5"
        visual_type = "EDUCATIONAL CONCEPT"


    
    # Escape text for SVG
    

    safe_topic = escape(str(topic))
    safe_grade = escape(str(grade))
    safe_concept = escape(str(concept))
    safe_style = escape(str(style))


    
    # PHYSICS
    

    if "physics" in subject_lower:

        
        # HARMONIC MOTION
        

        if (
            "harmonic" in topic_lower
            or "oscillation" in topic_lower
            or "oscillatory" in topic_lower
        ):

            diagram = """
            <!-- Fixed wall -->
            <line
                x1="180"
                y1="280"
                x2="180"
                y2="440"
                stroke="#374151"
                stroke-width="9"
            />

            <!-- Spring -->
            <path
                d="
                    M180 360
                    L220 360
                    L245 315
                    L285 405
                    L325 315
                    L365 405
                    L405 315
                    L445 405
                    L485 360
                "
                fill="none"
                stroke="#7c3aed"
                stroke-width="8"
            />

            <!-- Mass -->
            <rect
                x="485"
                y="300"
                width="150"
                height="120"
                rx="15"
                fill="#ede9fe"
                stroke="#7c3aed"
                stroke-width="6"
            />

            <text
                x="560"
                y="370"
                text-anchor="middle"
                font-size="27"
                font-weight="bold"
                fill="#4c1d95"
            >
                Mass
            </text>

            <!-- Equilibrium line -->
            <line
                x1="560"
                y1="225"
                x2="560"
                y2="500"
                stroke="#9ca3af"
                stroke-width="3"
                stroke-dasharray="12 8"
            />

            <text
                x="560"
                y="205"
                text-anchor="middle"
                font-size="21"
                font-weight="bold"
                fill="#374151"
            >
                Equilibrium Position
            </text>

            <!-- Right motion -->
            <line
                x1="635"
                y1="350"
                x2="830"
                y2="350"
                stroke="#dc2626"
                stroke-width="8"
            />

            <polygon
                points="830,350 800,332 800,368"
                fill="#dc2626"
            />

            <text
                x="735"
                y="320"
                text-anchor="middle"
                font-size="22"
                fill="#991b1b"
            >
                Oscillatory Motion
            </text>

            <!-- Restoring force -->
            <line
                x1="485"
                y1="455"
                x2="300"
                y2="455"
                stroke="#059669"
                stroke-width="8"
            />

            <polygon
                points="300,455 330,437 330,473"
                fill="#059669"
            />

            <text
                x="390"
                y="495"
                text-anchor="middle"
                font-size="22"
                fill="#065f46"
            >
                Restoring Force
            </text>

            <!-- Formula -->
            <text
                x="560"
                y="555"
                text-anchor="middle"
                font-size="32"
                font-weight="bold"
                fill="#111827"
            >
                F = −kx
            </text>
            """


        
        # GRAVITATION
        

        elif (
            "gravitation" in topic_lower
            or "gravity" in topic_lower
            or "gravitational" in topic_lower
        ):

            diagram = """
            <!-- Object -->
            <rect
                x="405"
                y="160"
                width="110"
                height="85"
                rx="12"
                fill="#fee2e2"
                stroke="#dc2626"
                stroke-width="5"
            />

            <text
                x="460"
                y="215"
                text-anchor="middle"
                font-size="23"
                font-weight="bold"
                fill="#991b1b"
            >
                Object
            </text>

            <!-- Gravity arrow -->
            <line
                x1="460"
                y1="250"
                x2="460"
                y2="390"
                stroke="#dc2626"
                stroke-width="8"
            />

            <polygon
                points="460,420 435,380 485,380"
                fill="#dc2626"
            />

            <text
                x="520"
                y="325"
                font-size="24"
                fill="#991b1b"
            >
                Gravity (g)
            </text>

            <!-- Earth -->
            <circle
                cx="460"
                cy="535"
                r="120"
                fill="#dbeafe"
                stroke="#2563eb"
                stroke-width="6"
            />

            <text
                x="460"
                y="545"
                text-anchor="middle"
                font-size="30"
                font-weight="bold"
                fill="#1e3a8a"
            >
                EARTH
            </text>

            <!-- Formula -->
            <text
                x="780"
                y="530"
                text-anchor="middle"
                font-size="28"
                font-weight="bold"
                fill="#111827"
            >
                F = Gm₁m₂ / r²
            </text>
            """


        
        # WAVES
        

        elif "wave" in topic_lower:

            diagram = """
            <!-- Axis -->
            <line
                x1="160"
                y1="360"
                x2="970"
                y2="360"
                stroke="#374151"
                stroke-width="3"
            />

            <!-- Wave -->
            <path
                d="
                    M160 360
                    C210 220 260 220 310 360
                    C360 500 410 500 460 360
                    C510 220 560 220 610 360
                    C660 500 710 500 760 360
                    C810 220 860 220 910 360
                    C935 420 955 420 970 360
                "
                fill="none"
                stroke="#2563eb"
                stroke-width="7"
            />

            <!-- Crest -->
            <text
                x="260"
                y="190"
                text-anchor="middle"
                font-size="24"
                font-weight="bold"
                fill="#1e3a8a"
            >
                Crest
            </text>

            <!-- Trough -->
            <text
                x="410"
                y="545"
                text-anchor="middle"
                font-size="24"
                font-weight="bold"
                fill="#1e3a8a"
            >
                Trough
            </text>

            <!-- Wavelength -->
            <line
                x1="310"
                y1="600"
                x2="610"
                y2="600"
                stroke="#7c3aed"
                stroke-width="5"
            />

            <text
                x="460"
                y="635"
                text-anchor="middle"
                font-size="25"
                fill="#4c1d95"
            >
                Wavelength
            </text>
            """


        
        # WORK / ENERGY
        

        elif (
            "work" in topic_lower
            or "energy" in topic_lower
        ):

            diagram = """
            <!-- Ground -->
            <line
                x1="160"
                y1="470"
                x2="950"
                y2="470"
                stroke="#374151"
                stroke-width="5"
            />

            <!-- Object -->
            <rect
                x="300"
                y="350"
                width="180"
                height="120"
                rx="15"
                fill="#fef3c7"
                stroke="#d97706"
                stroke-width="5"
            />

            <text
                x="390"
                y="420"
                text-anchor="middle"
                font-size="27"
                font-weight="bold"
                fill="#92400e"
            >
                Object
            </text>

            <!-- Force -->
            <line
                x1="480"
                y1="410"
                x2="760"
                y2="410"
                stroke="#dc2626"
                stroke-width="8"
            />

            <polygon
                points="760,410 730,392 730,428"
                fill="#dc2626"
            />

            <text
                x="620"
                y="380"
                text-anchor="middle"
                font-size="23"
                fill="#991b1b"
            >
                Applied Force
            </text>

            <!-- Distance -->
            <line
                x1="300"
                y1="520"
                x2="760"
                y2="520"
                stroke="#2563eb"
                stroke-width="5"
            />

            <text
                x="530"
                y="555"
                text-anchor="middle"
                font-size="25"
                fill="#1e3a8a"
            >
                Distance
            </text>

            <text
                x="530"
                y="620"
                text-anchor="middle"
                font-size="31"
                font-weight="bold"
                fill="#111827"
            >
                W = F × d
            </text>
            """

        # ELECTRICITY / CIRCUIT
  

        elif (
            "electricity" in topic_lower
            or "circuit" in topic_lower
            or "current" in topic_lower
        ):

            diagram = """
            <!-- Circuit -->
            <line
                x1="260"
                y1="280"
                x2="700"
                y2="280"
                stroke="#374151"
                stroke-width="5"
            />

            <line
                x1="260"
                y1="500"
                x2="700"
                y2="500"
                stroke="#374151"
                stroke-width="5"
            />

            <line
                x1="260"
                y1="280"
                x2="260"
                y2="500"
                stroke="#374151"
                stroke-width="5"
            />

            <line
                x1="700"
                y1="280"
                x2="700"
                y2="500"
                stroke="#374151"
                stroke-width="5"
            />

            <!-- Battery -->
            <line
                x1="235"
                y1="360"
                x2="285"
                y2="360"
                stroke="#dc2626"
                stroke-width="8"
            />

            <line
                x1="245"
                y1="400"
                x2="275"
                y2="400"
                stroke="#dc2626"
                stroke-width="5"
            />

            <text
                x="180"
                y="385"
                font-size="21"
                fill="#991b1b"
            >
                Battery
            </text>

            <!-- Bulb -->
            <circle
                cx="700"
                cy="390"
                r="60"
                fill="#fef3c7"
                stroke="#d97706"
                stroke-width="5"
            />

            <text
                x="700"
                y="398"
                text-anchor="middle"
                font-size="22"
                font-weight="bold"
                fill="#92400e"
            >
                Bulb
            </text>

            <!-- Current -->
            <text
                x="480"
                y="245"
                text-anchor="middle"
                font-size="25"
                fill="#2563eb"
            >
                Electric Current
            </text>

            <text
                x="480"
                y="590"
                text-anchor="middle"
                font-size="28"
                font-weight="bold"
                fill="#111827"
            >
                Closed Circuit → Current Flow
            </text>
            """

        # FORCE / NEWTON'S LAWS / MOTION


        elif (
            "force" in topic_lower
            or "newton" in topic_lower
            or topic_lower == "motion"
            or "laws of motion" in topic_lower
        ):

            diagram = """
            <!-- Ground -->
            <line
                x1="160"
                y1="460"
                x2="950"
                y2="460"
                stroke="#374151"
                stroke-width="5"
            />

            <!-- Mass -->
            <rect
                x="400"
                y="320"
                width="170"
                height="140"
                rx="15"
                fill="#dbeafe"
                stroke="#2563eb"
                stroke-width="6"
            />

            <text
                x="485"
                y="400"
                text-anchor="middle"
                font-size="28"
                font-weight="bold"
                fill="#1e3a8a"
            >
                Mass
            </text>

            <!-- Force -->
            <line
                x1="570"
                y1="385"
                x2="810"
                y2="385"
                stroke="#dc2626"
                stroke-width="8"
            />

            <polygon
                points="810,385 780,367 780,403"
                fill="#dc2626"
            />

            <text
                x="690"
                y="350"
                text-anchor="middle"
                font-size="23"
                fill="#991b1b"
            >
                Force
            </text>

            <!-- Acceleration -->
            <line
                x1="400"
                y1="510"
                x2="240"
                y2="510"
                stroke="#059669"
                stroke-width="8"
            />

            <polygon
                points="240,510 270,492 270,528"
                fill="#059669"
            />

            <text
                x="320"
                y="550"
                text-anchor="middle"
                font-size="23"
                fill="#065f46"
            >
                Acceleration
            </text>

            <text
                x="485"
                y="620"
                text-anchor="middle"
                font-size="31"
                font-weight="bold"
                fill="#111827"
            >
                F = m × a
            </text>
            """



        # DEFAULT PHYSICS


        else:

            diagram = """
            <circle
                cx="450"
                cy="350"
                r="100"
                fill="#dbeafe"
                stroke="#2563eb"
                stroke-width="6"
            />

            <text
                x="450"
                y="360"
                text-anchor="middle"
                font-size="28"
                font-weight="bold"
                fill="#1e3a8a"
            >
                PHYSICS
            </text>

            <line
                x1="550"
                y1="350"
                x2="780"
                y2="350"
                stroke="#dc2626"
                stroke-width="8"
            />

            <polygon
                points="780,350 750,332 750,368"
                fill="#dc2626"
            />

            <text
                x="665"
                y="320"
                text-anchor="middle"
                font-size="22"
                fill="#991b1b"
            >
                Force
            </text>

            <text
                x="600"
                y="520"
                text-anchor="middle"
                font-size="30"
                font-weight="bold"
                fill="#111827"
            >
                Understand → Apply → Practice
            </text>
            """


    # MATHEMATICS


    elif "math" in subject_lower:

        diagram = """
        <!-- Axes -->
        <line
            x1="220"
            y1="470"
            x2="900"
            y2="470"
            stroke="#374151"
            stroke-width="4"
        />

        <line
            x1="300"
            y1="520"
            x2="300"
            y2="180"
            stroke="#374151"
            stroke-width="4"
        />

        <!-- Graph -->
        <path
            d="M300 430 Q470 300 780 210"
            fill="none"
            stroke="#7c3aed"
            stroke-width="7"
        />

        <circle
            cx="520"
            cy="340"
            r="11"
            fill="#7c3aed"
        />

        <text
            x="560"
            y="315"
            font-size="24"
            fill="#4c1d95"
        >
            Mathematical Relationship
        </text>

        <text
            x="520"
            y="560"
            text-anchor="middle"
            font-size="30"
            font-weight="bold"
            fill="#111827"
        >
            Concept → Formula → Result
        </text>
        """



    # BIOLOGY


    elif "biology" in subject_lower:

        diagram = """
        <!-- Cell -->
        <circle
            cx="450"
            cy="350"
            r="130"
            fill="#d1fae5"
            stroke="#059669"
            stroke-width="6"
        />

        <!-- Nucleus -->
        <circle
            cx="450"
            cy="350"
            r="55"
            fill="#a7f3d0"
            stroke="#047857"
            stroke-width="5"
        />

        <text
            x="450"
            y="360"
            text-anchor="middle"
            font-size="25"
            font-weight="bold"
            fill="#065f46"
        >
            Nucleus
        </text>

        <text
            x="450"
            y="180"
            text-anchor="middle"
            font-size="25"
            font-weight="bold"
            fill="#065f46"
        >
            Cell
        </text>

        <text
            x="450"
            y="550"
            text-anchor="middle"
            font-size="30"
            font-weight="bold"
            fill="#111827"
        >
            Structure → Function
        </text>
        """


    # CHEMISTRY


    elif "chemistry" in subject_lower:

        diagram = """
        <!-- Atom A -->
        <circle
            cx="350"
            cy="350"
            r="70"
            fill="#fee2e2"
            stroke="#dc2626"
            stroke-width="6"
        />

        <!-- Atom B -->
        <circle
            cx="600"
            cy="350"
            r="70"
            fill="#fecaca"
            stroke="#dc2626"
            stroke-width="6"
        />

        <!-- Bond -->
        <line
            x1="420"
            y1="350"
            x2="530"
            y2="350"
            stroke="#991b1b"
            stroke-width="8"
        />

        <text
            x="350"
            y="360"
            text-anchor="middle"
            font-size="27"
            font-weight="bold"
            fill="#991b1b"
        >
            A
        </text>

        <text
            x="600"
            y="360"
            text-anchor="middle"
            font-size="27"
            font-weight="bold"
            fill="#991b1b"
        >
            B
        </text>

        <text
            x="475"
            y="550"
            text-anchor="middle"
            font-size="30"
            font-weight="bold"
            fill="#111827"
        >
            Atoms → Bonds → Molecule
        </text>
        """


   
    # COMPUTER SCIENCE
   

    elif "computer" in subject_lower:

        diagram = """
        <!-- Input -->
        <rect
            x="150"
            y="300"
            width="220"
            height="110"
            rx="15"
            fill="#cffafe"
            stroke="#0891b2"
            stroke-width="5"
        />

        <text
            x="260"
            y="365"
            text-anchor="middle"
            font-size="28"
            font-weight="bold"
            fill="#155e75"
        >
            INPUT
        </text>

        <!-- Arrow -->
        <line
            x1="370"
            y1="355"
            x2="470"
            y2="355"
            stroke="#0891b2"
            stroke-width="7"
        />

        <polygon
            points="470,355 445,340 445,370"
            fill="#0891b2"
        />

        <!-- Process -->
        <rect
            x="470"
            y="300"
            width="220"
            height="110"
            rx="15"
            fill="#e0f2fe"
            stroke="#0891b2"
            stroke-width="5"
        />

        <text
            x="580"
            y="365"
            text-anchor="middle"
            font-size="28"
            font-weight="bold"
            fill="#155e75"
        >
            PROCESS
        </text>

        <!-- Arrow -->
        <line
            x1="690"
            y1="355"
            x2="790"
            y2="355"
            stroke="#0891b2"
            stroke-width="7"
        />

        <polygon
            points="790,355 765,340 765,370"
            fill="#0891b2"
        />

        <!-- Output -->
        <rect
            x="790"
            y="300"
            width="220"
            height="110"
            rx="15"
            fill="#cffafe"
            stroke="#0891b2"
            stroke-width="5"
        />

        <text
            x="900"
            y="365"
            text-anchor="middle"
            font-size="28"
            font-weight="bold"
            fill="#155e75"
        >
            OUTPUT
        </text>
        """


    # GENERIC SUBJECT
  

    else:

        diagram = """
        <rect
            x="350"
            y="270"
            width="300"
            height="160"
            rx="20"
            fill="#eef2ff"
            stroke="#4f46e5"
            stroke-width="5"
        />

        <text
            x="500"
            y="360"
            text-anchor="middle"
            font-size="28"
            font-weight="bold"
            fill="#3730a3"
        >
            KEY CONCEPT
        </text>

        <line
            x1="500"
            y1="430"
            x2="500"
            y2="490"
            stroke="#4f46e5"
            stroke-width="5"
        />

        <text
            x="500"
            y="540"
            text-anchor="middle"
            font-size="25"
            fill="#111827"
        >
            Understand → Apply → Practice
        </text>
        """


    # COMPLETE SVG


    filename = f"visual_{uuid.uuid4()}.svg"

    output_path = MEDIA_DIR / filename

    svg = f"""<?xml version="1.0" encoding="UTF-8"?>

<svg
    xmlns="http://www.w3.org/2000/svg"
    width="1280"
    height="720"
    viewBox="0 0 1280 720"
>

    <!-- Background -->
    <rect
        width="1280"
        height="720"
        fill="white"
    />

    <!-- Main card -->
    <rect
        x="40"
        y="35"
        width="1200"
        height="650"
        rx="25"
        fill="#f9fafb"
        stroke="{subject_color}"
        stroke-width="5"
    />

    <!-- Subject -->
    <text
        x="640"
        y="100"
        text-anchor="middle"
        font-family="Arial, sans-serif"
        font-size="34"
        font-weight="bold"
        fill="{subject_color}"
    >
        {visual_type}
    </text>

    <!-- Topic -->
    <text
        x="640"
        y="150"
        text-anchor="middle"
        font-family="Arial, sans-serif"
        font-size="30"
        font-weight="bold"
        fill="#111827"
    >
        {safe_topic}
    </text>

    <!-- Grade and style -->
    <text
        x="640"
        y="190"
        text-anchor="middle"
        font-family="Arial, sans-serif"
        font-size="20"
        fill="#4b5563"
    >
        Grade {safe_grade} • {safe_style}
    </text>

    <!-- Topic-specific diagram -->
    {diagram}

    <!-- Concept box -->
    <rect
        x="100"
        y="570"
        width="1080"
        height="75"
        rx="15"
        fill="#f3f4f6"
    />

    <text
        x="640"
        y="600"
        text-anchor="middle"
        font-family="Arial, sans-serif"
        font-size="19"
        font-weight="bold"
        fill="#374151"
    >
        Concept
    </text>

    <text
        x="640"
        y="628"
        text-anchor="middle"
        font-family="Arial, sans-serif"
        font-size="17"
        fill="#4b5563"
    >
        {safe_concept}
    </text>

</svg>
"""

    with open(
        output_path,
        "w",
        encoding="utf-8"
    ) as svg_file:

        svg_file.write(svg)

    print(
        f"Fallback visual created: {output_path}"
    )

    return str(output_path)


# MAIN VISUAL GENERATOR

def generate_visual(
    subject: str,
    topic: str,
    grade: str,
    concept: str,
    style: str = "educational diagram",
) -> str:
    """
    Generate an educational visual.

    1. Try Gemini image generation.
    2. If Gemini fails or quota is exceeded,
       create a topic-aware SVG fallback.
    """

    # Gemini prompt 

    prompt = f"""
Create a unique educational visual for a personalized AI teacher.

SUBJECT:
{subject}

TOPIC:
{topic}

GRADE:
{grade}

CONCEPT:
{concept}

VISUAL STYLE:
{style}

IMPORTANT REQUIREMENTS:

1. The visual MUST specifically represent the exact topic:
   {topic}

2. Do NOT use a generic visual for the subject.

3. The visual must be different when the topic changes.

4. Clearly represent the supplied concept:
   {concept}

5. Make it appropriate for Grade {grade}.

6. Use an educational diagram, scientific illustration,
   labelled diagram, concept map, chart, or process diagram.

7. Avoid unrelated objects.

8. Make the visual useful for teaching the exact topic.

9. If the topic is Harmonic Motion, show concepts such as:
   - oscillation
   - equilibrium position
   - restoring force
   - spring and mass
   - periodic motion

10. If the topic is Gravitation, show:
    - Earth
    - gravitational attraction
    - falling object

11. If the topic is Waves, show:
    - crest
    - trough
    - wavelength
    - amplitude

12. If the topic is Electricity or Circuits, show:
    - battery
    - wires
    - current
    - load/bulb
    - closed circuit

13. Keep the visual clear and suitable for a classroom.
"""

    # TRY GEMINI

    try:

        interaction = client.interactions.create(
            model="gemini-3.1-flash-image",
            input=prompt,
            response_format={
                "type": "image",
                "mime_type": "image/jpeg",
                "aspect_ratio": "16:9",
                "image_size": "1K",
            },
        )

        if interaction.output_image:

            image_data = base64.b64decode(
                interaction.output_image.data
            )

            filename = f"visual_{uuid.uuid4()}.jpg"

            output_path = MEDIA_DIR / filename

            with open(
                output_path,
                "wb"
            ) as image_file:

                image_file.write(image_data)

            print(
                f"Gemini visual created: {output_path}"
            )

            return str(output_path)


    except Exception as e:

        print(
            f"Gemini visual generation unavailable: {e}"
        )

    # FALLBACK
  
    return _create_svg_fallback(
        subject=subject,
        topic=topic,
        grade=grade,
        concept=concept,
        style=style,
    )