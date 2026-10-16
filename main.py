# -*- coding: utf-8 -*-
import logging
from pathlib import Path

import arabic_reshaper
from bidi.algorithm import get_display

from kivy.app import App
from kivy.core.image import Image as CoreImage
from kivy.core.text import Label as CoreLabel
from kivy.core.window import Window
from kivy.graphics import Color, Line, Rectangle, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.properties import ListProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.screenmanager import (
    FadeTransition,
    Screen,
    ScreenManager,
)
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput

from calculations import (
    ISOTOPES,
    boundary_estimate,
    decay,
    number,
)


BASE = Path(__file__).resolve().parent
FONT = str(BASE / "font.ttf")

BRAND = "شرکت رادیوگرافی صنعتی ایران"

BG = (11 / 255, 16 / 255, 35 / 255, 1)
CARD = (21 / 255, 29 / 255, 57 / 255, 1)
BORDER = (43 / 255, 54 / 255, 92 / 255, 1)
ACCENT = (134 / 255, 166 / 255, 255 / 255, 1)
TEXT = (0.95, 0.96, 1, 1)
MUTED = (0.64, 0.69, 0.81, 1)
ERROR = (1, 0.68, 0.67, 1)
RESULT = (0.125, 0.18, 0.34, 1)


def fa(text):
    return get_display(
        arabic_reshaper.reshape(str(text))
    )


class FaLabel(Label):
    def __init__(self, text="", **kwargs):
        self.logical_text = str(text)

        kwargs.setdefault("font_size", sp(13))
        kwargs.setdefault("color", MUTED)
        kwargs.setdefault("halign", "right")
        kwargs.setdefault("size_hint_y", None)

        super().__init__(
            font_name=FONT,
            **kwargs,
        )

        self._measure = CoreLabel(
            font_name=FONT,
            font_size=self.font_size,
        )

        self.bind(
            width=self._wrap,
            texture_size=self._fit,
        )

        self._wrap()

    def set_text(self, text):
        self.logical_text = str(text)
        self._wrap()

    def _wrap(self, *args):
        width = max(
            dp(20),
            self.width - dp(4),
        )

        lines = []

        for paragraph in self.logical_text.split("\n"):
            line = ""

            for word in paragraph.split():
                candidate = (line + " " + word).strip()

                measured_width = self._measure.get_extents(
                    fa(candidate)
                )[0]

                if line and measured_width > width:
                    lines.append(fa(line))
                    line = word
                else:
                    line = candidate

            lines.append(fa(line))

        self.text_size = (width, None)
        self.text = "\n".join(lines)

    def _fit(self, *args):
        self.height = max(
            dp(22),
            self.texture_size[1] + dp(6),
        )


class Card(BoxLayout):
    fill = ListProperty(CARD)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        with self.canvas.before:
            self._color = Color(*self.fill)

            self._rect = RoundedRectangle(
                radius=[dp(13)]
            )

            Color(*BORDER)
            self._line = Line(width=1)

        self.bind(
            pos=self._paint,
            size=self._paint,
            fill=self._paint,
        )

        self._paint()

    def _paint(self, *args):
        self._color.rgba = self.fill
        self._rect.pos = self.pos
        self._rect.size = self.size

        self._line.rounded_rectangle = (
            *self.pos,
            *self.size,
            dp(13),
        )


class BlueButton(Button):
    fill = ListProperty(CARD)

    def __init__(self, text="", **kwargs):
        super().__init__(
            text=fa(text),
            font_name=FONT,
            font_size=sp(13),
            color=MUTED,
            background_normal="",
            background_down="",
            background_color=(0, 0, 0, 0),
            **kwargs,
        )

        with self.canvas.before:
            self._color = Color(*self.fill)

            self._rect = RoundedRectangle(
                radius=[dp(11)]
            )

            Color(*BORDER)
            self._line = Line(width=1)

        self.bind(
            pos=self._paint,
            size=self._paint,
            fill=self._paint,
        )

        self._paint()

    def _paint(self, *args):
        self._color.rgba = self.fill
        self._rect.pos = self.pos
        self._rect.size = self.size

        self._line.rounded_rectangle = (
            *self.pos,
            *self.size,
            dp(11),
        )

    def select(self, active):
        self.fill = ACCENT if active else CARD
        self.color = BG if active else MUTED


