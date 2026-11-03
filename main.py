# -*- coding: utf-8 -*-
"""ИТОГ — офлайн-тренажёр итогового сочинения. Android / Kivy."""
from __future__ import annotations

import random
import threading
from datetime import datetime
from pathlib import Path

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.progressbar import ProgressBar
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget

from coach import EssayCoach
from criteria import basic_audit, count_words
from library import LiteratureLibrary
from storage import AppStorage
from themes import ThemeBank

BG = (0.055, 0.070, 0.105, 1)
PANEL = (0.105, 0.13, 0.19, 1)
PANEL2 = (0.13, 0.16, 0.23, 1)
ACCENT = (0.48, 0.40, 0.95, 1)
TEXT = (0.93, 0.94, 0.98, 1)
MUTED = (0.66, 0.70, 0.78, 1)
GOOD = (0.25, 0.75, 0.55, 1)
WARN = (0.98, 0.68, 0.28, 1)


def make_label(text: str, size: int = 15, color=TEXT, height=None, bold=False, halign="left"):
    min_height = dp(height or max(42, size * 2.0))
    widget = Label(
        text=text,
        color=color,
        font_size=sp(size),
        bold=bold,
        halign=halign,
        valign="middle",
        size_hint_y=None,
        height=min_height,
        text_size=(Window.width - dp(48), None),
    )
    widget.bind(width=lambda inst, value: setattr(inst, "text_size", (max(0, value - dp(12)), None)))
    widget.bind(texture_size=lambda inst, value: setattr(inst, "height", max(min_height, value[1] + dp(12))))
    return widget


def make_button(text, callback, color=ACCENT, height=48):
    button = Button(
        text=text,
        size_hint_y=None,
        height=dp(height),
        background_normal="",
        background_color=color,
        color=TEXT,
        font_size=sp(14),
        bold=True,
    )
    button.bind(on_release=lambda *_: callback())
    return button


def make_input(hint, text="", height=100, multiline=True):
    return TextInput(
        text=text,
        hint_text=hint,
        size_hint_y=None,
        height=dp(height),
        multiline=multiline,
        background_normal="",
        background_active="",
        background_color=PANEL2,
        foreground_color=TEXT,
        hint_text_color=MUTED,
        cursor_color=TEXT,
        padding=(dp(12), dp(12)),
        font_size=sp(15),
    )


