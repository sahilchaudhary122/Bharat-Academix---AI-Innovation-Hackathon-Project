import json
import os
import re
import shutil
import subprocess
import uuid
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from groq import Groq


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is not configured.")

client = Groq(api_key=GROQ_API_KEY)


# ============================================================
# DIRECTORIES
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

MEDIA_DIR = BASE_DIR / "media" / "generated"
ANIMATION_DIR = MEDIA_DIR / "animations"
MANIM_MEDIA_DIR = ANIMATION_DIR / "manim_media"

MEDIA_DIR.mkdir(parents=True, exist_ok=True)
ANIMATION_DIR.mkdir(parents=True, exist_ok=True)
MANIM_MEDIA_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# OPTIONAL TTS INTEGRATION
# ============================================================

try:
    from services.tts_service import generate_speech
except Exception:
    generate_speech = None


# ============================================================
# GENERAL HELPERS
# ============================================================

def _safe_name(
    value: Any,
    fallback: str = "object",
) -> str:

    name = re.sub(
        r"[^a-zA-Z0-9_]",
        "_",
        str(value or ""),
    )

    name = re.sub(
        r"_+",
        "_",
        name,
    ).strip("_")

    if not name:
        name = fallback

    if name[0].isdigit():
        name = "_" + name

    return name


def _short_text(
    value: Any,
    limit: int,
) -> str:

    text = (
        str(value or "")
        .replace("\n", " ")
        .replace("\r", " ")
        .strip()
    )

    if len(text) <= limit:
        return text

    return (
        text[: max(1, limit - 1)]
        .rstrip()
        + "…"
    )


def _safe_duration(
    value: Any,
    default: float = 1.0,
) -> float:
    """
    Validate AI-generated animation duration.

    Used for NORMALIZATION of AI output.

    Synchronization code later may intentionally
    use shorter durations.
    """

    try:
        duration = float(value)
    except (TypeError, ValueError):
        duration = default

    return max(
        0.45,
        min(duration, 3.0),
    )


def _sync_duration(
    value: Any,
    default: float = 1.0,
) -> float:
    """
    Validate durations AFTER synchronization.

    Unlike _safe_duration(), this function allows
    very short animation durations when necessary
    to fit the narration duration.
    """

    try:
        duration = float(value)
    except (TypeError, ValueError):
        duration = default

    return max(
        0.01,
        min(duration, 3.0),
    )


def _py_string(value: Any) -> str:
    """
    Return a safe Python literal for generated source code.
    """

    return repr(
        str(value or "")
    )


# ============================================================
# LATEX FIXER
# ============================================================

def _latex_safe_formula(
    value: Any,
) -> str:
    """
    Normalize AI-generated formulas before passing
    them to MathTex.
    """

    formula = str(
        value or ""
    ).strip()

    if not formula:
        return ""

    # --------------------------------------------------------
    # DOUBLE ESCAPED LATEX
    # --------------------------------------------------------

    formula = formula.replace(
        "\\\\",
        "\\",
    )

    # --------------------------------------------------------
    # UNICODE SUBSCRIPTS
    # --------------------------------------------------------

    subscript = {
        "₀": "_0",
        "₁": "_1",
        "₂": "_2",
        "₃": "_3",
        "₄": "_4",
        "₅": "_5",
        "₆": "_6",
        "₇": "_7",
        "₈": "_8",
        "₉": "_9",
    }

    for char, replacement in subscript.items():
        formula = formula.replace(
            char,
            replacement,
        )

    # --------------------------------------------------------
    # UNICODE SUPERSCRIPTS
    # --------------------------------------------------------

    superscript = {
        "⁰": "^0",
        "¹": "^1",
        "²": "^2",
        "³": "^3",
        "⁴": "^4",
        "⁵": "^5",
        "⁶": "^6",
        "⁷": "^7",
        "⁸": "^8",
        "⁹": "^9",
    }

    for char, replacement in superscript.items():
        formula = formula.replace(
            char,
            replacement,
        )

    # --------------------------------------------------------
    # SYMBOLS
    # --------------------------------------------------------

    replacements = {
        "×": r"\times ",
        "÷": r"\div ",
        "±": r"\pm ",
        "≤": r"\leq ",
        "≥": r"\geq ",
        "≠": r"\neq ",
        "≈": r"\approx ",
        "∝": r"\propto ",
        "∞": r"\infty ",
        "→": r"\rightarrow ",
        "←": r"\leftarrow ",
        "↔": r"\leftrightarrow ",
        "α": r"\alpha ",
        "β": r"\beta ",
        "γ": r"\gamma ",
        "δ": r"\delta ",
        "θ": r"\theta ",
        "λ": r"\lambda ",
        "μ": r"\mu ",
        "π": r"\pi ",
        "ρ": r"\rho ",
        "σ": r"\sigma ",
        "φ": r"\phi ",
        "ω": r"\omega ",
        "Ω": r"\Omega ",
        "Δ": r"\Delta ",
    }

    for char, replacement in replacements.items():
        formula = formula.replace(
            char,
            replacement,
        )

    # --------------------------------------------------------
    # MULTIPLICATION
    # --------------------------------------------------------

    formula = re.sub(
        r"\s*\*\s*",
        r" \\cdot ",
        formula,
    )

    # --------------------------------------------------------
    # SIMPLE POWERS
    # --------------------------------------------------------

    formula = re.sub(
        r"([A-Za-z0-9)])\^([0-9A-Za-z]+)",
        r"\1^{\2}",
        formula,
    )

    # --------------------------------------------------------
    # SUBSCRIPTS
    # --------------------------------------------------------

    formula = re.sub(
        r"([A-Za-z])_([0-9]+)",
        r"\1_{\2}",
        formula,
    )

    # --------------------------------------------------------
    # MARKDOWN MATH
    # --------------------------------------------------------

    formula = formula.replace(
        "$$",
        "",
    ).strip()

    if (
        formula.startswith("$")
        and formula.endswith("$")
    ):
        formula = formula[1:-1].strip()

    # --------------------------------------------------------
    # WHITESPACE
    # --------------------------------------------------------

    formula = re.sub(
        r"\s+",
        " ",
        formula,
    ).strip()

    return formula


# ============================================================
# AI PLAN GENERATION
# ============================================================

