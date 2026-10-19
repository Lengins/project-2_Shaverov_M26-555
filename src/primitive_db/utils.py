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


DATA_DIR = Path("data")


def _table_path(table_name: str) -> Path:
    return DATA_DIR / f"{table_name}.json"


def load_table_data(table_name: str) -> list[dict]:
    """Загружает данные таблицы. Если файла нет — пустой список."""
    try:
        with open(_table_path(table_name), "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def save_table_data(table_name: str, data: list[dict]) -> None:
    """Сохраняет данные таблицы, создавая папку data/ при необходимости."""
    path = _table_path(table_name)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def delete_table_data(table_name: str) -> None:
    """Удаляет файл данных таблицы (вызывается при drop_table)."""
    path = _table_path(table_name)
    if path.exists():
        path.unlink()