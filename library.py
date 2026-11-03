# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import re
from pathlib import Path

STOP = {"и", "в", "на", "о", "об", "для", "как", "что", "это", "ли", "к", "с", "по", "из", "не", "человек", "можно", "быть", "его", "её", "их", "или", "а", "но", "при", "над", "под", "от", "до"}


class LiteratureLibrary:
    def __init__(self):
        path = Path(__file__).parent / "data" / "books.json"
        self.entries = json.loads(path.read_text(encoding="utf-8"))

    def search(self, query):
        terms = {x.lower() for x in re.findall(r"[а-яёa-z0-9]+", query or "") if len(x) > 2 and x.lower() not in STOP}
        if not terms:
            return self.entries
        scored = []
        for entry in self.entries:
            haystack = " ".join([
                entry.get("title", ""), entry.get("author", ""), entry.get("summary", ""),
                entry.get("themes_text", ""), " ".join(entry.get("themes", [])),
                " ".join(entry.get("characters", [])), " ".join(entry.get("episodes", [])),
            ]).lower()
            score = sum(2 if term in entry.get("title", "").lower() else 1 for term in terms if term in haystack)
            if score:
                scored.append((score, entry))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [item[1] for item in scored]

    def context_for(self, query, limit=5):
        matched = self.search(query)[:limit]
        if not matched:
            return "В локальной библиотеке не найден подходящий материал. Не выдумывай эпизоды или цитаты; попроси пользователя назвать знакомое произведение."
        blocks = []
        for entry in matched:
            blocks.append(
                f"Произведение: {entry['title']}. Автор: {entry['author']}.\n"
                f"Краткое содержание: {entry['summary']}\n"
                f"Темы: {', '.join(entry['themes'])}.\n"
                f"Герои: {', '.join(entry['characters'])}.\n"
                f"Эпизоды для анализа: {'; '.join(entry['episodes'])}.\n"
                f"Связь с аргументацией: {entry['argument_use']}"
            )
        return "\n\n".join(blocks)