def generate_animation_plan(
    subject: str,
    topic: str,
    grade: str,
    concept: str,
) -> dict:
    """
    Generate a topic-specific visual lesson plan.
    """

    prompt = f"""
You are an expert educational animation director.

Create an animation plan for:

Subject: {subject}
Topic: {topic}
Grade: {grade}
Concept: {concept}

The animation is rendered by Python Manim.

CRITICAL RULES:

- The topic can be ANY subject.
- Do not assume a fixed topic.
- Choose visuals that actually explain the topic.

Physics:
- diagrams
- forces
- formulas
- simulations
- graphs

Mathematics:
- equations
- graphs
- step-by-step transformations

Biology:
- structures
- labels
- processes

History:
- timelines
- maps
- events

Programming:
- code
- flow
- output
- architecture

Use 3 to 5 scenes.

Each scene teaches exactly one main idea.

Prefer visuals over paragraphs.

Object labels must be very short:
normally 1-2 words or symbols.

Do not repeat object labels as scene labels.

Use at most 6 objects per scene.

Use at most 6 actions per scene.

Titles must be short.

Descriptions must be short.

Narration must be natural spoken English
and 1-3 short sentences.

Do not put equations in narration.

Formulas MUST use simple LaTeX such as:

M_1
M_2
r^2
\\frac{{a}}{{b}}
\\cdot

NEVER use Unicode subscripts/superscripts in formulas.

NEVER use Markdown code fences.

Allowed object types:

planet, earth, sun, star, ball, mass,
particle, object, arrow, axis, graph,
wave, circle, rectangle, box, triangle,
line, spring, battery, resistor,
molecule, atom, text, formula,
equation, math

Allowed actions:

appear, disappear, move,
move_left, move_right,
move_up, move_down,
oscillate, rotate, draw,
trace, grow, shrink,
bounce, highlight, connect

Return ONLY valid JSON.

Use this exact structure:

{{
  "title": "...",
  "summary": "...",
  "scenes": [
    {{
      "title": "...",
      "description": "...",
      "narration": "...",
      "objects": [
        {{
          "type": "...",
          "name": "...",
          "label": "...",
          "formula": ""
        }}
      ],
      "actions": [
        {{
          "target": "...",
          "action": "...",
          "duration": 1.2
        }}
      ],
      "formula": ""
    }}
  ]
}}
"""

    response = client.chat.completions.create(
        model="qwen/qwen3.8-27b",
        messages=[
            {
                "role": "system",
                "content": (
                    "Return only valid JSON for "
                    "an educational Manim plan."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.3,
        max_tokens=5000,
    )

    text = response.choices[0].message.content

    if not text:
        raise RuntimeError(
            "Groq returned an empty animation plan."
        )

    text = text.strip()

    text = re.sub(
        r"^```(?:json)?\s*",
        "",
        text,
        flags=re.I,
    )

    text = re.sub(
        r"\s*```$",
        "",
        text,
    )

    try:

        plan = json.loads(text)

    except json.JSONDecodeError as exc:

        raise RuntimeError(
            "Groq returned invalid JSON:\n"
            f"{text}"
        ) from exc

    if (
        not isinstance(plan, dict)
        or not isinstance(
            plan.get("scenes"),
            list,
        )
    ):
        raise RuntimeError(
            "Invalid animation plan: scenes are missing."
        )

    if not plan["scenes"]:
        raise RuntimeError(
            "Groq returned zero scenes."
        )

    return _normalize_plan(plan)


# ============================================================
# PLAN NORMALIZATION
# ============================================================

def _normalize_plan(
    plan: dict,
) -> dict:
    """
    Protect Manim from bad AI output.
    """

    normalized_scenes = []
    used_scene_count = 0

    for raw_scene in plan.get(
        "scenes",
        [],
    )[:5]:

        if not isinstance(
            raw_scene,
            dict,
        ):
            continue

        scene = dict(
            raw_scene
        )

        used_scene_count += 1

        # ----------------------------------------------------
        # TITLE
        # ----------------------------------------------------

        scene["title"] = _short_text(
            scene.get(
                "title",
                "Concept",
            ),
            38,
        )

        # ----------------------------------------------------
        # DESCRIPTION
        # ----------------------------------------------------

        scene["description"] = _short_text(
            scene.get(
                "description",
                "",
            ),
            90,
        )

        # ----------------------------------------------------
        # NARRATION
        # ----------------------------------------------------

        narration = str(
            scene.get(
                "narration",
                scene.get(
                    "description",
                    "",
                ),
            )
        ).strip()

        if not narration:

            narration = str(
                scene.get(
                    "description",
                    "",
                )
            ).strip()

        if not narration:

            narration = str(
                scene.get(
                    "title",
                    f"Scene {used_scene_count}",
                )
            ).strip()

        scene["narration"] = _short_text(
            narration,
            360,
        )

        # ----------------------------------------------------
        # FORMULA
        # ----------------------------------------------------

        scene_formula = _latex_safe_formula(
            scene.get(
                "formula",
                "",
            )
        )

        scene["formula"] = scene_formula

        # ====================================================
        # OBJECTS
        # ====================================================

        raw_objects = scene.get(
            "objects",
            [],
        )

        if not isinstance(
            raw_objects,
            list,
        ):
            raw_objects = []

        objects = []
        used_names = set()

        for i, raw_obj in enumerate(
            raw_objects[:6]
        ):

            if not isinstance(
                raw_obj,
                dict,
            ):
                continue

            obj = dict(
                raw_obj
            )

            obj_type = str(
                obj.get(
                    "type",
                    "circle",
                )
            ).lower().strip()

            # ------------------------------------------------
            # SAFE UNIQUE NAME
            # ------------------------------------------------

            name = _safe_name(
                obj.get(
                    "name",
                    f"object_{i}",
                ),
                f"object_{i}",
            )

            base_name = name
            counter = 2

            while name in used_names:

                name = (
                    f"{base_name}_{counter}"
                )

                counter += 1

            used_names.add(name)

            obj["type"] = obj_type
            obj["name"] = name

            obj["label"] = _short_text(
                obj.get(
                    "label",
                    "",
                ),
                12,
            )

            # ------------------------------------------------
            # FORMULA OBJECT
            # ------------------------------------------------

            if obj_type in {
                "formula",
                "equation",
                "math",
            }:

                # Scene-level formula takes priority.
                if scene_formula:
                    continue

                obj["formula"] = (
                    _latex_safe_formula(
                        obj.get(
                            "formula",
                            obj.get(
                                "label",
                                "",
                            ),
                        )
                    )
                )

            objects.append(obj)

        scene["objects"] = objects

        # Labels are embedded inside objects.
        scene["labels"] = []

        # ====================================================
        # ACTIONS
        # ====================================================

        raw_actions = scene.get(
            "actions",
            [],
        )

        if not isinstance(
            raw_actions,
            list,
        ):
            raw_actions = []

        actions = []

        valid_names = {
            obj["name"]
            for obj in objects
        }

        for raw_action in raw_actions[:6]:

            if not isinstance(
                raw_action,
                dict,
            ):
                continue

            action = dict(
                raw_action
            )

            target = _safe_name(
                action.get(
                    "target",
                    "",
                )
            )

            if target not in valid_names:
                continue

            action_name = str(
                action.get(
                    "action",
                    "appear",
                )
            ).lower().strip()

            if action_name not in {
                "appear",
                "disappear",
                "move",
                "move_left",
                "move_right",
                "move_up",
                "move_down",
                "oscillate",
                "rotate",
                "draw",
                "trace",
                "grow",
                "shrink",
                "bounce",
                "highlight",
                "connect",
            }:

                action_name = "highlight"

            actions.append(
                {
                    "target": target,
                    "action": action_name,
                    "duration": _safe_duration(
                        action.get(
                            "duration",
                            1.0,
                        )
                    ),
                }
            )

        scene["actions"] = actions

        normalized_scenes.append(
            scene
        )

    if not normalized_scenes:
        raise RuntimeError(
            "Animation plan contains no usable scenes."
        )

    result = dict(
        plan
    )

    result["title"] = _short_text(
        result.get(
            "title",
            "AI Lesson",
        ),
        50,
    )

    result["summary"] = _short_text(
        result.get(
            "summary",
            "",
        ),
        120,
    )

    result["scenes"] = normalized_scenes

    return result


# ============================================================
# MANIM OBJECT BUILDERS
# ============================================================

def _build_object_code(
    obj: dict,
    index: int,
) -> str:

    obj_type = str(
        obj.get(
            "type",
            "circle",
        )
    ).lower().strip()

    name = _safe_name(
        obj.get(
            "name",
            f"object_{index}",
        ),
        f"object_{index}",
    )

    label = str(
        obj.get(
            "label",
            "",
        )
    ).strip()

    label_literal = _py_string(
        _short_text(
            label,
            12,
        )
    )

    # ========================================================
    # FORMULA
    # ========================================================

    if obj_type in {
        "formula",
        "equation",
        "math",
    }:

        formula = _latex_safe_formula(
            obj.get(
                "formula",
                obj.get(
                    "label",
                    "",
                ),
            )
        )

        if not formula:
            formula = r"x = y"

        return f"""
        {name} = MathTex(
            {_py_string(formula)},
            font_size=19
        )

        if {name}.width > 4.8:
            {name}.scale_to_fit_width(4.8)

        if {name}.height > 0.62:
            {name}.scale_to_fit_height(0.62)
"""

    # ========================================================
    # TEXT
    # ========================================================

    if obj_type == "text":

        return f"""
        {name} = Text(
            {label_literal},
            font_size=14
        )

        if {name}.width > 3.0:
            {name}.scale_to_fit_width(3.0)

        if {name}.height > 0.45:
            {name}.scale_to_fit_height(0.45)
"""

    # ========================================================
    # EARTH / PLANET
    # ========================================================

    if obj_type in {
        "earth",
        "planet",
        "world",
    }:

        return f"""
        {name}_main = Circle(
            radius=0.62,
            fill_opacity=1
        )

        {name}_label = Text(
            {label_literal},
            font_size=11
        )

        if {name}_label.width > 1.0:
            {name}_label.scale_to_fit_width(1.0)

        if {name}_label.height > 0.25:
            {name}_label.scale_to_fit_height(0.25)

        {name}_label.move_to(
            {name}_main.get_center()
        )

        {name} = VGroup(
            {name}_main,
            {name}_label
        )

        if {name}.width > 1.65:
            {name}.scale_to_fit_width(1.65)

        if {name}.height > 1.65:
            {name}.scale_to_fit_height(1.65)
"""

    # ========================================================
    # SUN
    # ========================================================

    if obj_type == "sun":

        return f"""
        {name}_main = Circle(
            radius=0.52,
            fill_opacity=1
        )

        {name}_rays = VGroup()

        for angle in np.linspace(
            0,
            TAU,
            8,
            endpoint=False
        ):

            {name}_rays.add(
                Line(
                    {name}_main.get_center()
                    + 0.68 * np.array([
                        np.cos(angle),
                        np.sin(angle),
                        0
                    ]),

                    {name}_main.get_center()
                    + 0.92 * np.array([
                        np.cos(angle),
                        np.sin(angle),
                        0
                    ])
                )
            )

        {name}_visual = VGroup(
            {name}_main,
            {name}_rays
        )

        {name}_label = Text(
            {label_literal},
            font_size=11
        )

        if {name}_label.width > 1.25:
            {name}_label.scale_to_fit_width(1.25)

        {name}_label.next_to(
            {name}_visual,
            DOWN,
            buff=0.07
        )

        {name} = VGroup(
            {name}_visual,
            {name}_label
        )

        if {name}.width > 1.9:
            {name}.scale_to_fit_width(1.9)

        if {name}.height > 1.8:
            {name}.scale_to_fit_height(1.8)
"""

    # ========================================================
    # MASS / BALL / PARTICLE / OBJECT / ATOM
    # ========================================================

    if obj_type in {
        "mass",
        "ball",
        "particle",
        "object",
        "atom",
    }:

        return f"""
        {name}_main = Circle(
            radius=0.34,
            fill_opacity=1
        )

        {name}_label = Text(
            {label_literal},
            font_size=10
        )

        if {name}_label.width > 0.52:
            {name}_label.scale_to_fit_width(0.52)

        if {name}_label.height > 0.22:
            {name}_label.scale_to_fit_height(0.22)

        {name}_label.move_to(
            {name}_main.get_center()
        )

        {name} = VGroup(
            {name}_main,
            {name}_label
        )

        if {name}.width > 1.05:
            {name}.scale_to_fit_width(1.05)

        if {name}.height > 1.05:
            {name}.scale_to_fit_height(1.05)
"""

    # ========================================================
    # ARROW
    # ========================================================

    if obj_type == "arrow":

        return f"""
        {name}_main = Arrow(
            LEFT * 0.70,
            RIGHT * 0.70,
            buff=0,
            max_tip_length_to_length_ratio=0.18
        )

        {name}_label = Text(
            {label_literal},
            font_size=10
        )

        if {name}_label.width > 0.7:
            {name}_label.scale_to_fit_width(0.7)

        {name}_label.next_to(
            {name}_main,
            UP,
            buff=0.04
        )

        {name} = VGroup(
            {name}_main,
            {name}_label
        )

        if {name}.width > 1.75:
            {name}.scale_to_fit_width(1.75)

        if {name}.height > 0.65:
            {name}.scale_to_fit_height(0.65)
"""

    # ========================================================
    # AXIS
    # ========================================================

    if obj_type == "axis":

        return f"""
        {name}_main = Line(
            LEFT * 2.0,
            RIGHT * 2.0
        )

        {name}_label = Text(
            {label_literal},
            font_size=10
        )

        if {name}_label.width > 1.4:
            {name}_label.scale_to_fit_width(1.4)

        {name}_label.next_to(
            {name}_main,
            DOWN,
            buff=0.05
        )

        {name} = VGroup(
            {name}_main,
            {name}_label
        )

        if {name}.width > 4.3:
            {name}.scale_to_fit_width(4.3)
"""

    # ========================================================
    # GRAPH / WAVE
    # ========================================================

    if obj_type in {
        "graph",
        "wave",
    }:

        return f"""
        {name}_axes = Axes(
            x_range=[-5, 5, 1],
            y_range=[-2, 2, 1],
            x_length=5.8,
            y_length=2.6
        )

        {name}_plot = {name}_axes.plot(
            lambda x: np.sin(x)
        )

        {name}_label = Text(
            {label_literal},
            font_size=10
        )

        if {name}_label.width > 2.5:
            {name}_label.scale_to_fit_width(2.5)

        {name}_label.next_to(
            {name}_axes,
            UP,
            buff=0.04
        )

        {name} = VGroup(
            {name}_axes,
            {name}_plot,
            {name}_label
        )

        if {name}.width > 6.2:
            {name}.scale_to_fit_width(6.2)

        if {name}.height > 2.9:
            {name}.scale_to_fit_height(2.9)
"""

    # ========================================================
    # SPRING
    # ========================================================

    if obj_type == "spring":

        return f"""
        {name}_spring = ParametricFunction(
            lambda t: np.array([
                0.28 * np.sin(10 * t),
                t,
                0
            ]),
            t_range=[-1.2, 1.2]
        )

        {name}_label = Text(
            {label_literal},
            font_size=10
        )

        if {name}_label.width > 1.2:
            {name}_label.scale_to_fit_width(1.2)

        {name}_label.next_to(
            {name}_spring,
            RIGHT,
            buff=0.08
        )

        {name} = VGroup(
            {name}_spring,
            {name}_label
        )

        if {name}.height > 2.8:
            {name}.scale_to_fit_height(2.8)
"""

    # ========================================================
    # BATTERY
    # ========================================================

    if obj_type == "battery":

        return f"""
        {name}_long = Line(
            UP * 0.60,
            DOWN * 0.60
        ).shift(
            LEFT * 0.16
        )

        {name}_short = Line(
            UP * 0.35,
            DOWN * 0.35
        ).shift(
            RIGHT * 0.16
        )

        {name}_visual = VGroup(
            {name}_long,
            {name}_short
        )

        {name}_label = Text(
            {label_literal},
            font_size=10
        )

        {name}_label.next_to(
            {name}_visual,
            DOWN,
            buff=0.06
        )

        {name} = VGroup(
            {name}_visual,
            {name}_label
        )
"""

    # ========================================================
    # RESISTOR
    # ========================================================

    if obj_type == "resistor":

        return f"""
        {name}_main = Polygon(
            LEFT * 0.70,
            LEFT * 0.45 + UP * 0.22,
            LEFT * 0.15 + DOWN * 0.22,
            RIGHT * 0.15 + UP * 0.22,
            RIGHT * 0.45 + DOWN * 0.22,
            RIGHT * 0.70,
            stroke_width=2
        )

        {name}_label = Text(
            {label_literal},
            font_size=10
        )

        {name}_label.next_to(
            {name}_main,
            DOWN,
            buff=0.05
        )

        {name} = VGroup(
            {name}_main,
            {name}_label
        )
"""

    # ========================================================
    # RECTANGLE / BOX
    # ========================================================

    if obj_type in {
        "rectangle",
        "box",
    }:

        return f"""
        {name}_main = RoundedRectangle(
            width=1.55,
            height=0.85,
            corner_radius=0.12
        )

        {name}_label = Text(
            {label_literal},
            font_size=10
        )

        if {name}_label.width > 1.2:
            {name}_label.scale_to_fit_width(1.2)

        {name}_label.move_to(
            {name}_main.get_center()
        )

        {name} = VGroup(
            {name}_main,
            {name}_label
        )

        if {name}.width > 2.0:
            {name}.scale_to_fit_width(2.0)

        if {name}.height > 1.2:
            {name}.scale_to_fit_height(1.2)
"""

    # ========================================================
    # TRIANGLE
    # ========================================================

    if obj_type == "triangle":

        return f"""
        {name}_main = Triangle().scale(0.45)

        {name}_label = Text(
            {label_literal},
            font_size=10
        )

        {name}_label.next_to(
            {name}_main,
            DOWN,
            buff=0.05
        )

        {name} = VGroup(
            {name}_main,
            {name}_label
        )
"""

    # ========================================================
    # LINE
    # ========================================================

    if obj_type == "line":

        return f"""
        {name}_main = Line(
            LEFT * 1.25,
            RIGHT * 1.25
        )

        {name}_label = Text(
            {label_literal},
            font_size=10
        )

        if {name}_label.width > 1.6:
            {name}_label.scale_to_fit_width(1.6)

        {name}_label.next_to(
            {name}_main,
            UP,
            buff=0.04
        )

        {name} = VGroup(
            {name}_main,
            {name}_label
        )

        if {name}.width > 3.0:
            {name}.scale_to_fit_width(3.0)
"""

    # ========================================================
    # CIRCLE / DEFAULT
    # ========================================================

    return f"""
        {name}_main = Circle(
            radius=0.45
        )

        {name}_label = Text(
            {label_literal},
            font_size=10
        )

        if {name}_label.width > 0.95:
            {name}_label.scale_to_fit_width(0.95)

        {name}_label.next_to(
            {name}_main,
            DOWN,
            buff=0.05
        )

        {name} = VGroup(
            {name}_main,
            {name}_label
        )

        if {name}.width > 1.45:
            {name}.scale_to_fit_width(1.45)

        if {name}.height > 1.45:
            {name}.scale_to_fit_height(1.45)
"""


# ============================================================
# ACTION BUILDER
# ============================================================

def _build_action_code(
    action: dict,
) -> str:

    target = _safe_name(
        action.get(
            "target",
            "",
        )
    )

    action_name = str(
        action.get(
            "action",
            "appear",
        )
    ).lower().strip()

    # IMPORTANT:
    # Use synchronized duration directly.
    duration = _sync_duration(
        action.get(
            "duration",
            1.0,
        )
    )

    # ========================================================
    # APPEAR
    # ========================================================

    if action_name == "appear":

        return f"""
        if "{target}" in objects:
            self.play(
                FadeIn(
                    objects["{target}"]
                ),
                run_time={duration:.3f}
            )
"""

    # ========================================================
    # DISAPPEAR
    # ========================================================

    if action_name == "disappear":

        return f"""
        if "{target}" in objects:
            self.play(
                FadeOut(
                    objects["{target}"]
                ),
                run_time={duration:.3f}
            )
"""

    # ========================================================
    # MOVEMENT
    # ========================================================

    movement = {
        "move": "RIGHT * 0.45",
        "move_right": "RIGHT * 0.45",
        "move_left": "LEFT * 0.45",
        "move_up": "UP * 0.40",
        "move_down": "DOWN * 0.40",
    }

    if action_name in movement:

        return f"""
        if "{target}" in objects:
            self.play(
                objects["{target}"].animate.shift(
                    {movement[action_name]}
                ),
                run_time={duration:.3f}
            )
"""

    # ========================================================
    # OSCILLATE
    # ========================================================

    if action_name == "oscillate":

        q = duration / 4

        return f"""
        if "{target}" in objects:

            self.play(
                objects["{target}"].animate.shift(
                    DOWN * 0.28
                ),
                run_time={q:.3f}
            )

            self.play(
                objects["{target}"].animate.shift(
                    UP * 0.56
                ),
                run_time={q * 2:.3f}
            )

            self.play(
                objects["{target}"].animate.shift(
                    DOWN * 0.28
                ),
                run_time={q:.3f}
            )
"""

    # ========================================================
    # ROTATE
    # ========================================================

    if action_name == "rotate":

        return f"""
        if "{target}" in objects:
            self.play(
                Rotate(
                    objects["{target}"],
                    angle=PI
                ),
                run_time={duration:.3f}
            )
"""

    # ========================================================
    # GROW
    # ========================================================

    if action_name == "grow":

        return f"""
        if "{target}" in objects:
            self.play(
                objects["{target}"].animate.scale(1.06),
                run_time={duration:.3f}
            )
"""

    # ========================================================
    # SHRINK
    # ========================================================

    if action_name == "shrink":

        return f"""
        if "{target}" in objects:
            self.play(
                objects["{target}"].animate.scale(0.94),
                run_time={duration:.3f}
            )
"""

    # ========================================================
    # DRAW / TRACE
    # ========================================================

    if action_name in {
        "draw",
        "trace",
    }:

        return f"""
        if "{target}" in objects:
            self.play(
                Create(
                    objects["{target}"]
                ),
                run_time={duration:.3f}
            )
"""

    # ========================================================
    # BOUNCE
    # ========================================================

    if action_name == "bounce":

        half = duration / 2

        return f"""
        if "{target}" in objects:

            self.play(
                objects["{target}"].animate.shift(
                    UP * 0.30
                ),
                run_time={half:.3f}
            )

            self.play(
                objects["{target}"].animate.shift(
                    DOWN * 0.30
                ),
                run_time={half:.3f}
            )
"""

    # ========================================================
    # HIGHLIGHT / CONNECT / UNKNOWN
    # ========================================================

    return f"""
        if "{target}" in objects:
            self.play(
                Indicate(
                    objects["{target}"],
                    scale_factor=1.03
                ),
                run_time={duration:.3f}
            )
"""


# ============================================================
# LAYOUT
# ============================================================

def _build_layout_code(
    object_count: int,
    has_formula: bool,
) -> str:
    """
    Fixed safe zones:

        top    = title + description
        middle = teaching visuals
        bottom = formula
    """

    center_y = (
        0.05
        if has_formula
        else -0.05
    )

    max_height = (
        2.35
        if has_formula
        else 2.75
    )

    if object_count <= 1:

        arrangement = f"""
            group.move_to(
                UP * {center_y}
            )
"""

    elif object_count == 2:

        arrangement = f"""
            group.arrange(
                RIGHT,
                buff=0.85,
                aligned_edge=DOWN
            )

            group.move_to(
                UP * {center_y}
            )
"""

    elif object_count <= 4:

        arrangement = f"""
            group.arrange_in_grid(
                rows=2,
                cols=2,
                buff=(0.65, 0.45)
            )

            group.move_to(
                UP * {center_y}
            )
"""

    else:

        arrangement = f"""
            group.arrange_in_grid(
                rows=2,
                cols=3,
                buff=(0.55, 0.38)
            )

            group.move_to(
                UP * {center_y}
            )
"""

    return f"""
        if visual_objects:

            group = VGroup(
                *visual_objects
            )

{arrangement}

            if group.width > 7.1:
                group.scale_to_fit_width(7.1)

            if group.height > {max_height}:
                group.scale_to_fit_height(
                    {max_height}
                )

            if group.width > 7.1:
                group.scale_to_fit_width(7.1)

            group.move_to(
                UP * {center_y}
            )
"""


# ============================================================
# MANIM SCRIPT GENERATOR
# ============================================================

def create_manim_script(
    plan: dict,
    subject: str,
    topic: str,
    scene_durations: list[float] | None = None,
) -> Path:

    plan = _normalize_plan(
        plan
    )

    if scene_durations is None:

        scene_durations = [
            0.0
            for _ in plan["scenes"]
        ]

    if len(scene_durations) != len(
        plan["scenes"]
    ):

        raise ValueError(
            "Number of scene durations "
            "must match number of scenes."
        )

    scene_code = []

    for scene_index, scene in enumerate(
        plan["scenes"]
    ):

        target_duration = max(
            0.0,
            float(
                scene_durations[
                    scene_index
                ]
            ),
        )

        title = _short_text(
            scene.get(
                "title",
                f"Scene {scene_index + 1}",
            ),
            38,
        )

        description = _short_text(
            scene.get(
                "description",
                "",
            ),
            90,
        )

        objects = scene.get(
            "objects",
            [],
        )

        actions = scene.get(
            "actions",
            [],
        )

        formula = _latex_safe_formula(
            scene.get(
                "formula",
                "",
            )
        )

        # ====================================================
        # OBJECT CODE
        # ====================================================

        object_code = []
        registration = []

        for i, obj in enumerate(
            objects
        ):

            object_code.append(
                _build_object_code(
                    obj,
                    i,
                )
            )

            name = _safe_name(
                obj.get(
                    "name",
                    f"object_{i}",
                )
            )

            registration.append(
                (
                    "        objects["
                    f"{_py_string(name)}"
                    f"] = {name}"
                )
            )

        # ====================================================
        # FORMULA CODE
        # ====================================================

        formula_code = ""

        if formula:

            formula_code = f"""
        scene_formula = MathTex(
            {_py_string(formula)},
            font_size=18
        )

        if scene_formula.width > 5.0:
            scene_formula.scale_to_fit_width(5.0)

        if scene_formula.height > 0.60:
            scene_formula.scale_to_fit_height(0.60)

        scene_formula.to_edge(
            DOWN,
            buff=0.28
        )

        self.play(
            Write(scene_formula),
            run_time=0.65
        )
"""

        else:

            formula_code = """
        scene_formula = None
"""

        # ====================================================
        # SCENE TIMING
        # ====================================================

        # Fixed animation time.
        #
        # Title + description:
        #       0.50s
        #
        # Object appearance:
        #       0.55s
        #
        # Visual hold:
        #       0.35s
        #
        # Cleanup:
        #       0.40s

        base_scene_duration = (
            0.50
            + 0.55
            + 0.35
            + 0.40
        )

        # Formula animation.
        if formula:
            base_scene_duration += 0.65

        # ----------------------------------------------------
        # REQUESTED ACTION DURATION
        # ----------------------------------------------------

        action_duration = sum(
            _safe_duration(
                action.get(
                    "duration",
                    1.0,
                )
            )
            for action in actions
        )

        # ----------------------------------------------------
        # AVAILABLE ACTION TIME
        # ----------------------------------------------------

        available_action_time = max(
            0.0,
            target_duration
            - base_scene_duration,
        )

        # ----------------------------------------------------
        # SCALE ACTIONS
        # ----------------------------------------------------

        if (
            actions
            and action_duration
            > available_action_time
        ):

            if available_action_time > 0:

                scale_factor = (
                    available_action_time
                    / action_duration
                )

                for action in actions:

                    original_duration = (
                        _safe_duration(
                            action.get(
                                "duration",
                                1.0,
                            )
                        )
                    )

                    action["duration"] = (
                        original_duration
                        * scale_factor
                    )

            else:

                # There is no available time for actions.
                #
                # Use a tiny duration rather than
                # allowing actions to exceed narration.

                for action in actions:

                    action["duration"] = 0.01

            action_duration = sum(
                _sync_duration(
                    action.get(
                        "duration",
                        0.01,
                    )
                )
                for action in actions
            )

        # ====================================================
        # HOLD DURATION
        # ====================================================

        hold_duration = max(
            0.0,
            target_duration
            - base_scene_duration
            - action_duration,
        )

        # ====================================================
        # IMPORTANT:
        # BUILD ACTION CODE AFTER SCALING
        # ====================================================

        action_code = [
            _build_action_code(
                action
            )
            for action in actions
        ]

        # ====================================================
        # SCENE BLOCK
        # ====================================================

        scene_block = f"""
        # ==================================================
        # SCENE {scene_index + 1}
        # ==================================================

        scene_title = Text(
            {_py_string(title)},
            font_size=20
        )

        if scene_title.width > 6.7:
            scene_title.scale_to_fit_width(6.7)

        if scene_title.height > 0.42:
            scene_title.scale_to_fit_height(0.42)

        scene_title.to_edge(
            UP,
            buff=0.22
        )

        scene_description = Text(
            {_py_string(description)},
            font_size=10
        )

        if scene_description.width > 6.7:
            scene_description.scale_to_fit_width(6.7)

        if scene_description.height > 0.32:
            scene_description.scale_to_fit_height(0.32)

        scene_description.next_to(
            scene_title,
            DOWN,
            buff=0.06
        )

        self.play(
            Write(scene_title),
            FadeIn(scene_description),
            run_time=0.50
        )

        objects = {{}}

{''.join(object_code)}

{chr(10).join(registration)}

        visual_objects = list(
            objects.values()
        )

{_build_layout_code(
    len(objects),
    bool(formula)
)}

        # ----------------------------------------------
        # SHOW OBJECTS
        # ----------------------------------------------

        if visual_objects:

            self.play(
                *[
                    FadeIn(item)
                    for item in visual_objects
                ],
                run_time=0.55
            )

{''.join(action_code)}

{formula_code}

        # ----------------------------------------------
        # FINAL OVERFLOW CHECK
        # ----------------------------------------------

        if visual_objects:

            visible_group = VGroup(
                *visual_objects
            )

            max_h = {
                2.35
                if formula
                else 2.75
            }

            if visible_group.width > 7.1:
                visible_group.scale_to_fit_width(
                    7.1
                )

            if visible_group.height > max_h:
                visible_group.scale_to_fit_height(
                    max_h
                )

            if visible_group.width > 7.1:
                visible_group.scale_to_fit_width(
                    7.1
                )

        # ----------------------------------------------
        # KEEP VISUAL ON SCREEN
        # ----------------------------------------------

        self.wait(
            0.35
        )

        if {hold_duration:.3f} > 0:

            self.wait(
                {hold_duration:.3f}
            )

        # ----------------------------------------------
        # CLEAN SCENE
        # ----------------------------------------------

        fade_items = [
            scene_title,
            scene_description
        ]

        if scene_formula is not None:

            fade_items.append(
                scene_formula
            )

        fade_items.extend(
            visual_objects
        )

        self.play(
            FadeOut(*fade_items),
            run_time=0.40
        )
"""

        scene_code.append(
            scene_block
        )

    # ========================================================
    # COMPLETE MANIM SCRIPT
    # ========================================================

    script = f'''from manim import *
import numpy as np


class AIAnimatedLesson(Scene):

    def construct(self):

        # ==================================================
        # INTRO
        # ==================================================

        # No separate intro.
        #
        # Scene 1 starts immediately.
        #
        # This keeps the Manim timeline aligned
        # with the narration timeline.

{''.join(scene_code)}
'''

    path = (
        ANIMATION_DIR
        / f"animation_{uuid.uuid4().hex}.py"
    )

    path.write_text(
        script,
        encoding="utf-8",
    )

    return path


# ============================================================
# MANIM RENDER
# ============================================================

def render_animation(
    plan: dict,
    subject: str,
    topic: str,
    scene_durations: list[float] | None = None,
) -> str:

    print(
        "\n========== ANIMATION GENERATION =========="
    )

    print(
        "Running Manim..."
    )

    script_path = create_manim_script(
        plan=plan,
        subject=subject,
        topic=topic,
        scene_durations=scene_durations,
    )

    command = [
        "manim",
        "-qm",
        "--media_dir",
        str(MANIM_MEDIA_DIR),
        str(script_path),
        "AIAnimatedLesson",
    ]

    try:

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
        )

    except FileNotFoundError as exc:

        raise RuntimeError(
            "Manim was not found. "
            "Activate the virtual environment "
            "and install Manim."
        ) from exc

    if result.returncode != 0:

        combined = (
            result.stderr or ""
        ) + "\n" + (
            result.stdout or ""
        )

        raise RuntimeError(
            "Manim rendering failed:\n\n"
            + combined[-16000:]
        )

    candidates = list(
        MANIM_MEDIA_DIR.rglob(
            "AIAnimatedLesson.mp4"
        )
    )

    if not candidates:

        raise FileNotFoundError(
            "Manim completed but "
            "AIAnimatedLesson.mp4 was not found."
        )

    source_video = max(
        candidates,
        key=lambda p: p.stat().st_mtime,
    )

    final_video = (
        MEDIA_DIR
        / f"ai_animation_{uuid.uuid4().hex}.mp4"
    )

    shutil.copy2(
        source_video,
        final_video,
    )

    print(
        "Animation generated:",
        final_video,
    )

    return str(
        final_video
    )


# ============================================================
# AUDIO
# ============================================================

def _scene_narrations(
    plan: dict,
) -> list[str]:
    """
    Extract exactly one narration for every scene.

    A fallback narration is generated from description/title
    so scene count always matches TTS duration count.
    """

    narrations = []

    for scene_index, scene in enumerate(
        plan.get(
            "scenes",
            [],
        ),
        start=1,
    ):

        if not isinstance(
            scene,
            dict,
        ):
            narration = f"Scene {scene_index}."
        else:

            narration = str(
                scene.get(
                    "narration",
                    "",
                )
            ).strip()

            if not narration:

                narration = str(
                    scene.get(
                        "description",
                        "",
                    )
                ).strip()

            if not narration:

                narration = str(
                    scene.get(
                        "title",
                        f"Scene {scene_index}",
                    )
                ).strip()

        narration = re.sub(
            r"\s+",
            " ",
            narration,
        ).strip()

        if not narration:

            narration = (
                f"Let's understand "
                f"this idea in scene "
                f"{scene_index}."
            )

        narrations.append(
            narration
        )

    return narrations


# ============================================================
# AUDIO DURATION
# ============================================================

def _get_audio_duration(
    audio_file: str | Path,
) -> float:
    """
    Get audio duration using ffprobe.
    """

    command = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(audio_file),
    ]

    try:

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
        )

        return float(
            result.stdout.strip()
        )

    except Exception as exc:

        print(
            "WARNING: Could not determine "
            f"audio duration: {exc}"
        )

        return 0.0


