from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict

try:
    from config import DATA_DIR  # если есть
except Exception:
    DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

SETTINGS_PATH = os.path.join(DATA_DIR, "ui_settings.json")


@dataclass
class UISettings:
    theme: str = "light"          # "light" | "dark"
    sidebar_visible: bool = True


class AppSettings:
    @staticmethod
    def load() -> UISettings:
        try:
            if not os.path.exists(SETTINGS_PATH):
                return UISettings()
            with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                raw = json.load(f)
            return UISettings(
                theme=str(raw.get("theme", "light")),
                sidebar_visible=bool(raw.get("sidebar_visible", True)),
            )
        except Exception:
            return UISettings()

    @staticmethod
    def save(settings: UISettings) -> None:
        os.makedirs(os.path.dirname(SETTINGS_PATH), exist_ok=True)
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(asdict(settings), f, ensure_ascii=False, indent=2)
