import os
import base64
import uuid
from pathlib import Path
from xml.sax.saxutils import escape

from dotenv import load_dotenv
from google import genai


# ============================================================
# CONFIGURATION
# ============================================================

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY is not configured.")

client = genai.Client(api_key=api_key)


# ============================================================
# GENERATED MEDIA DIRECTORY
# ============================================================

MEDIA_DIR = (
    Path(__file__).resolve().parent.parent
    / "media"
    / "generated"
)

MEDIA_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# SVG FALLBACK GENERATOR
# ============================================================

def _create_svg_fallback(
    subject: str,
    topic: str,
    grade: str,
    concept: str,
    style: str,
) -> str:
    """
    Create a topic-aware educational SVG.

    Used when Gemini image generation is unavailable,
    fails, or its image-generation quota is exceeded.
    """

    subject_lower = str(subject).lower().strip()
    topic_lower = str(topic).lower().strip()

    # --------------------------------------------------------
    # Subject colors / headings
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Escape text for SVG
    # --------------------------------------------------------

    safe_topic = escape(str(topic))
    safe_grade = escape(str(grade))
    safe_concept = escape(str(concept))
    safe_style = escape(str(style))

    # --------------------------------------------------------
    # Default diagram
    # --------------------------------------------------------

    diagram = """
        <rect
            x="350"
            y="270"
            width="580"
            height="170"
            rx="20"
            fill="#eef2ff"
            stroke="#4f46e5"
            stroke-width="5"
        />

        <text
            x="640"
            y="350"
            text-anchor="middle"
            font-size="30"
            font-weight="bold"
            fill="#3730a3"
        >
            KEY CONCEPT
        </text>

        <text
            x="640"
            y="395"
            text-anchor="middle"
            font-size="23"
            fill="#374151"
        >
            Understand → Apply → Practice
        </text>
    """

    # ========================================================
    # PHYSICS
    # ========================================================

    if "physics" in subject_lower:

        # ----------------------------------------------------
        # NEWTON'S THIRD LAW
        # ----------------------------------------------------

                # ----------------------------------------------------
        # NEWTON'S THIRD LAW
        # ----------------------------------------------------

        if (
            "newton" in topic_lower
            and (
                "third" in topic_lower
                or "3rd" in topic_lower
                or "action" in topic_lower
                or "reaction" in topic_lower
            )
        ):

            diagram = """
                <!-- =================================================
                     NEWTON'S THIRD LAW
                     Person pushes wall
                     ================================================= -->

                <!-- Ground -->
                <line
                    x1="120"
                    y1="535"
                    x2="1000"
                    y2="535"
                    stroke="#374151"
                    stroke-width="6"
                />

                <!-- ================= PERSON ================= -->

                <!-- Head -->
                <circle
                    cx="300"
                    cy="285"
                    r="42"
                    fill="#dbeafe"
                    stroke="#2563eb"
                    stroke-width="6"
                />

                <!-- Body -->
                <line
                    x1="300"
                    y1="327"
                    x2="300"
                    y2="410"
                    stroke="#2563eb"
                    stroke-width="10"
                />

                <!-- Left leg -->
                <line
                    x1="300"
                    y1="410"
                    x2="250"
                    y2="535"
                    stroke="#2563eb"
                    stroke-width="10"
                />

                <!-- Right leg -->
                <line
                    x1="300"
                    y1="410"
                    x2="350"
                    y2="535"
                    stroke="#2563eb"
                    stroke-width="10"
                />

                <!-- Arm pushing wall -->
                <line
                    x1="300"
                    y1="345"
                    x2="420"
                    y2="375"
                    stroke="#2563eb"
                    stroke-width="10"
                />

                <line
                    x1="420"
                    y1="375"
                    x2="475"
                    y2="375"
                    stroke="#2563eb"
                    stroke-width="10"
                />

                <!-- Person label -->
                <text
                    x="300"
                    y="570"
                    text-anchor="middle"
                    font-size="24"
                    font-weight="bold"
                    fill="#1e3a8a"
                >
                    PERSON
                </text>

                <!-- ================= WALL ================= -->

                <rect
                    x="475"
                    y="225"
                    width="55"
                    height="310"
                    rx="5"
                    fill="#d1d5db"
                    stroke="#374151"
                    stroke-width="6"
                />

                <!-- Wall texture -->
                <line
                    x1="485"
                    y1="255"
                    x2="520"
                    y2="290"
                    stroke="#9ca3af"
                    stroke-width="4"
                />

                <line
                    x1="485"
                    y1="315"
                    x2="520"
                    y2="350"
                    stroke="#9ca3af"
                    stroke-width="4"
                />

                <line
                    x1="485"
                    y1="375"
                    x2="520"
                    y2="410"
                    stroke="#9ca3af"
                    stroke-width="4"
                />

                <line
                    x1="485"
                    y1="435"
                    x2="520"
                    y2="470"
                    stroke="#9ca3af"
                    stroke-width="4"
                />

                <line
                    x1="485"
                    y1="495"
                    x2="520"
                    y2="525"
                    stroke="#9ca3af"
                    stroke-width="4"
                />

                <!-- Wall label -->
                <text
                    x="502"
                    y="205"
                    text-anchor="middle"
                    font-size="24"
                    font-weight="bold"
                    fill="#374151"
                >
                    WALL
                </text>

                <!-- ================= ACTION FORCE ================= -->

                <line
                    x1="405"
                    y1="315"
                    x2="730"
                    y2="315"
                    stroke="#dc2626"
                    stroke-width="8"
                />

                <polygon
                    points="730,315 695,293 695,337"
                    fill="#dc2626"
                />

                <text
                    x="570"
                    y="285"
                    text-anchor="middle"
                    font-size="21"
                    font-weight="bold"
                    fill="#991b1b"
                >
                    Action: Person → Wall
                </text>

                <!-- ================= REACTION FORCE ================= -->

                <line
                    x1="405"
                    y1="445"
                    x2="80"
                    y2="445"
                    stroke="#059669"
                    stroke-width="8"
                />

                <polygon
                    points="80,445 115,423 115,467"
                    fill="#059669"
                />

                <text
                    x="245"
                    y="415"
                    text-anchor="middle"
                    font-size="21"
                    font-weight="bold"
                    fill="#065f46"
                >
                    Reaction: Wall → Person
                </text>

                <!-- ================= EXPLANATION BOX ================= -->

                <rect
                    x="680"
                    y="350"
                    width="310"
                    height="145"
                    rx="18"
                    fill="#eff6ff"
                    stroke="#2563eb"
                    stroke-width="4"
                />

                <text
                    x="835"
                    y="385"
                    text-anchor="middle"
                    font-size="21"
                    font-weight="bold"
                    fill="#1e3a8a"
                >
                    Equal magnitude
                </text>

                <text
                    x="835"
                    y="420"
                    text-anchor="middle"
                    font-size="21"
                    font-weight="bold"
                    fill="#1e3a8a"
                >
                    Opposite direction
                </text>

                <text
                    x="835"
                    y="460"
                    text-anchor="middle"
                    font-size="24"
                    font-weight="bold"
                    fill="#111827"
                >
                    F₁ = −F₂
                </text>
            """

        # ----------------------------------------------------
        # HARMONIC MOTION
        # ----------------------------------------------------

        elif (
            "harmonic" in topic_lower
            or "oscillation" in topic_lower
            or "oscillatory" in topic_lower
        ):

            diagram = """
                <!-- Fixed wall -->
                <line
                    x1="180"
                    y1="220"
                    x2="180"
                    y2="430"
                    stroke="#374151"
                    stroke-width="8"
                />

                <!-- Spring -->
                <path
                    d="
                        M180 325
                        L220 325
                        L245 280
                        L285 370
                        L325 280
                        L365 370
                        L405 280
                        L445 370
                        L485 325
                    "
                    fill="none"
                    stroke="#7c3aed"
                    stroke-width="8"
                />

                <!-- Mass -->
                <rect
                    x="485"
                    y="265"
                    width="150"
                    height="120"
                    rx="15"
                    fill="#ede9fe"
                    stroke="#7c3aed"
                    stroke-width="6"
                />

                <text
                    x="560"
                    y="338"
                    text-anchor="middle"
                    font-size="27"
                    font-weight="bold"
                    fill="#4c1d95"
                >
                    MASS
                </text>

                <!-- Equilibrium -->
                <line
                    x1="560"
                    y1="200"
                    x2="560"
                    y2="450"
                    stroke="#9ca3af"
                    stroke-width="3"
                    stroke-dasharray="12 8"
                />

                <text
                    x="560"
                    y="180"
                    text-anchor="middle"
                    font-size="20"
                    font-weight="bold"
                    fill="#374151"
                >
                    Equilibrium
                </text>

                <!-- Motion arrow -->
                <line
                    x1="650"
                    y1="325"
                    x2="850"
                    y2="325"
                    stroke="#dc2626"
                    stroke-width="8"
                />

                <polygon
                    points="850,325 815,303 815,347"
                    fill="#dc2626"
                />

                <text
                    x="750"
                    y="290"
                    text-anchor="middle"
                    font-size="21"
                    fill="#991b1b"
                >
                    Oscillatory Motion
                </text>

                <!-- Restoring force -->
                <line
                    x1="485"
                    y1="430"
                    x2="300"
                    y2="430"
                    stroke="#059669"
                    stroke-width="8"
                />

                <polygon
                    points="300,430 335,408 335,452"
                    fill="#059669"
                />

                <text
                    x="395"
                    y="470"
                    text-anchor="middle"
                    font-size="20"
                    fill="#065f46"
                >
                    Restoring Force
                </text>

                <!-- Formula -->
                <text
                    x="560"
                    y="545"
                    text-anchor="middle"
                    font-size="31"
                    font-weight="bold"
                    fill="#111827"
                >
                    F = −kx
                </text>
            """

        # ----------------------------------------------------
        # GRAVITATION
        # ----------------------------------------------------

        elif (
            "gravitation" in topic_lower
            or "gravity" in topic_lower
            or "gravitational" in topic_lower
        ):

            diagram = """
                <!-- Object -->
                <rect
                    x="400"
                    y="205"
                    width="120"
                    height="85"
                    rx="12"
                    fill="#fee2e2"
                    stroke="#dc2626"
                    stroke-width="5"
                />

                <text
                    x="460"
                    y="258"
                    text-anchor="middle"
                    font-size="23"
                    font-weight="bold"
                    fill="#991b1b"
                >
                    OBJECT
                </text>

                <!-- Gravity arrow -->
                <line
                    x1="460"
                    y1="295"
                    x2="460"
                    y2="370"
                    stroke="#dc2626"
                    stroke-width="8"
                />

                <polygon
                    points="460,405 435,365 485,365"
                    fill="#dc2626"
                />

                <text
                    x="535"
                    y="345"
                    font-size="23"
                    fill="#991b1b"
                >
                    Gravity
                </text>

                <!-- Earth -->
                <circle
                    cx="460"
                    cy="505"
                    r="95"
                    fill="#dbeafe"
                    stroke="#2563eb"
                    stroke-width="6"
                />

                <text
                    x="460"
                    y="515"
                    text-anchor="middle"
                    font-size="29"
                    font-weight="bold"
                    fill="#1e3a8a"
                >
                    EARTH
                </text>

                <!-- Formula -->
                <text
                    x="820"
                    y="500"
                    text-anchor="middle"
                    font-size="27"
                    font-weight="bold"
                    fill="#111827"
                >
                    F = Gm₁m₂ / r²
                </text>
            """

        # ----------------------------------------------------
        # WAVES
        # ----------------------------------------------------

        elif "wave" in topic_lower:

            diagram = """
                <!-- Axis -->
                <line
                    x1="150"
                    y1="330"
                    x2="990"
                    y2="330"
                    stroke="#374151"
                    stroke-width="3"
                />

                <!-- Wave -->
                <path
                    d="
                        M150 330
                        C200 200 250 200 300 330
                        C350 460 400 460 450 330
                        C500 200 550 200 600 330
                        C650 460 700 460 750 330
                        C800 200 850 200 900 330
                        C940 430 970 430 990 330
                    "
                    fill="none"
                    stroke="#2563eb"
                    stroke-width="7"
                />

                <!-- Crest -->
                <text
                    x="225"
                    y="175"
                    text-anchor="middle"
                    font-size="23"
                    font-weight="bold"
                    fill="#1e3a8a"
                >
                    CREST
                </text>

                <!-- Trough -->
                <text
                    x="375"
                    y="500"
                    text-anchor="middle"
                    font-size="23"
                    font-weight="bold"
                    fill="#1e3a8a"
                >
                    TROUGH
                </text>

                <!-- Wavelength -->
                <line
                    x1="300"
                    y1="555"
                    x2="600"
                    y2="555"
                    stroke="#7c3aed"
                    stroke-width="5"
                />

                <text
                    x="450"
                    y="595"
                    text-anchor="middle"
                    font-size="24"
                    fill="#4c1d95"
                >
                    Wavelength
                </text>

                <!-- Amplitude -->
                <line
                    x1="225"
                    y1="330"
                    x2="225"
                    y2="205"
                    stroke="#059669"
                    stroke-width="5"
                />

                <text
                    x="275"
                    y="270"
                    font-size="22"
                    fill="#065f46"
                >
                    Amplitude
                </text>
            """

        # ----------------------------------------------------
        # WORK / ENERGY
        # ----------------------------------------------------

        elif (
            "work" in topic_lower
            or "energy" in topic_lower
        ):

            diagram = """
                <!-- Ground -->
                <line
                    x1="150"
                    y1="450"
                    x2="990"
                    y2="450"
                    stroke="#374151"
                    stroke-width="5"
                />

                <!-- Object -->
                <rect
                    x="280"
                    y="330"
                    width="170"
                    height="120"
                    rx="15"
                    fill="#fef3c7"
                    stroke="#d97706"
                    stroke-width="5"
                />

                <text
                    x="365"
                    y="402"
                    text-anchor="middle"
                    font-size="27"
                    font-weight="bold"
                    fill="#92400e"
                >
                    OBJECT
                </text>

                <!-- Force -->
                <line
                    x1="450"
                    y1="390"
                    x2="750"
                    y2="390"
                    stroke="#dc2626"
                    stroke-width="8"
                />

                <polygon
                    points="750,390 715,368 715,412"
                    fill="#dc2626"
                />

                <text
                    x="600"
                    y="355"
                    text-anchor="middle"
                    font-size="22"
                    fill="#991b1b"
                >
                    Applied Force
                </text>

                <!-- Distance -->
                <line
                    x1="280"
                    y1="500"
                    x2="750"
                    y2="500"
                    stroke="#2563eb"
                    stroke-width="5"
                />

                <text
                    x="515"
                    y="540"
                    text-anchor="middle"
                    font-size="24"
                    fill="#1e3a8a"
                >
                    Distance
                </text>

                <!-- Formula -->
                <text
                    x="900"
                    y="280"
                    text-anchor="middle"
                    font-size="28"
                    font-weight="bold"
                    fill="#111827"
                >
                    W = F × d
                </text>
            """

        # ----------------------------------------------------
        # ELECTRICITY / CIRCUITS
        # ----------------------------------------------------

        elif (
            "electricity" in topic_lower
            or "circuit" in topic_lower
            or "current" in topic_lower
        ):

            diagram = """
                <!-- Circuit wire -->
                <line
                    x1="250"
                    y1="300"
                    x2="450"
                    y2="300"
                    stroke="#0891b2"
                    stroke-width="7"
                />

                <line
                    x1="550"
                    y1="300"
                    x2="850"
                    y2="300"
                    stroke="#0891b2"
                    stroke-width="7"
                />

                <line
                    x1="850"
                    y1="300"
                    x2="850"
                    y2="470"
                    stroke="#0891b2"
                    stroke-width="7"
                />

                <line
                    x1="850"
                    y1="470"
                    x2="250"
                    y2="470"
                    stroke="#0891b2"
                    stroke-width="7"
                />

                <line
                    x1="250"
                    y1="470"
                    x2="250"
                    y2="300"
                    stroke="#0891b2"
                    stroke-width="7"
                />

                <!-- Battery -->
                <line
                    x1="450"
                    y1="260"
                    x2="450"
                    y2="340"
                    stroke="#111827"
                    stroke-width="8"
                />

                <line
                    x1="500"
                    y1="275"
                    x2="500"
                    y2="325"
                    stroke="#111827"
                    stroke-width="4"
                />

                <text
                    x="475"
                    y="220"
                    text-anchor="middle"
                    font-size="22"
                    font-weight="bold"
                    fill="#111827"
                >
                    BATTERY
                </text>

                <!-- Bulb -->
                <circle
                    cx="850"
                    cy="385"
                    r="42"
                    fill="#fef3c7"
                    stroke="#d97706"
                    stroke-width="6"
                />

                <text
                    x="850"
                    y="393"
                    text-anchor="middle"
                    font-size="20"
                    font-weight="bold"
                    fill="#92400e"
                >
                    BULB
                </text>

                <!-- Current arrow -->
                <polygon
                    points="680,292 650,275 650,309"
                    fill="#dc2626"
                />

                <text
                    x="680"
                    y="255"
                    text-anchor="middle"
                    font-size="22"
                    fill="#991b1b"
                >
                    Current
                </text>

                <!-- Closed circuit -->
                <text
                    x="550"
                    y="550"
                    text-anchor="middle"
                    font-size="27"
                    font-weight="bold"
                    fill="#111827"
                >
                    Closed Circuit → Current Flows
                </text>
            """

    # ========================================================
    # MATHEMATICS
    # ========================================================

    elif "math" in subject_lower:

        diagram = """
            <!-- Axes -->
            <line
                x1="220"
                y1="460"
                x2="950"
                y2="460"
                stroke="#374151"
                stroke-width="4"
            />

            <line
                x1="300"
                y1="530"
                x2="300"
                y2="170"
                stroke="#374151"
                stroke-width="4"
            />

            <!-- Arrow X -->
            <polygon
                points="950,460 925,445 925,475"
                fill="#374151"
            />

            <!-- Arrow Y -->
            <polygon
                points="300,170 285,195 315,195"
                fill="#374151"
            />

            <!-- Graph -->
            <path
                d="M300 430 Q470 320 800 220"
                fill="none"
                stroke="#7c3aed"
                stroke-width="7"
            />

            <circle
                cx="520"
                cy="350"
                r="11"
                fill="#7c3aed"
            />

            <text
                x="620"
                y="285"
                font-size="23"
                fill="#4c1d95"
            >
                Mathematical Relationship
            </text>

            <text
                x="580"
                y="555"
                text-anchor="middle"
                font-size="27"
                font-weight="bold"
                fill="#111827"
            >
                Concept → Formula → Result
            </text>
        """

    # ========================================================
    # BIOLOGY
    # ========================================================

    elif "biology" in subject_lower:

        diagram = """
            <!-- Cell -->
            <circle
                cx="470"
                cy="350"
                r="135"
                fill="#d1fae5"
                stroke="#059669"
                stroke-width="6"
            />

            <!-- Nucleus -->
            <circle
                cx="470"
                cy="350"
                r="55"
                fill="#a7f3d0"
                stroke="#047857"
                stroke-width="5"
            />

            <text
                x="470"
                y="360"
                text-anchor="middle"
                font-size="24"
                font-weight="bold"
                fill="#065f46"
            >
                Nucleus
            </text>

            <text
                x="470"
                y="175"
                text-anchor="middle"
                font-size="25"
                font-weight="bold"
                fill="#065f46"
            >
                Cell
            </text>

            <!-- Label -->
            <line
                x1="570"
                y1="285"
                x2="760"
                y2="220"
                stroke="#059669"
                stroke-width="4"
            />

            <text
                x="780"
                y="220"
                font-size="22"
                fill="#065f46"
            >
                Cell Structure
            </text>

            <text
                x="470"
                y="550"
                text-anchor="middle"
                font-size="29"
                font-weight="bold"
                fill="#111827"
            >
                Structure → Function
            </text>
        """

    # ========================================================
    # CHEMISTRY
    # ========================================================

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
                cx="650"
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
                x2="580"
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
                x="650"
                y="360"
                text-anchor="middle"
                font-size="27"
                font-weight="bold"
                fill="#991b1b"
            >
                B
            </text>

            <text
                x="500"
                y="285"
                text-anchor="middle"
                font-size="22"
                fill="#991b1b"
            >
                Chemical Bond
            </text>

            <text
                x="500"
                y="550"
                text-anchor="middle"
                font-size="29"
                font-weight="bold"
                fill="#111827"
            >
                Atoms → Bonds → Molecule
            </text>
        """

    # ========================================================
    # COMPUTER SCIENCE
    # ========================================================

    elif "computer" in subject_lower:

        diagram = """
            <!-- Input -->
            <rect
                x="120"
                y="300"
                width="220"
                height="110"
                rx="15"
                fill="#cffafe"
                stroke="#0891b2"
                stroke-width="5"
            />

            <text
                x="230"
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
                x1="340"
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
                x2="820"
                y2="355"
                stroke="#0891b2"
                stroke-width="7"
            />

            <polygon
                points="820,355 795,340 795,370"
                fill="#0891b2"
            />

            <!-- Output -->
            <rect
                x="820"
                y="300"
                width="220"
                height="110"
                rx="15"
                fill="#cffafe"
                stroke="#0891b2"
                stroke-width="5"
            />

            <text
                x="930"
                y="365"
                text-anchor="middle"
                font-size="28"
                font-weight="bold"
                fill="#155e75"
            >
                OUTPUT
            </text>
        """

    # ========================================================
    # GENERIC SUBJECT
    # ========================================================

    else:

        diagram = """
            <rect
                x="350"
                y="270"
                width="580"
                height="160"
                rx="20"
                fill="#eef2ff"
                stroke="#4f46e5"
                stroke-width="5"
            />

            <text
                x="640"
                y="345"
                text-anchor="middle"
                font-size="29"
                font-weight="bold"
                fill="#3730a3"
            >
                KEY CONCEPT
            </text>

            <text
                x="640"
                y="395"
                text-anchor="middle"
                font-size="23"
                fill="#374151"
            >
                Understand → Apply → Practice
            </text>
        """

    # ========================================================
    # COMPLETE SVG
    # ========================================================

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
        y="90"
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
        y="135"
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
        y="172"
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
        y="590"
        width="1080"
        height="55"
        rx="15"
        fill="#f3f4f6"
    />

    <text
        x="640"
        y="614"
        text-anchor="middle"
        font-family="Arial, sans-serif"
        font-size="17"
        font-weight="bold"
        fill="#374151"
    >
        Concept
    </text>

    <text
        x="640"
        y="636"
        text-anchor="middle"
        font-family="Arial, sans-serif"
        font-size="16"
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

    print(f"Fallback visual created: {output_path}")

    return str(output_path)


# ============================================================
# MAIN VISUAL GENERATOR
# ============================================================

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

PHYSICS-SPECIFIC REQUIREMENTS:

9. If the topic is Newton's Third Law of Motion:
   - Show TWO interacting objects.
   - Clearly show the action force from object A on object B.
   - Clearly show the reaction force from object B on object A.
   - The forces must have equal magnitude.
   - The forces must point in opposite directions.
   - Make clear that the forces act on DIFFERENT objects.
   - A person pushing a wall is a preferred example.
   - Do NOT show the action and reaction forces as two forces
     acting on the same object.
   - Do NOT confuse Newton's Third Law with acceleration.

10. If the topic is Harmonic Motion, show concepts such as:
    - oscillation
    - equilibrium position
    - restoring force
    - spring and mass
    - periodic motion

11. If the topic is Gravitation, show:
    - Earth
    - gravitational attraction
    - falling object

12. If the topic is Waves, show:
    - crest
    - trough
    - wavelength
    - amplitude

13. If the topic is Electricity or Circuits, show:
    - battery
    - wires
    - current
    - load/bulb
    - closed circuit

14. Keep the visual clear and suitable for a classroom.

15. Use large readable labels and avoid excessive text.
"""
    # ========================================================
    # DETERMINISTIC PHYSICS VISUALS
    # ========================================================
    #
    # For important physics concepts where exact relationships
    # matter, use the deterministic SVG fallback.
    #
    # This guarantees that Newton's Third Law always shows
    # equal and opposite forces acting on different objects.
    # ========================================================

    subject_lower = str(subject).lower().strip()
    topic_lower = str(topic).lower().strip()

    if (
        "physics" in subject_lower
        and "newton" in topic_lower
        and (
            "third" in topic_lower
            or "3rd" in topic_lower
            or "action" in topic_lower
            or "reaction" in topic_lower
        )
    ):
        print(
            "Using deterministic Newton's Third Law educational visual."
        )

        return _create_svg_fallback(
            subject=subject,
            topic=topic,
            grade=grade,
            concept=concept,
            style=style,
        )

    
    # ========================================================
    # TRY GEMINI
    # ========================================================

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

    # ========================================================
    # FALLBACK
    # ========================================================

    return _create_svg_fallback(
        subject=subject,
        topic=topic,
        grade=grade,
        concept=concept,
        style=style,
    )