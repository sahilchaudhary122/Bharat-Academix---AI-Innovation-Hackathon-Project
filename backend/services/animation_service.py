import json
import os
import re
import subprocess
import uuid
from pathlib import Path

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

MEDIA_DIR.mkdir(
    parents=True,
    exist_ok=True
)

ANIMATION_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# AI ANIMATION PLANNER
# ============================================================

def generate_animation_plan(
    subject: str,
    topic: str,
    grade: str,
    concept: str,
) -> dict:

    prompt = f"""
You are an expert educational animation director.

Create a visual animation plan for:

Subject: {subject}
Topic: {topic}
Grade: {grade}
Concept: {concept}

The animation will be rendered programmatically using Manim.

The animation must genuinely explain the user's topic.

IMPORTANT:

- The topic is dynamic.
- Do NOT assume Simple Harmonic Motion.
- Do NOT use a fixed animation.
- Select visual objects based on the actual topic.
- Select actions based on the actual topic.
- Use movement whenever movement helps explain the concept.
- Use diagrams, graphs, formulas, arrows, particles,
  processes, simulations or transformations when appropriate.
- Use 3 to 6 scenes.
- Every scene must teach one clear idea.
- Avoid unrelated decorative objects.

Possible object types:

spring
mass
ball
earth
object
arrow
axis
graph
wave
particle
circle
rectangle
triangle
line
circuit
battery
resistor
array
tree
leaf
molecule
atom
text

Possible actions:

appear
disappear
move
move_up
move_down
move_left
move_right
oscillate
rotate
draw
transform
grow
shrink
trace
bounce
highlight
connect

These are examples only.

Choose objects and actions according to the actual topic.

Return ONLY valid JSON.

Format:

{{
    "title": "...",
    "summary": "...",
    "scenes": [
        {{
            "title": "...",
            "description": "...",
            "animation_type": "...",
            "duration": 8,

            "objects": [
                {{
                    "type": "...",
                    "name": "...",
                    "label": "..."
                }}
            ],

            "actions": [
                {{
                    "target": "...",
                    "action": "...",
                    "duration": 4
                }}
            ],

            "labels": [
                "..."
            ],

            "formula": "..."
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
                    "You are an educational animation planner. "
                    "Return only valid JSON."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.4,
        max_tokens=4000,
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
        flags=re.IGNORECASE,
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
            "Groq returned invalid JSON:\n" + text
        ) from exc

    if not isinstance(plan, dict):
        raise RuntimeError(
            "Animation plan must be a JSON object."
        )

    if not isinstance(
        plan.get("scenes"),
        list
    ):
        raise RuntimeError(
            "Animation plan does not contain scenes."
        )

    if not plan["scenes"]:
        raise RuntimeError(
            "Groq returned zero scenes."
        )

    return plan


# ============================================================
# PYTHON STRING ESCAPING
# ============================================================

def _py(value: str) -> str:

    return (
        str(value)
        .replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", " ")
    )


# ============================================================
# MANIM VISUAL BUILDERS
# ============================================================

def _build_object_code(
    obj: dict,
    index: int,
) -> str:

    obj_type = str(
        obj.get("type", "circle")
    ).lower()

    name = re.sub(
        r"[^a-zA-Z0-9_]",
        "_",
        str(
            obj.get(
                "name",
                f"object_{index}"
            )
        )
    )

    label = _py(
        obj.get(
            "label",
            name
        )
    )

    # --------------------------------------------------------
    # SPRING
    # --------------------------------------------------------

    if obj_type == "spring":

        return f"""
        {name}_start = UP * 2.3
        {name}_end = DOWN * 0.5

        {name} = VMobject()

        {name}.set_points_as_corners([
            {name}_start,
            {name}_start + DOWN * 0.25 + RIGHT * 0.22,
            {name}_start + DOWN * 0.50 + LEFT * 0.22,
            {name}_start + DOWN * 0.75 + RIGHT * 0.22,
            {name}_start + DOWN * 1.00 + LEFT * 0.22,
            {name}_start + DOWN * 1.25 + RIGHT * 0.22,
            {name}_start + DOWN * 1.50 + LEFT * 0.22,
            {name}_start + DOWN * 1.75 + RIGHT * 0.22,
            {name}_end
        ])

        {name}_label = Text(
            "{label}",
            font_size=20
        )

        {name}_label.next_to(
            {name},
            RIGHT,
            buff=0.25
        )
