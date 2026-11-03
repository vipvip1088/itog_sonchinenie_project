# -*- coding: utf-8 -*-
from __future__ import annotations

import re
from collections import Counter

WORD_RE = re.compile(r"[A-Za-zА-Яа-яЁё0-9]+(?:[-’'][A-Za-zА-Яа-яЁё0-9]+)*")


def words(text: str) -> list[str]:
    return WORD_RE.findall(text or "")


def count_words(text: str) -> int:
    return len(words(text))


def basic_audit(text: str) -> str:
    text = (text or "").strip()
    if not text:
        return "Текст пустой."
    tokens = words(text)
    n = len(tokens)
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    sentences = [s for s in re.split(r"[.!?…]+", text) if s.strip()]
    repeated = [(w, c) for w, c in Counter(x.lower() for x in tokens).most_common(8) if c >= 8 and len(w) > 3]
    lines = [f"Объём: {n} слов."]
    if n < 250:
        lines.append("НЕДОСТАТОЧНЫЙ ОБЪЁМ: менее 250 слов — это основание для незачёта по требованию объёма.")
    elif n < 350:
        lines.append("Объём достиг минимума 250 слов, но лучше довести работу примерно до 350 слов.")
    else:
        lines.append("Объём соответствует рекомендуемому ориентиру 350+ слов.")
    lines.append(f"Абзацев: {len(paragraphs)}. Предложений (приблизительно): {len(sentences)}.")
    if len(paragraphs) < 4:
        lines.append("Проверь композицию: обычно удобно выделить вступление, основные аргументы и заключение.")
    if len(sentences) > 0 and sum(len(s.split()) for s in sentences) / len(sentences) > 35:
        lines.append("Есть очень длинные предложения. Проверь, можно ли разделить их без потери смысла.")
    if repeated:
        lines.append("Возможные повторы слов: " + ", ".join(f"{w} ({c})" for w, c in repeated) + ".")
    lines.append("Автоматическая проверка не оценивает соответствие теме и качество литературной аргументации — для этого нужен содержательный разбор.")
    lines.append("Официальные критерии: К1 — соответствие теме; К2 — аргументация с привлечением литературного материала; К3 — композиция и логика; К4 — качество речи; К5 — грамотность.")
    lines.append("Для общего зачёта К1 и К2 должны быть зачтены, а также должен быть зачтён хотя бы один из К3–К5. Это ориентир для обучения, а не официальный вердикт.")
    return "\n".join(lines)
