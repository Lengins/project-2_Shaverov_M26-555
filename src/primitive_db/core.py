"""Ядро: операции с таблицами и метаданными."""

from typing import Any

VALID_TYPES = {"int", "str", "bool"}


def create_table(
    metadata: dict[str, Any],
    table_name: str,
    columns: list[tuple[str, str]],
) -> dict[str, Any] | None:
    """Создаёт таблицу. Возвращает обновлённый metadata или None при ошибке."""
    if table_name in metadata:
        print(f'Ошибка: Таблица "{table_name}" уже существует.')
        return None

    for col_name, col_type in columns:
        if col_type not in VALID_TYPES:
            print(f"Некорректное значение: {col_type}. Попробуйте снова.")
            return None

    # ID:int всегда первый, автоматически
    full_columns: list[dict[str, str]] = [{"name": "ID", "type": "int"}]
    full_columns.extend({"name": name, "type": typ} for name, typ in columns)

    metadata[table_name] = {"columns": full_columns}

    cols_repr = ", ".join(f"{c['name']}:{c['type']}" for c in full_columns)
    print(f'Таблица "{table_name}" успешно создана со столбцами: {cols_repr}')
    return metadata


def drop_table(metadata: dict[str, Any], table_name: str) -> dict[str, Any] | None:
    """Удаляет таблицу. Возвращает обновлённый metadata или None при ошибке."""
    if table_name not in metadata:
        print(f'Ошибка: Таблица "{table_name}" не существует.')
        return None

    del metadata[table_name]
    print(f'Таблица "{table_name}" успешно удалена.')
    return metadata


def list_tables(metadata: dict[str, Any]) -> None:
    """Печатает список таблиц."""
    if not metadata:
        print("Таблиц нет.")
        return
    for table_name in metadata:
        print(f"- {table_name}")