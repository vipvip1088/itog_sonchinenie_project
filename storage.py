# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import threading
from datetime import datetime
from pathlib import Path


class AppStorage:
    def __init__(self, root):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = self.root / "itog_data.json"
        self.lock = threading.RLock()
        self.data = {"settings": {}, "essays": []}
        self._load()

    def _load(self):
        with self.lock:
            if not self.path.exists():
                return
            try:
                loaded = json.loads(self.path.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    self.data.update(loaded)
                    self.data.setdefault("settings", {})
                    self.data.setdefault("essays", [])
            except (OSError, json.JSONDecodeError):
                backup = self.path.with_suffix(".broken.json")
                try:
                    self.path.replace(backup)
                except OSError:
                    pass

    def _save(self):
        temp = self.path.with_suffix(".tmp")
        temp.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")
        temp.replace(self.path)

    def get_setting(self, key, default=None):
        with self.lock:
            return self.data["settings"].get(key, default)

    def set_setting(self, key, value):
        with self.lock:
            self.data["settings"][key] = value
            self._save()

    def increment(self, key, amount=1):
        with self.lock:
            self.data["settings"][key] = int(self.data["settings"].get(key, 0)) + amount
            self._save()

    def get_essays(self):
        with self.lock:
            return list(self.data.get("essays", []))

    def save_essay(self, title, text):
        with self.lock:
            essays = self.data.setdefault("essays", [])
            now = datetime.now().astimezone().isoformat(timespec="minutes")
            essays.append({"title": title, "text": text, "date": now, "created": datetime.now().timestamp()})
            self.data["essays"] = essays[-200:]
            self._save()