class ItogApp(App):
    title = "ИТОГ — тренажёр сочинения"

    def build(self):
        Window.clearcolor = BG
        self.storage = AppStorage(self.user_data_dir)
        self.themes = ThemeBank()
        self.library = LiteratureLibrary()
        self.coach = EssayCoach(self.library)
        self.current_theme = ""
        self.current_screen = "home"
        self.root_box = BoxLayout(orientation="vertical", spacing=dp(8), padding=(dp(12), dp(10)))
        self.header = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        self.header.add_widget(make_label("ИТОГ", 22, TEXT, 42, True))
        self.ai_badge = make_label("ЛОКАЛЬНЫЙ ИИ · не запущен", 11, MUTED, 42, True, "right")
        self.header.add_widget(self.ai_badge)
        self.root_box.add_widget(self.header)

        self.content = BoxLayout(orientation="vertical")
        self.root_box.add_widget(self.content)
        self.nav = GridLayout(cols=5, size_hint_y=None, height=dp(56), spacing=dp(5))
        for name, title in (("home", "Главная"), ("themes", "Темы"), ("essay", "Сочинение"), ("coach", "ИИ"), ("library", "Книги")):
            self.nav.add_widget(make_button(title, lambda n=name: self.show_screen(n), PANEL2, 50))
        self.root_box.add_widget(self.nav)
        self.show_screen("home")
        return self.root_box

    def on_start(self):
        self.refresh_ai_badge()

    def scroll_page(self):
        layout = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(10), padding=(dp(4), dp(6)))
        layout.bind(minimum_height=layout.setter("height"))
        scroll = ScrollView(do_scroll_x=False, bar_width=dp(3))
        scroll.add_widget(layout)
        return scroll, layout

    def add_heading(self, layout, title, subtitle=None):
        layout.add_widget(make_label(title, 21, TEXT, 48, True))
        if subtitle:
            layout.add_widget(make_label(subtitle, 13, MUTED, 45))

    def show_screen(self, name):
        self.current_screen = name
        self.content.clear_widgets()
        if name == "home":
            self.build_home()
        elif name == "themes":
            self.build_themes()
        elif name == "essay":
            self.build_essay()
        elif name == "coach":
            self.build_coach()
        elif name == "library":
            self.build_library()
        elif name == "progress":
            self.build_progress()

    def build_home(self):
        scroll, body = self.scroll_page()
        self.add_heading(body, "Подготовка без зубрёжки", "Твоя цель — научиться самостоятельно раскрывать тему и доказывать мысль литературными примерами.")
        essays = self.storage.get_essays()
        done = int(self.storage.get_setting("completed_tasks", 0))
        total_words = sum(count_words(item.get("text", "")) for item in essays)
        body.add_widget(make_label(f"РАБОЧИЙ ПРОГРЕСС     {len(essays)} работ   ·   {total_words} слов   ·   {done} заданий", 13, GOOD, 42, True))
        body.add_widget(make_label("СЕГОДНЯ", 13, MUTED, 26, True))
        plan = [
            "1. Возьми одну тему и найди в ней главный вопрос.",
            "2. Запиши тезис — прямой ответ на вопрос темы.",
            "3. Подбери литературный эпизод и объясни его связь с тезисом.",
            "4. Напиши один связный абзац и проверь логику.",
        ]
        for item in plan:
            body.add_widget(make_label("• " + item, 14, TEXT, 46))
        body.add_widget(make_button("Начать тренировку темы", lambda: self.show_screen("themes")))
        body.add_widget(make_button("Написать полноценное сочинение", lambda: self.show_screen("essay"), PANEL2))
        body.add_widget(make_button("Спросить локальный ИИ", lambda: self.show_screen("coach"), PANEL2))
        body.add_widget(make_button("Открыть статистику подготовки", lambda: self.show_screen("progress"), PANEL2))
        body.add_widget(make_label("КАК РАБОТАЕТ ИИ", 13, MUTED, 28, True))
        body.add_widget(make_label("Qwen запускается непосредственно на телефоне. Текст не отправляется в облако. Первый запуск модели может быть долгим; во время работы телефон может нагреваться.", 13, MUTED, 76))
        self.content.add_widget(scroll)

    def build_themes(self):
        scroll, body = self.scroll_page()
        self.add_heading(body, "Тренажёр тем", "Сначала сформулируй вопрос темы своими словами. Не начинай писать, пока не понял, что именно нужно доказать.")
        sections = self.themes.sections()
        self.section_spinner = Spinner(text=sections[0], values=sections, size_hint_y=None, height=dp(48), background_color=PANEL2, color=TEXT)
        body.add_widget(self.section_spinner)
        self.topic_label = make_label("Нажми «Новая тема»", 17, TEXT, 100, True)
        body.add_widget(self.topic_label)
        self.topic_work = make_label("После выбора темы запиши: 1) ключевой вопрос; 2) тезис; 3) два литературных аргумента; 4) вывод.", 14, MUTED, 120)
        body.add_widget(self.topic_work)
        body.add_widget(make_button("Новая случайная тема", self.next_topic))
        body.add_widget(make_button("Разобрать выбранную тему с ИИ", self.analyze_selected_theme, PANEL2))
        body.add_widget(make_label("Важно: формулировки в тренажёре — учебные. Это не обещание, что именно такая тема попадётся на экзамене.", 12, WARN, 70))
        self.content.add_widget(scroll)

    def next_topic(self):
        topic = self.themes.random_topic(self.section_spinner.text)
        self.current_theme = topic["text"]
        self.topic_label.text = topic["text"]
        self.topic_work.text = f"Раздел: {topic['section']}\n\nПодумай: {topic['hint']}\n\nТвой тезис должен отвечать на вопрос темы, а не просто повторять её формулировку."

    def analyze_selected_theme(self):
        if not self.current_theme:
            self.popup("Сначала выбери тему", "Нажми кнопку «Новая случайная тема».")
            return
        self.show_screen("coach")
        self.mode_spinner.text = "Разобрать тему"
        self.coach_input.text = self.current_theme
        self.run_coach()

    def build_essay(self):
        scroll, body = self.scroll_page()
        self.add_heading(body, "Мастер сочинения", "Пиши своими словами. Сохраняй промежуточные версии и сравнивай, как меняется качество аргументации.")
        self._draft_event = None
        self.essay_title = make_input("Тема сочинения", self.storage.get_setting("draft_title", ""), 52, False)
        self.essay_title.bind(text=lambda _, value: self.storage.set_setting("draft_title", value))
        body.add_widget(self.essay_title)
        self.essay_text = make_input("Начни писать здесь…", self.storage.get_setting("draft_text", ""), 300, True)
        self.essay_text.bind(text=self.update_word_count)
        body.add_widget(self.essay_text)
        self.word_label = make_label("Слов: 0 · ориентир ФИПИ: от 250, рекомендуемый объём — от 350", 13, MUTED, 40, True)
        body.add_widget(self.word_label)
        self.update_word_count(self.essay_text, self.essay_text.text)
        body.add_widget(make_button("Сохранить черновик", self.save_essay, PANEL2))
        body.add_widget(make_button("Быстрая проверка структуры", self.quick_check, PANEL2))
        body.add_widget(make_button("Глубокая проверка локальным ИИ", self.analyze_essay))
        self.content.add_widget(scroll)

    def update_word_count(self, _widget, value):
        if hasattr(self, "word_label"):
            words = count_words(value)
            color = GOOD if words >= 350 else WARN if words >= 250 else MUTED
            self.word_label.text = f"Слов: {words} · минимум для допуска к оцениванию: 250 · ориентир: 350+"
            self.word_label.color = color
        if getattr(self, "_draft_event", None) is not None:
            self._draft_event.cancel()
        self._draft_event = Clock.schedule_once(lambda _dt, text=value: self.storage.set_setting("draft_text", text), 0.7)

    def save_essay(self):
        title = self.essay_title.text.strip() or "Черновик без названия"
        text = self.essay_text.text.strip()
        if not text:
            self.popup("Пока нечего сохранять", "Добавь текст сочинения и повтори.")
            return
        self.storage.save_essay(title, text)
        self.popup("Черновик сохранён", f"Сохранено слов: {count_words(text)}. Его можно найти в статистике.")

    def quick_check(self):
        report = basic_audit(self.essay_text.text)
        self.popup("Быстрая проверка", report)

    def analyze_essay(self):
        text = self.essay_text.text.strip()
        topic = self.essay_title.text.strip()
        if not text:
            self.popup("Нет текста", "Сначала напиши хотя бы черновик.")
            return
        self.show_screen("coach")
        self.mode_spinner.text = "Проверить сочинение"
        self.coach_input.text = f"ТЕМА: {topic or 'не указана'}\n\nСОЧИНЕНИЕ:\n{text}"
        self.run_coach()

    def build_coach(self):
        scroll, body = self.scroll_page()
        self.add_heading(body, "ИИ-наставник", "Можно попросить объяснить тему, найти слабое место в плане, проверить аргумент или подробно разобрать весь текст.")
        modes = ["Разобрать тему", "Проверить план", "Найти литературный аргумент", "Проверить сочинение", "Объяснить правило", "Ответить на мой вопрос"]
        self.mode_spinner = Spinner(text=modes[0], values=modes, size_hint_y=None, height=dp(48), background_color=PANEL2, color=TEXT)
        body.add_widget(self.mode_spinner)
        self.coach_input = make_input("Напиши вопрос, тему, план или вставь сочинение…", "", 190, True)
        body.add_widget(self.coach_input)
        body.add_widget(make_button("Разобрать", self.run_coach))
        self.ai_progress = ProgressBar(max=100, value=0, size_hint_y=None, height=dp(6))
        body.add_widget(self.ai_progress)
        self.ai_output = make_label("Ответ ИИ появится здесь. Модель запускается на устройстве и может отвечать медленнее облачных сервисов.", 14, MUTED, 280)
        body.add_widget(self.ai_output)
        body.add_widget(make_label("Проверка не является официальным решением экспертов ФИПИ. Используй её как обратную связь, а факты о произведениях перепроверяй по тексту.", 12, WARN, 76))
        self.content.add_widget(scroll)

    def run_coach(self):
        if not hasattr(self, "coach_input"):
            return
        query = self.coach_input.text.strip()
        if not query:
            self.popup("Нужен материал для разбора", "Введи тему, вопрос, план или текст.")
            return
        mode = self.mode_spinner.text
        self.ai_output.text = "Подготавливаю модель… Первый запуск может занять некоторое время."
        self.ai_output.color = MUTED
        self.ai_progress.value = 10

        def worker():
            try:
                answer = self.coach.answer(mode, query)
                Clock.schedule_once(lambda _dt: self._coach_done(answer, None), 0)
            except Exception as exc:
                Clock.schedule_once(lambda _dt, e=str(exc): self._coach_done(None, e), 0)

        threading.Thread(target=worker, daemon=True).start()

    def _coach_done(self, answer, error):
        if error:
            self.ai_output.text = "Не удалось запустить локальный ИИ.\n\n" + error
            self.ai_output.color = WARN
        else:
            self.ai_output.text = answer
            self.ai_output.color = TEXT
            self.storage.increment("completed_tasks")
        self.ai_progress.value = 100
        self.refresh_ai_badge()

    def build_library(self):
        scroll, body = self.scroll_page()
        self.add_heading(body, "Библиотека аргументов", "Ищи не просто название книги, а произведение, где есть подходящий нравственный конфликт и конкретный эпизод.")
        search = make_input("Поиск: совесть, выбор, дружба, война…", "", 52, False)
        body.add_widget(search)
        results = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(10))
        results.bind(minimum_height=results.setter("height"))
        body.add_widget(results)

        def render(*_):
            results.clear_widgets()
            entries = self.library.search(search.text)
            if not entries:
                results.add_widget(make_label("Ничего не найдено. Попробуй другое ключевое слово.", 14, MUTED, 60))
                return
            for entry in entries[:30]:
                card = BoxLayout(orientation="vertical", size_hint_y=None, padding=dp(10), spacing=dp(4))
                card.bind(minimum_height=card.setter("height"))
                card.add_widget(make_label(f"{entry['title']} — {entry['author']}", 15, TEXT, 32, True))
                card.add_widget(make_label(entry["summary"], 12, MUTED, 66))
                card.add_widget(make_label("Темы: " + ", ".join(entry["themes"]), 11, GOOD, 38))
                results.add_widget(card)
        search.bind(text=render)
        render()
        self.content.add_widget(scroll)

    def build_progress(self):
        scroll, body = self.scroll_page()
        self.add_heading(body, "Статистика подготовки", "Смотри на прогресс по работам и качеству рассуждений, а не только на количество написанных слов.")
        essays = self.storage.get_essays()
        total_words = sum(count_words(item.get("text", "")) for item in essays)
        body.add_widget(make_label(f"Сохранено работ: {len(essays)}", 17, TEXT, 42, True))
        body.add_widget(make_label(f"Всего написано слов: {total_words}", 17, TEXT, 42, True))
        body.add_widget(make_label(f"Завершено тренировок ИИ: {self.storage.get_setting('completed_tasks', 0)}", 17, TEXT, 42, True))
        body.add_widget(make_label("ПОСЛЕДНИЕ РАБОТЫ", 13, MUTED, 30, True))
        for item in essays[-10:][::-1]:
            words = count_words(item.get("text", ""))
            body.add_widget(make_label(f"{item.get('title', 'Без названия')} · {words} слов · {item.get('date', '')}", 13, MUTED, 48))
        body.add_widget(make_button("Вернуться на главную", lambda: self.show_screen("home")))
        self.content.add_widget(scroll)

    def refresh_ai_badge(self):
        state = self.coach.status()
        self.ai_badge.text = state

    def on_pause(self):
        if hasattr(self, "essay_text"):
            self.storage.set_setting("draft_text", self.essay_text.text)
        if hasattr(self, "essay_title"):
            self.storage.set_setting("draft_title", self.essay_title.text)
        return True

    def on_stop(self):
        try:
            self.coach.engine.close()
        except Exception:
            pass

    def popup(self, title, message):
        content = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(12))
        content.add_widget(make_label(message, 14, TEXT, 180))
        content.add_widget(make_button("Понятно", lambda: popup.dismiss()))
        popup = Popup(title=title, content=content, size_hint=(0.9, 0.55), auto_dismiss=True)
        popup.open()


if __name__ == "__main__":
    ItogApp().run()