# ============================================================
# GENERATE SCENE AUDIO
# ============================================================

def generate_scene_audio(
    plan: dict,
) -> tuple[list[str], list[float]]:
    """
    Generate one WAV file per scene narration.

    Returns:

        (
            audio_files,
            scene_durations
        )
    """

    if generate_speech is None:

        print(
            "WARNING: TTS service is unavailable."
        )

        return [], []

    narrations = _scene_narrations(
        plan
    )

    if not narrations:

        print(
            "WARNING: No narration available."
        )

        return [], []

    audio_files = []
    scene_durations = []

    print(
        "\n========== SCENE AUDIO GENERATION =========="
    )

    for index, narration in enumerate(
        narrations,
        start=1,
    ):

        print(
            f"\n----- Scene {index} -----"
        )

        print(
            "Narration:",
            narration,
        )

        # ----------------------------------------------------
        # TTS
        # ----------------------------------------------------

        try:

            try:

                audio_file = generate_speech(
                    text=narration,
                    voice="Kore",
                )

            except TypeError:

                audio_file = generate_speech(
                    narration
                )

        except Exception as exc:

            raise RuntimeError(
                "TTS generation failed for "
                f"scene {index}: {exc}"
            ) from exc

        if not audio_file:

            raise RuntimeError(
                f"TTS returned no audio "
                f"for scene {index}."
            )

        audio_path = Path(
            str(audio_file)
        )

        if not audio_path.exists():

            raise RuntimeError(
                "TTS audio file does not exist "
                f"for scene {index}: {audio_path}"
            )

        if audio_path.stat().st_size == 0:

            raise RuntimeError(
                f"TTS audio file is empty "
                f"for scene {index}."
            )

        # ----------------------------------------------------
        # MEASURE DURATION
        # ----------------------------------------------------

        duration = _get_audio_duration(
            audio_path
        )

        if duration <= 0:

            raise RuntimeError(
                "Could not determine duration "
                f"for scene {index}."
            )

        scene_durations.append(
            duration
        )

        print(
            f"Scene {index} audio:"
        )

        print(
            audio_path
        )

        print(
            f"Scene {index} duration: "
            f"{duration:.2f} seconds"
        )

        audio_files.append(
            str(audio_path)
        )

    print(
        "\nGenerated",
        len(audio_files),
        "scene audio files.",
    )

    return (
        audio_files,
        scene_durations,
    )