class InputCard(Card):
    def __init__(
        self,
        title,
        unit,
        default="",
        **kwargs,
    ):
        super().__init__(
            orientation="vertical",
            padding=dp(10),
            size_hint_y=None,
            height=dp(100),
            **kwargs,
        )

        self.add_widget(
            FaLabel(
                title,
                font_size=sp(12),
            )
        )

        self.input = TextInput(
            text=default,
            multiline=False,
            font_name=FONT,
            font_size=sp(25),
            size_hint_y=None,
            height=dp(38),
            halign="right",
            background_normal="",
            background_active="",
            background_color=(0, 0, 0, 0),
            foreground_color=TEXT,
            cursor_color=ACCENT,
            padding=[0, dp(2)],
            write_tab=False,
            input_type="number",
        )

        self.add_widget(self.input)

        self.add_widget(
            FaLabel(
                unit,
                font_size=sp(10),
                halign="left",
            )
        )


class CalculationScreen(Screen):
    def __init__(self, app, title, **kwargs):
        super().__init__(**kwargs)

        self.app = app
        self.inputs = {}
        self.titles = {}
        self.ready = False

        scroll = ScrollView(
            do_scroll_x=False,
            bar_width=dp(3),
        )

        self.content = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            padding=[dp(16), dp(8)],
            spacing=dp(10),
        )

        self.content.bind(
            minimum_height=self.content.setter("height")
        )

        self.content.add_widget(
            FaLabel(
                title,
                font_size=sp(21),
                color=TEXT,
            )
        )

        self.content.add_widget(
            FaLabel(
                "انتخاب ایزوتوپ",
                font_size=sp(12),
            )
        )

        selectors = GridLayout(
            cols=4,
            spacing=dp(6),
            size_hint_y=None,
            height=dp(36),
        )

        self.iso_buttons = {}

        for source in ISOTOPES:
            button = BlueButton(source)

            button.bind(
                on_release=lambda _, key=source:
                app.set_source(key)
            )

            selectors.add_widget(button)
            self.iso_buttons[source] = button

        self.content.add_widget(selectors)
        scroll.add_widget(self.content)
        self.add_widget(scroll)

        app.bind(
            current_source=self.source_changed
        )

    def field(
        self,
        key,
        title,
        unit,
        default,
        parent=None,
    ):
        card = InputCard(
            title,
            unit,
            default,
        )

        self.inputs[key] = card.input
        self.titles[key] = title

        target = (
            parent
            if parent is not None
            else self.content
        )

        target.add_widget(card)
        card.input.bind(text=self.calc)

    def finish(self, result_title):
        card = Card(
            orientation="vertical",
            padding=dp(12),
            spacing=dp(3),
            size_hint_y=None,
            fill=RESULT,
        )

        card.bind(
            minimum_height=card.setter("height")
        )

        card.add_widget(
            FaLabel(
                result_title,
                color=(0.76, 0.83, 1, 1),
            )
        )

        self.result = FaLabel(
            "—",
            halign="center",
            font_size=sp(31),
            color=TEXT,
        )

        self.details = FaLabel(
            "",
            halign="center",
            font_size=sp(12),
        )

        card.add_widget(self.result)
        card.add_widget(self.details)

        self.content.add_widget(card)

        self.content.add_widget(
            FaLabel(
                "برآورد مدل؛ نه تأیید ایمنی",
                color=ERROR,
                halign="center",
                font_size=sp(12),
            )
        )

        button = BlueButton(
            "درباره محاسبات و محدودیت‌ها",
            size_hint_y=None,
            height=dp(42),
        )

        button.bind(
            on_release=lambda _:
            self.app.switch_tab("info")
        )

        self.content.add_widget(button)

        self.ready = True
        self.source_changed()

    def source_changed(self, *args):
        for key, button in self.iso_buttons.items():
            button.select(
                key == self.app.current_source
            )

        self.calc()

    def value(self, key, positive=False):
        return number(
            self.inputs[key].text,
            self.titles[key],
            positive,
        )

    def calc(self, *args):
        if not self.ready:
            return

        self.result.set_text("—")
        self.details.set_text("")

        try:
            result, details = self.compute()

            self.result.color = TEXT
            self.result.set_text(result)
            self.details.set_text(details)

        except (ValueError, OverflowError) as exc:
            self.result.color = ERROR
            self.result.set_text("—")

            message = (
                str(exc)
                if isinstance(exc, ValueError)
                else "عدد خارج از محدوده محاسبه است"
            )

            self.details.set_text(message)

        except Exception:
            logging.exception(
                "Calculation failed on %s",
                self.name,
            )

            self.result.color = ERROR

            self.details.set_text(
                "خطای داخلی؛ گزارش برنامه را بررسی کنید"
            )


