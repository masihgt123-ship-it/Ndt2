# -*- coding: utf-8 -*-
"""Ndt2: minimal Android startup test."""

from kivy.app import App
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label


class NDTApp(App):
    def build(self):
        self.title = 'شرکت رادیوگرافی صنعتی ایران'
        self.seconds = 0
        self.taps = 0

        root = BoxLayout(
            orientation='vertical',
            padding=dp(24),
            spacing=dp(20),
        )

        with root.canvas.before:
            Color(0.043, 0.063, 0.137, 1)
            self.background = Rectangle(
                pos=root.pos,
                size=root.size,
            )

        root.bind(
            pos=self.update_background,
            size=self.update_background,
        )

        root.add_widget(Label(
            text='IRAN INDUSTRIAL RADIOGRAPHY',
            font_size='18sp',
            color=(0.75, 0.83, 1, 1),
        ))

        self.status = Label(
            text='NDT2\nStartup test\nRunning: 0 seconds',
            font_size='24sp',
            halign='center',
            color=(1, 1, 1, 1),
        )
        root.add_widget(self.status)

        self.test_button = Button(
            text='Test button: 0',
            size_hint_y=None,
            height=dp(56),
            font_size='20sp',
            background_normal='',
            background_color=(0.20, 0.36, 0.70, 1),
        )
        self.test_button.bind(on_release=self.test_tap)
        root.add_widget(self.test_button)

        return root

    def on_start(self):
        self.timer = Clock.schedule_interval(
            self.update_status, 1
        )

    def update_background(self, widget, *args):
        self.background.pos = widget.pos
        self.background.size = widget.size

    def update_status(self, dt):
        self.seconds += 1
        self.status.text = (
            'NDT2\nStartup test\n'
            f'Running: {self.seconds} seconds'
        )

    def test_tap(self, button):
        self.taps += 1
        button.text = f'Test button: {self.taps}'

    def on_pause(self):
        return True

    def on_stop(self):
        if hasattr(self, 'timer'):
            self.timer.cancel()


if __name__ == '__main__':
    NDTApp().run()