"""

    # --------------------------------------------------------
    # MASS / BALL / OBJECT
    # --------------------------------------------------------

    if obj_type in {
        "mass",
        "ball",
        "particle",
        "object",
    }:

        return f"""
        {name} = Circle(
            radius=0.42,
            fill_opacity=1
        )

        {name}_label = Text(
            "{label}",
            font_size=20
        )

        {name}_label.next_to(
            {name},
            RIGHT,
            buff=0.25
        )
"""

    # --------------------------------------------------------
    # EARTH
    # --------------------------------------------------------

    if obj_type == "earth":

        return f"""
        {name} = Circle(
            radius=1.25,
            fill_opacity=1
        )

        {name}_label = Text(
            "{label}",
            font_size=22
        )

        {name}_label.move_to(
            {name}.get_center()
        )
"""

    # --------------------------------------------------------
    # ARROW
    # --------------------------------------------------------

    if obj_type == "arrow":

        return f"""
        {name} = Arrow(
            LEFT * 1.2,
            RIGHT * 1.2
        )

        {name}_label = Text(
            "{label}",
            font_size=20
        )

        {name}_label.next_to(
            {name},
            UP,
            buff=0.15
        )
"""

    # --------------------------------------------------------
    # AXIS
    # --------------------------------------------------------

    if obj_type == "axis":

        return f"""
        {name} = Line(
            LEFT * 4,
            RIGHT * 4
        )

        {name}_label = Text(
            "{label}",
            font_size=20
        )

        {name}_label.next_to(
            {name},
            DOWN,
            buff=0.2
        )
"""

    # --------------------------------------------------------
    # WAVE / GRAPH
    # --------------------------------------------------------

    if obj_type in {
        "wave",
        "graph",
    }:

        return f"""
        {name}_axes = Axes(
            x_range=[-6, 6, 1],
            y_range=[-2.5, 2.5, 1],
            x_length=9,
            y_length=4.5
        )

        {name} = {name}_axes.plot(
            lambda x: __import__("math").sin(x),
        )

        {name}_label = Text(
            "{label}",
            font_size=20
        )

        {name}_label.next_to(
            {name}_axes,
            UP,
            buff=0.2
        )
"""

    # --------------------------------------------------------
    # TRIANGLE
    # --------------------------------------------------------

    if obj_type == "triangle":

        return f"""
        {name} = Triangle()

        {name}_label = Text(
            "{label}",
            font_size=20
        )

        {name}_label.next_to(
            {name},
            DOWN,
            buff=0.2
        )
"""

    # --------------------------------------------------------
    # RECTANGLE / BOX
    # --------------------------------------------------------

    if obj_type in {
        "rectangle",
        "box",
    }:

        return f"""
        {name} = RoundedRectangle(
            width=2.4,
            height=1.4
        )

        {name}_label = Text(
            "{label}",
            font_size=20
        )

        {name}_label.move_to(
            {name}.get_center()
        )
"""

    # --------------------------------------------------------
    # LINE
    # --------------------------------------------------------

    if obj_type == "line":

        return f"""
        {name} = Line(
            LEFT * 3,
            RIGHT * 3
        )

        {name}_label = Text(
            "{label}",
            font_size=18
        )

        {name}_label.next_to(
            {name},
            UP,
            buff=0.15
        )
"""

    # --------------------------------------------------------
    # DEFAULT
    # --------------------------------------------------------

    return f"""
        {name} = Circle(
            radius=0.45
        )

        {name}_label = Text(
            "{label}",
            font_size=18
        )

        {name}_label.next_to(
            {name},
            RIGHT,
            buff=0.2
        )
"""


# ============================================================
# ACTION CODE
# ============================================================

def _build_action_code(
    action: dict,
) -> str:

    target = re.sub(
        r"[^a-zA-Z0-9_]",
        "_",
        str(
            action.get(
                "target",
                ""
            )
        )
    )

    action_name = str(
        action.get(
            "action",
            "appear"
        )
    ).lower()

    try:
        duration = float(
            action.get(
                "duration",
                2
            )
        )
    except (TypeError, ValueError):
        duration = 2

    duration = max(
        0.5,
        min(duration, 15)
    )

    # --------------------------------------------------------
    # APPEAR
    # --------------------------------------------------------

    if action_name == "appear":

        return f"""
        if "{target}" in objects:
            self.play(
                FadeIn(objects["{target}"]),
                run_time={duration}
            )
"""

    # --------------------------------------------------------
    # DISAPPEAR
    # --------------------------------------------------------

    if action_name == "disappear":

        return f"""
        if "{target}" in objects:
            self.play(
                FadeOut(objects["{target}"]),
                run_time={duration}
            )