class SafetyScreen(CalculationScreen):
    def __init__(self, app, **kwargs):
        super().__init__(
            app,
            "مرزبندی و حفاظ",
            **kwargs,
        )

        row = BoxLayout(
            spacing=dp(10),
            size_hint_y=None,
            height=dp(100),
        )

        self.content.add_widget(row)

        self.field(
            "activity",
            "اکتیویته",
            "Ci",
            "40",
            row,
        )

        self.field(
            "dose",
            "نرخ دوز هدف طبق طرح مصوب",
            "µSv/h",
            "",
            row,
        )

        self.field(
            "shield",
            "ضخامت سرب در مسیر پرتو",
            "mm",
            "0",
        )

        self.finish(
            "فاصله برآوردی مدل"
        )

    def compute(self):
        distance, transmission = boundary_estimate(
            self.app.current_source,
            self.value("activity"),
            self.value("dose", True),
            self.value("shield"),
        )

        return (
            f"{distance:.4g} متر",
            f"ضریب عبور سرب: {transmission:.4g}",
        )


class DecayScreen(CalculationScreen):
    def __init__(self, app, **kwargs):
        super().__init__(
            app,
            "واپاشی چشمه",
            **kwargs,
        )

        self.field(
            "initial",
            "اکتیویته اولیه",
            "Ci",
            "80",
        )

        self.field(
            "days",
            "روزهای سپری‌شده",
            "روز",
            "30",
        )

        self.finish(
            "اکتیویته پس از واپاشی"
        )

    def compute(self):
        initial = self.value("initial")

        activity, percent = decay(
            self.app.current_source,
            initial,
            self.value("days"),
        )

        if initial:
            details = (
                "کاهش نسبت به مقدار اولیه: "
                f"{percent:.2f}٪"
            )
        else:
            details = (
                "برای اکتیویته اولیه صفر، "
                "درصد کاهش تعریف نمی‌شود."
            )

        return (
            f"{activity:.6g} Ci",
            details,
        )


class InfoScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        scroll = ScrollView(
            do_scroll_x=False
        )

        content = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            padding=dp(16),
            spacing=dp(12),
        )

        content.bind(
            minimum_height=content.setter("height")
        )

        content.add_widget(
            FaLabel(
                "اطلاعات و محدودیت‌ها",
                font_size=sp(21),
                color=TEXT,
            )
        )

        paragraphs = [
            (
                "نتایج این برنامه صرفاً برآورد هستند؛ "
                "تأیید ایمنی، طراحی حفاظ یا تعیین محل "
                "مجاز اپراتور نیستند. مرزبندی عملی باید "
                "طبق طرح مصوب و با نظر مسئول حفاظت "
                "پرتویی و اندازه‌گیری در محل انجام شود."
            ),
            (
                "داده‌های ایزوتوپ از کد اولیه منتقل "
                "شده‌اند و مستقلاً تأیید نشده‌اند. "
                "نیمه‌عمر و اکتیویته باید با گواهی چشمه "
                "و منابع معتبر تطبیق داده شوند."
            ),
            (
                "مدل گاما، چشمه نقطه‌ای و قانون عکس "
                "مجذور فاصله با HVL ثابت سرب را فرض "
                "می‌کند. پراکندگی، buildup، نشتی و "
                "هندسه واقعی لحاظ نمی‌شوند. تبدیل "
                "R/h به µSv/h با ضریب تقریبی ۱۰۰۰۰ "
                "از کد اولیه حفظ شده است."
            ),
            (
                "ضخامت بدنه کولیماتور برای دهانه خروجی "
                "پرتو قابل استفاده نیست. نرخ دوز هدف "
                "باید از طرح مصوب گرفته شود. نتیجه "
                "باید با دستگاه مناسب و کالیبره "
                "بررسی شود."
            ),
            (
                "واپاشی بر حسب تعداد روز واردشده "
                "محاسبه می‌شود؛ تاریخ امروز یا تاریخ "
                "گواهی خودکار محاسبه نمی‌شود. اکتیویته "
                "صفر صرفاً نتیجه عددی است، نه اعلام ایمنی."
            ),
        ]

        for paragraph in paragraphs:
            card = Card(
                orientation="vertical",
                size_hint_y=None,
                padding=dp(12),
            )

            card.bind(
                minimum_height=card.setter("height")
            )

            card.add_widget(
                FaLabel(
                    paragraph,
                    color=TEXT,
                )
            )

            content.add_widget(card)

        for key, data in ISOTOPES.items():
            card = Card(
                orientation="vertical",
                size_hint_y=None,
                padding=dp(12),
            )

            card.bind(
                minimum_height=card.setter("height")
            )

            texts = (
                f"{data['name']} ({key})",
                (
                    f"نیمه‌عمر: {data['half_life']} روز"
                    f" | انرژی درج‌شده: {data['energy']}"
                ),
                (
                    f"ثابت گامای ورودی: {data['gamma']}"
                    " R·m²/(Ci·h)"
                ),
                (
                    f"HVL سرب: {data['hvl_pb']} mm"
                    f" | فولاد: {data['hvl_fe']} mm"
                ),
            )

            for text in texts:
                card.add_widget(
                    FaLabel(text)
                )

            content.add_widget(card)

        scroll.add_widget(content)
        self.add_widget(scroll)


