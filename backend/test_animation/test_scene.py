from manim import *

class TestScene(Scene):
    def construct(self):
        title = Text("AI Animated Learning", font_size=48)
        circle = Circle(radius=1.2)
        arrow = Arrow(LEFT, RIGHT)

        self.play(Write(title))
        self.play(title.animate.to_edge(UP))
        self.play(Create(circle))
        self.play(Create(arrow))
        self.play(circle.animate.shift(RIGHT * 2))
        self.wait(2)