"""

    # --------------------------------------------------------
    # MOVE UP
    # --------------------------------------------------------

    if action_name == "move_up":

        return f"""
        if "{target}" in objects:
            self.play(
                objects["{target}"].animate.shift(UP * 2),
                run_time={duration}
            )
"""

    # --------------------------------------------------------
    # MOVE DOWN
    # --------------------------------------------------------

    if action_name == "move_down":

        return f"""
        if "{target}" in objects:
            self.play(
                objects["{target}"].animate.shift(DOWN * 2),
                run_time={duration}
            )
"""

    # --------------------------------------------------------
    # MOVE LEFT
    # --------------------------------------------------------

    if action_name == "move_left":

        return f"""
        if "{target}" in objects:
            self.play(
                objects["{target}"].animate.shift(LEFT * 2),
                run_time={duration}
            )
"""

    # --------------------------------------------------------
    # MOVE RIGHT
    # --------------------------------------------------------

    if action_name == "move_right":

        return f"""
        if "{target}" in objects:
            self.play(
                objects["{target}"].animate.shift(RIGHT * 2),
                run_time={duration}
            )
"""

    # --------------------------------------------------------
    # OSCILLATE
    # --------------------------------------------------------

    if action_name == "oscillate":

        return f"""
        if "{target}" in objects:

            self.play(
                objects["{target}"].animate.shift(
                    DOWN * 1.5
                ),
                run_time={duration / 4}
            )

            self.play(
                objects["{target}"].animate.shift(
                    UP * 3
                ),
                run_time={duration / 2}
            )

            self.play(
                objects["{target}"].animate.shift(
                    DOWN * 1.5
                ),
                run_time={duration / 4}
            )
"""

    # --------------------------------------------------------
    # ROTATE
    # --------------------------------------------------------

    if action_name == "rotate":

        return f"""
        if "{target}" in objects:
            self.play(
                Rotate(
                    objects["{target}"],
                    angle=TAU
                ),
                run_time={duration}
            )
"""

    # --------------------------------------------------------
    # GROW
    # --------------------------------------------------------

    if action_name == "grow":

        return f"""
        if "{target}" in objects:
            self.play(
                objects["{target}"].animate.scale(1.4),
                run_time={duration}
            )
"""

    # --------------------------------------------------------
    # SHRINK
    # --------------------------------------------------------

    if action_name == "shrink":

        return f"""
        if "{target}" in objects:
            self.play(
                objects["{target}"].animate.scale(0.7),
                run_time={duration}
            )
"""

    # --------------------------------------------------------
    # DRAW / TRACE
    # --------------------------------------------------------

    if action_name in {
        "draw",
        "trace",
    }:

        return f"""
        if "{target}" in objects:
            self.play(
                Create(objects["{target}"]),
                run_time={duration}
            )
"""

    # --------------------------------------------------------
    # HIGHLIGHT
    # --------------------------------------------------------

    if action_name == "highlight":

        return f"""
        if "{target}" in objects:

            self.play(
                Indicate(
                    objects["{target}"]
                ),
                run_time={duration}
            )
"""

    # --------------------------------------------------------
    # BOUNCE
    # --------------------------------------------------------

    if action_name == "bounce":

        return f"""
        if "{target}" in objects:

            self.play(
                objects["{target}"].animate.shift(
                    UP * 1.5
                ),
                run_time={duration / 2}
            )

            self.play(
                objects["{target}"].animate.shift(
                    DOWN * 1.5
                ),
                run_time={duration / 2}
            )
"""

    # --------------------------------------------------------
    # CONNECT
    # --------------------------------------------------------

    if action_name == "connect":

        return """
        self.wait(1)
"""

    # --------------------------------------------------------
    # DEFAULT
    # --------------------------------------------------------

    return f"""
        if "{target}" in objects:
            self.play(
                Indicate(objects["{target}"]),
                run_time={duration}
            )