class PendingScreen(Screen):
    def __init__(self, title, **kwargs):
        super().__init__(**kwargs)

        content = BoxLayout(
            orientation="vertical",
            padding=dp(20),
            spacing=dp(16),
        )

        content.add_widget(
            FaLabel(
                title,
                font_size=sp(22),
                color=TEXT,
            )
        )

        content.add_widget(
            FaLabel(
                "این بخش هنوز محاسبه ندارد.\n"
                "پس از مشخص‌شدن مدل و داده‌های معتبر "
                "اضافه می‌شود.",
                color=MUTED,
                font_size=sp(15),
            )
        )

        content.add_widget(Label())
        self.add_widget(content)


class NDTMainApp(App):
    current_source = StringProperty("Ir-192")

    def build(self):
        self.title = BRAND

        Window.clearcolor = BG
        Window.softinput_mode = "below_target"
        Window.bind(on_keyboard=self.on_keyboard)

        self.outer = ScreenManager(
            transition=FadeTransition(
                duration=0.2
            )
        )

        self._background_texture = CoreImage(
            str(BASE / "bg.png")
        ).texture

        with self.outer.canvas.before:
            Color(1, 1, 1, 1)

            self._background = Rectangle(
                texture=self._background_texture,
                pos=self.outer.pos,
                size=self.outer.size,
            )

        self.outer.bind(
            pos=self._paint_background,
            size=self._paint_background,
        )

        home = Screen(name="home")

        root = BoxLayout(
            orientation="vertical",
            padding=[dp(8), dp(8)],
            spacing=dp(6),
        )

        header = Card(
            size_hint_y=None,
            height=dp(72),
            padding=dp(10),
            spacing=dp(10),
        )

        header.add_widget(
            Image(
                source=str(BASE / "logo.png"),
                size_hint_x=None,
                width=dp(56),
            )
        )

        header.add_widget(
            FaLabel(
                BRAND,
                color=TEXT,
                font_size=sp(14),
                pos_hint={"center_y": 0.5},
            )
        )

        root.add_widget(header)

        self.sm = ScreenManager(
            transition=FadeTransition(
                duration=0.12
            )
        )

        self.sm.add_widget(
            SafetyScreen(
                self,
                name="safety",
            )
        )

        self.sm.add_widget(
            DecayScreen(
                self,
                name="decay",
            )
        )

        self.sm.add_widget(
            InfoScreen(
                name="info"
            )
        )

        self.sm.add_widget(
            PendingScreen(
                "محاسبات ایکس‌ری",
                name="xray",
            )
        )

        self.sm.add_widget(
            PendingScreen(
                "زمان پرتودهی",
                name="exposure",
            )
        )

        root.add_widget(self.sm)

        nav = Card(
            size_hint_y=None,
            height=dp(54),
            padding=dp(5),
            spacing=dp(5),
        )

        self.nav_buttons = {}

        tabs = (
            ("مرزبندی", "safety"),
            ("ایکس‌ری", "xray"),
            ("واپاشی", "decay"),
            ("پرتودهی", "exposure"),
            ("اطلاعات", "info"),
        )

        for label, name in tabs:
            button = BlueButton(label)

            button.bind(
                on_release=lambda _, target=name:
                self.switch_tab(target)
            )

            self.nav_buttons[name] = button
            nav.add_widget(button)

        root.add_widget(nav)
        home.add_widget(root)
        self.outer.add_widget(home)

        self.switch_tab("safety")

        return self.outer

    def _paint_background(self, *args):
        self._background.pos = self.outer.pos
        self._background.size = self.outer.size

    def set_source(self, name):
        if name in ISOTOPES:
            self.current_source = name

    def switch_tab(self, name):
        self.sm.current = name

        for key, button in self.nav_buttons.items():
            button.select(
                key == name
            )

    def on_keyboard(self, window, key, *args):
        if (
            key == 27
            and self.outer.current == "home"
            and self.sm.current != "safety"
        ):
            self.switch_tab("safety")
            return True

        return False

    def on_pause(self):
        return True


if __name__ == "__main__":
    NDTMainApp().run()