# ============================================================
# AUDIO CONCATENATION
# ============================================================

def combine_scene_audio(
    audio_files: list[str],
) -> str | None:
    """
    Combine scene WAV files into one continuous WAV.

    Output:
        24 kHz
        mono
        PCM 16-bit
    """

    if not audio_files:
        return None

    valid_files = []

    for audio_file in audio_files:

        path = Path(
            audio_file
        )

        if not path.exists():

            raise FileNotFoundError(
                f"Scene audio does not exist: {path}"
            )

        if path.stat().st_size == 0:

            raise RuntimeError(
                f"Scene audio is empty: {path}"
            )

        valid_files.append(
            path
        )

    if not valid_files:
        return None

    concat_file = (
        MEDIA_DIR
        / f"audio_concat_{uuid.uuid4().hex}.txt"
    )

    combined_audio = (
        MEDIA_DIR
        / f"narration_{uuid.uuid4().hex}.wav"
    )

    # ========================================================
    # CONCAT FILE
    # ========================================================

    lines = []

    for path in valid_files:

        escaped = str(
            path
        ).replace(
            "'",
            "'\\''",
        )

        lines.append(
            f"file '{escaped}'"
        )

    concat_file.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )

    print(
        "\n========== COMBINING SCENE AUDIO =========="
    )

    command = [
        "ffmpeg",
        "-y",

        "-f",
        "concat",

        "-safe",
        "0",

        "-i",
        str(concat_file),

        "-ar",
        "24000",

        "-ac",
        "1",

        "-c:a",
        "pcm_s16le",

        str(combined_audio),
    ]

    try:

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
        )

    except FileNotFoundError as exc:

        raise RuntimeError(
            "FFmpeg was not found. "
            "Install FFmpeg and make sure "
            "'ffmpeg' is available in PATH."
        ) from exc

    finally:

        if concat_file.exists():

            try:
                concat_file.unlink()

            except OSError:
                pass

    if result.returncode != 0:

        raise RuntimeError(
            "FFmpeg audio concatenation failed:\n\n"
            + (
                result.stderr
                or result.stdout
                or "Unknown FFmpeg error."
            )[-12000:]
        )

    if not combined_audio.exists():

        raise RuntimeError(
            "FFmpeg did not create combined narration."
        )

    if combined_audio.stat().st_size == 0:

        raise RuntimeError(
            "Combined narration is empty."
        )

    duration = _get_audio_duration(
        combined_audio
    )

    print(
        "Combined narration:",
        combined_audio,
    )

    print(
        f"Combined narration duration: "
        f"{duration:.2f} seconds"
    )

    return str(
        combined_audio
    )


