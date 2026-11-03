# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import random
from pathlib import Path


class ThemeBank:
    def __init__(self):
        path = Path(__file__).parent / "data" / "themes.json"
        self.data = json.loads(path.read_text(encoding="utf-8"))

    def sections(self):
        return list(self.data.keys())

    def random_topic(self, section):
        options = self.data.get(section) or [topic for group in self.data.values() for topic in group]
        item = random.choice(options)
        return {"section": section, **item}
