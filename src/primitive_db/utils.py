import json
from pathlib import Path
from typing import Any


def load_metadata(filepath: str | Path) -> dict[str, Any]:
    """Загружает метаданные из JSON. Если файла нет — пустой словарь."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def save_metadata(filepath: str | Path, data: dict[str, Any]) -> None:
    """Сохраняет метаданные в JSON-файл."""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)