# ============================================================
# COMPLETE NARRATION PIPELINE
# ============================================================

def generate_narration_audio(
    plan: dict,
) -> tuple[
    str | None,
    list[float],
]:
    """
    Complete TTS pipeline:

        Scene 1 → TTS
        Scene 2 → TTS
        Scene 3 → TTS
             ↓
        concatenate
             ↓
        continuous WAV

    Returns:

        (
            combined_audio_path,
            scene_durations
        )
    """

    (
        scene_audio,
        scene_durations,
    ) = generate_scene_audio(
        plan
    )

    if not scene_audio:

        return None, []

    combined_audio = combine_scene_audio(
        scene_audio
    )

    return (
        combined_audio,
        scene_durations,
    )


# ============================================================
# MEDIA DURATION
# ============================================================

def _get_media_duration(
    file_path: str | Path,
) -> float:
    """
    Return media duration using ffprobe.
    """

    command = [
        "ffprobe",
        "-v",
        "error",

        "-show_entries",
        "format=duration",

        "-of",
        "default=noprint_wrappers=1:nokey=1",

        str(file_path),
    ]

    try:

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
        )

        return float(
            result.stdout.strip()
        )

    except Exception as exc:

        print(
            "WARNING: Could not determine "
            f"media duration: {exc}"
        )

        return 0.0