"""


# ============================================================
# MANIM SCRIPT GENERATOR
# ============================================================

def create_manim_script(
    plan: dict,
    subject: str,
    topic: str,
) -> Path:

    safe_subject = _py(subject)

    safe_topic = _py(topic)

    scene_code = []

    for scene_index, scene in enumerate(
        plan["scenes"]
    ):

        title = _py(
            scene.get(
                "title",
                f"Scene {scene_index + 1}"
            )
        )

        description = _py(
            scene.get(
                "description",
                ""
            )
        )

        formula = scene.get(
            "formula"
        )

        objects = scene.get(
            "objects",
            []
        )

        actions = scene.get(
            "actions",
            []
        )

        object_code = []

        for object_index, obj in enumerate(
            objects
        ):

            object_code.append(
                _build_object_code(
                    obj,
                    object_index
                )
            )

        action_code = []

        for action in actions:

            action_code.append(
                _build_action_code(
                    action
                )
            )

        formula_code = ""

        if formula:

            safe_formula = _py(
                formula
            )

            formula_code = f"""
        formula = Text(
            "{safe_formula}",
            font_size=28
        )

        formula.to_edge(
            DOWN
        )

        self.play(
            Write(formula)
        )

        self.wait(1)
"""

        scene_block = f"""

        # ==================================================
        # AI GENERATED SCENE {scene_index + 1}
        # ==================================================

        scene_title = Text(
            "{title}",
            font_size=30
        )

        scene_description = Text(
            "{description}",
            font_size=17
        )

        scene_description.scale_to_fit_width(
            11
        )

        scene_title.to_edge(
            UP
        )

        scene_description.next_to(
            scene_title,
            DOWN,
            buff=0.2
        )

        self.play(
            Write(scene_title),
            FadeIn(scene_description)
        )

        objects = {{}}

{''.join(object_code)}

"""

        # Register all generated objects.
        for obj in objects:

            name = re.sub(
                r"[^a-zA-Z0-9_]",
                "_",
                str(
                    obj.get(
                        "name",
                        ""
                    )
                )
            )

            if name:

                scene_block += f"""
        objects["{name}"] = {name}
"""

        scene_block += f"""

        # Arrange scene objects.
        visual_objects = [
            value
            for key, value in objects.items()
        ]

        if visual_objects:

            group = VGroup(
                *visual_objects
            )

            group.scale_to_fit_width(
                10
            )

            group.move_to(
                ORIGIN
            )

            self.play(
                FadeIn(group)
            )

{''.join(action_code)}

{formula_code}

        self.wait(1)

        self.play(
            FadeOut(
                scene_title,
                scene_description,
                *[
                    value
                    for value in objects.values()
                ]
            )
        )
"""

        scene_code.append(
            scene_block
        )

    script = f'''
from manim import *


class AIAnimatedLesson(Scene):

    def construct(self):

        subject = Text(
            "{safe_subject}",
            font_size=28
        )

        topic = Text(
            "{safe_topic}",
            font_size=42
        )

        header = VGroup(
            subject,
            topic
        ).arrange(
            DOWN,
            buff=0.25
        )

        self.play(
            Write(subject),
            Write(topic)
        )

        self.wait(1)

        self.play(
            FadeOut(header)
        )

{"".join(scene_code)}
'''

    filename = (
        f"animation_{uuid.uuid4().hex}.py"
    )

    script_path = (
        ANIMATION_DIR
        / filename
    )

    script_path.write_text(
        script,
        encoding="utf-8"
    )

    return script_path


# ============================================================
# RENDER ANIMATION
# ============================================================

def render_animation(
    plan: dict,
    subject: str,
    topic: str,
) -> str:

    script_path = create_manim_script(
        plan=plan,
        subject=subject,
        topic=topic,
    )

    render_dir = (
        ANIMATION_DIR
        / "manim_media"
    )

    render_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    command = [
        "manim",
        "-ql",
        "--media_dir",
        str(render_dir),
        str(script_path),
        "AIAnimatedLesson",
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:

        raise RuntimeError(
            "Manim rendering failed:\n\n"
            + result.stderr[-10000:]
        )

    candidates = list(
        render_dir.rglob(
            "AIAnimatedLesson.mp4"
        )
    )

    if not candidates:

        raise FileNotFoundError(
            "Manim completed but no MP4 was found."
        )

    source_video = candidates[-1]

    final_name = (
        f"ai_animation_{uuid.uuid4().hex}.mp4"
    )

    final_video = (
        MEDIA_DIR
        / final_name
    )

    source_video.replace(
        final_video
    )

    return str(final_video)


# ============================================================
# COMPLETE AI ANIMATION PIPELINE
# ============================================================

def generate_ai_animation(
    subject: str,
    topic: str,
    grade: str,
    concept: str,
) -> tuple[str, dict]:

    plan = generate_animation_plan(
        subject=subject,
        topic=topic,
        grade=grade,
        concept=concept,
    )

    video_file = render_animation(
        plan=plan,
        subject=subject,
        topic=topic,
    )

    return (
        video_file,
        plan,
    )
