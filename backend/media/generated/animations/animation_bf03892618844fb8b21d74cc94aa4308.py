
from manim import *


class AIAnimatedLesson(Scene):

    def construct(self):

        subject = Text(
            "Physics",
            font_size=28
        )

        topic = Text(
            "Simple Harmonic Motion",
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

        self.wait(2)

        self.play(
            FadeOut(header)
        )


        # ==================================================
        # AI GENERATED SCENE 1
        # ==================================================

        scene_title = Text(
            "The Setup: Equilibrium and Displacement",
            font_size=32
        )

        scene_description = Text(
            "Introduces a mass attached to a vertical spring. Shows the equilibrium position clearly. The mass is pulled down to a maximum displacement (amplitude) and released. Arrows indicate the direction of the initial force and the restoring force acting upwards.",
            font_size=18
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
            buff=0.25
        )

        scene_type = Text(
            "AI animation type: diagram",
            font_size=16
        )

        scene_type.to_edge(
            DOWN
        )

        self.play(
            Write(scene_title),
            FadeIn(scene_description),
            FadeIn(scene_type)
        )


        concept_box = RoundedRectangle(
            width=6,
            height=3
        )

        self.play(
            Create(concept_box)
        )

        self.play(
            concept_box.animate.scale(1.15),
            run_time=4
        )

        self.play(
            concept_box.animate.scale(1 / 1.15),
            run_time=4
        )


        self.play(
            FadeOut(
                VGroup(
                    scene_title,
                    scene_description,
                    scene_type
                )
            )
        )

        # ==================================================
        # AI GENERATED SCENE 2
        # ==================================================

        scene_title = Text(
            "The Oscillation Cycle",
            font_size=32
        )

        scene_description = Text(
            "The mass moves up and down in a continuous cycle. A ghost trail or motion blur effect is used to visualize the speed: the mass moves fastest at the equilibrium point and slows down to a stop at the extremes. This highlights the non-linear nature of the velocity.",
            font_size=18
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
            buff=0.25
        )

        scene_type = Text(
            "AI animation type: motion",
            font_size=16
        )

        scene_type.to_edge(
            DOWN
        )

        self.play(
            Write(scene_title),
            FadeIn(scene_description),
            FadeIn(scene_type)
        )


        moving_object = Circle(
            radius=0.5
        )

        path = Line(
            LEFT * 3,
            RIGHT * 3
        )

        self.play(
            Create(path),
            FadeIn(moving_object)
        )

        self.play(
            MoveAlongPath(
                moving_object,
                path
            ),
            run_time=10
        )


        self.play(
            FadeOut(
                VGroup(
                    scene_title,
                    scene_description,
                    scene_type
                )
            )
        )

        # ==================================================
        # AI GENERATED SCENE 3
        # ==================================================

        scene_title = Text(
            "Position vs. Time Graph",
            font_size=32
        )

        scene_description = Text(
            "A coordinate system appears next to the spring. As the mass oscillates, a point traces a sine wave on the graph. The animation synchronizes the vertical position of the mass with the y-value of the graph, visually linking the physical motion to the mathematical function y(t) = A cos(ωt).",
            font_size=18
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
            buff=0.25
        )

        scene_type = Text(
            "AI animation type: graph",
            font_size=16
        )

        scene_type.to_edge(
            DOWN
        )

        self.play(
            Write(scene_title),
            FadeIn(scene_description),
            FadeIn(scene_type)
        )


        axes = Axes(
            x_range=[-5, 5, 1],
            y_range=[-2, 2, 1],
            x_length=8,
            y_length=4
        )

        graph = axes.plot(
            lambda x: __import__("math").sin(x),
            color=BLUE
        )

        self.play(
            Create(axes)
        )

        self.play(
            Create(graph),
            run_time=12
        )


        self.play(
            FadeOut(
                VGroup(
                    scene_title,
                    scene_description,
                    scene_type
                )
            )
        )

        # ==================================================
        # AI GENERATED SCENE 4
        # ==================================================

        scene_title = Text(
            "Restoring Force and Acceleration",
            font_size=32
        )

        scene_description = Text(
            "Vectors are overlaid on the mass. A red arrow represents the restoring force (F = -kx) and a blue arrow represents acceleration. The animation shows that the force and acceleration are always directed towards the equilibrium position and are largest at the maximum displacement, but zero at the center.",
            font_size=18
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
            buff=0.25
        )

        scene_type = Text(
            "AI animation type: simulation",
            font_size=16
        )

        scene_type.to_edge(
            DOWN
        )

        self.play(
            Write(scene_title),
            FadeIn(scene_description),
            FadeIn(scene_type)
        )


        particle = Dot()

        circle = Circle(
            radius=2
        )

        self.play(
            Create(circle),
            FadeIn(particle)
        )

        self.play(
            MoveAlongPath(
                particle,
                circle
            ),
            run_time=10
        )


        self.play(
            FadeOut(
                VGroup(
                    scene_title,
                    scene_description,
                    scene_type
                )
            )
        )

        # ==================================================
        # AI GENERATED SCENE 5
        # ==================================================

        scene_title = Text(
            "Energy Transformation",
            font_size=32
        )

        scene_description = Text(
            "Two energy bars appear: Elastic Potential Energy (PE) and Kinetic Energy (KE). As the mass moves from the bottom to the top, the PE bar decreases while the KE bar increases, and vice versa. The total height of the combined bars remains constant, demonstrating the conservation of mechanical energy.",
            font_size=18
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
            buff=0.25
        )

        scene_type = Text(
            "AI animation type: process",
            font_size=16
        )

        scene_type.to_edge(
            DOWN
        )

        self.play(
            Write(scene_title),
            FadeIn(scene_description),
            FadeIn(scene_type)
        )


        box1 = RoundedRectangle(
            width=2.4,
            height=1.2
        )

        box2 = RoundedRectangle(
            width=2.4,
            height=1.2
        )

        arrow = Arrow(
            LEFT,
            RIGHT
        )

        group = VGroup(
            box1,
            arrow,
            box2
        ).arrange(
            RIGHT,
            buff=0.5
        )

        self.play(
            Create(group)
        )

        self.play(
            box1.animate.shift(UP * 0.5),
            run_time=6
        )

        self.play(
            box1.animate.shift(DOWN * 0.5),
            run_time=6
        )


        self.play(
            FadeOut(
                VGroup(
                    scene_title,
                    scene_description,
                    scene_type
                )
            )
        )