# ============================================================
# AUDIO / VIDEO MERGE
# ============================================================

def merge_audio_video(
    video_file: str,
    audio_file: str,
) -> str:
    """
    Merge synchronized Manim animation
    with generated narration.

    Because the Manim scene durations are already
    based on the measured TTS durations, the video
    and narration should naturally have matching
    lengths.

    The final duration check remains as a safety
    mechanism.
    """

    video = Path(
        video_file
    )

    audio = Path(
        audio_file
    )

    if not video.exists():

        raise FileNotFoundError(
            f"Video not found: {video}"
        )

    if not audio.exists():

        raise FileNotFoundError(
            f"Audio not found: {audio}"
        )

    video_duration = _get_media_duration(
        video
    )

    audio_duration = _get_media_duration(
        audio
    )

    print(
        "\n========== AUDIO / VIDEO CHECK =========="
    )

    print(
        f"Video duration: "
        f"{video_duration:.2f}s"
    )

    print(
        f"Audio duration: "
        f"{audio_duration:.2f}s"
    )

    if video_duration <= 0:

        raise RuntimeError(
            "Could not determine video duration."
        )

    if audio_duration <= 0:

        raise RuntimeError(
            "Generated narration has zero duration."
        )

    difference = (
        video_duration
        - audio_duration
    )

    # ========================================================
    # DURATION CHECK
    # ========================================================

    if abs(difference) <= 0.15:

        print(
            "\nNarration and animation durations "
            "are synchronized."
        )

    elif difference > 0:

        print(
            "\nWARNING: Animation is longer "
            "than narration."
        )

        print(
            f"Animation exceeds narration by "
            f"{difference:.2f}s"
        )

    else:

        print(
            "\nWARNING: Narration is longer "
            "than animation."
        )

        print(
            f"Narration exceeds animation by "
            f"{abs(difference):.2f}s"
        )

    # ========================================================
    # FINAL TARGET
    # ========================================================

    output_duration = min(
        video_duration,
        audio_duration,
    )

    print(
        f"Final target duration: "
        f"{output_duration:.2f}s"
    )

    final_video = (
        MEDIA_DIR
        / (
            "ai_animation_final_"
            f"{uuid.uuid4().hex}.mp4"
        )
    )

    # ========================================================
    # FFMPEG
    # ========================================================

    command = [
        "ffmpeg",
        "-y",

        # ----------------------------------------------------
        # VIDEO
        # ----------------------------------------------------

        "-i",
        str(video),

        # ----------------------------------------------------
        # AUDIO
        # ----------------------------------------------------

        "-i",
        str(audio),

        # ----------------------------------------------------
        # VIDEO STREAM
        # ----------------------------------------------------

        "-map",
        "0:v:0",

        # ----------------------------------------------------
        # AUDIO STREAM
        # ----------------------------------------------------

        "-map",
        "1:a:0",

        # ----------------------------------------------------
        # VIDEO
        # ----------------------------------------------------

        "-c:v",
        "libx264",

        "-preset",
        "veryfast",

        "-pix_fmt",
        "yuv420p",

        # ----------------------------------------------------
        # AUDIO
        # ----------------------------------------------------

        "-c:a",
        "aac",

        "-b:a",
        "128k",

        # ----------------------------------------------------
        # FINAL DURATION
        # ----------------------------------------------------

        "-t",
        f"{output_duration:.3f}",

        # ----------------------------------------------------
        # MP4
        # ----------------------------------------------------

        "-movflags",
        "+faststart",

        str(final_video),
    ]

    print(
        "\n========== MERGING AUDIO + VIDEO =========="
    )

    print(
        "Running FFmpeg..."
    )

    try:

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
        )

    except FileNotFoundError as exc:

        raise RuntimeError(
            "FFmpeg was not found. "
            "Install FFmpeg and make sure "
            "'ffmpeg' is available in PATH."
        ) from exc

    if result.returncode != 0:

        raise RuntimeError(
            "FFmpeg audio/video merge failed:\n\n"
            + (
                result.stderr
                or result.stdout
                or "Unknown FFmpeg error."
            )[-12000:]
        )

    # ========================================================
    # VALIDATE OUTPUT
    # ========================================================

    if not final_video.exists():

        raise RuntimeError(
            "FFmpeg did not create "
            "the final video."
        )

    if final_video.stat().st_size == 0:

        raise RuntimeError(
            "Final video is empty."
        )

    final_duration = _get_media_duration(
        final_video
    )

    print(
        "\n========== FINAL VIDEO =========="
    )

    print(
        "Final video:",
        final_video,
    )

    print(
        f"Final duration: "
        f"{final_duration:.2f}s"
    )

    print(
        f"Original narration: "
        f"{audio_duration:.2f}s"
    )

    return str(
        final_video
    )


# ============================================================
# COMPLETE ANIMATION PIPELINE
# ============================================================

def generate_ai_animation(
    subject: str,
    topic: str,
    grade: str,
    concept: str,
) -> tuple[str, dict]:
    """
    Complete synchronized AI animation pipeline.

    Pipeline:

        1. Generate AI plan
        2. Generate scene-by-scene TTS
        3. Measure each TTS duration
        4. Render Manim using those durations
        5. Combine narration
        6. Merge audio + video

    Returns:

        (
            final_video_path,
            animation_plan
        )
    """

    print("\n")
    print("=" * 60)
    print(
        "       AI ANIMATION GENERATION"
    )
    print("=" * 60)

    # ========================================================
    # STEP 1
    # ========================================================

    print(
        "\n[1/4] Generating animation plan..."
    )

    plan = generate_animation_plan(
        subject=subject,
        topic=topic,
        grade=grade,
        concept=concept,
    )

    if not plan:

        raise RuntimeError(
            "AI failed to generate "
            "an animation plan."
        )

    if not isinstance(
        plan.get("scenes"),
        list,
    ):

        raise RuntimeError(
            "Animation plan does not "
            "contain scenes."
        )

    if not plan["scenes"]:

        raise RuntimeError(
            "Animation plan contains "
            "zero scenes."
        )

    print(
        "Animation plan generated with "
        f"{len(plan['scenes'])} scenes."
    )

    # ========================================================
    # STEP 2
    # ========================================================

    print(
        "\n[2/4] Generating narration audio..."
    )

    (
        audio_file,
        scene_durations,
    ) = generate_narration_audio(
        plan
    )

    if not audio_file:

        raise RuntimeError(
            "Narration could not be generated."
        )

    if not Path(
        audio_file
    ).exists():

        raise RuntimeError(
            "Generated narration file "
            "does not exist: "
            f"{audio_file}"
        )

    if len(scene_durations) != len(
        plan["scenes"]
    ):

        raise RuntimeError(
            "Number of narration durations "
            "does not match number of "
            "animation scenes."
        )

    print(
        "\nNarration generated successfully:"
    )

    print(
        audio_file
    )

    print(
        "\nScene durations:"
    )

    for index, duration in enumerate(
        scene_durations,
        start=1,
    ):

        print(
            f"  Scene {index}: "
            f"{duration:.2f}s"
        )

    # ========================================================
    # STEP 3
    # ========================================================

    print(
        "\n[3/4] Rendering synchronized "
        "Manim animation..."
    )

    video_file = render_animation(
        plan=plan,
        subject=subject,
        topic=topic,
        scene_durations=scene_durations,
    )

    if not video_file:

        raise RuntimeError(
            "Manim did not return "
            "a video file."
        )

    if not Path(
        video_file
    ).exists():

        raise RuntimeError(
            "Rendered video does not exist: "
            f"{video_file}"
        )

    print(
        "\nSynchronized animation "
        "rendered successfully:"
    )

    print(
        video_file
    )

    # ========================================================
    # STEP 4
    # ========================================================

    print(
        "\n[4/4] Merging animation "
        "and narration..."
    )

    try:

        final_video = merge_audio_video(
            video_file=video_file,
            audio_file=audio_file,
        )

    except Exception as exc:

        raise RuntimeError(
            "Failed to merge animation "
            "and narration:\n"
            f"{exc}"
        ) from exc

    if not final_video:

        raise RuntimeError(
            "Audio/video merge returned "
            "no video."
        )

    if not Path(
        final_video
    ).exists():

        raise RuntimeError(
            "Final video does not exist: "
            f"{final_video}"
        )

    # ========================================================
    # COMPLETE
    # ========================================================

    print("\n")
    print("=" * 60)
    print(
        "       ANIMATION GENERATION COMPLETE"
    )
    print("=" * 60)

    print(
        "\nFINAL VIDEO:"
    )

    print(
        final_video
    )

    print(
        "\nSCENES:"
    )

    print(
        len(plan["scenes"])
    )

    print(
        "\nSCENE DURATIONS:"
    )

    for index, duration in enumerate(
        scene_durations,
        start=1,
    ):

        print(
            f"Scene {index}: "
            f"{duration:.2f}s"
        )

    print("=" * 60)

    return (
        final_video,
        plan,
    )


# ============================================================
# MODULE TEST
# ============================================================

if __name__ == "__main__":

    print(
        "animation_service.py "
        "loaded successfully."
    )