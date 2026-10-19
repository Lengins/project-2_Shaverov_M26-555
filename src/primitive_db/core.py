"""Ядро: операции с таблицами, данными и метаданными."""

from typing import Any

from primitive_db.utils import load_table_data

VALID_TYPES = {"int", "str", "bool"}


# ---------- Метаданные (из прошлого задания, без изменений) ----------

def create_table(
    metadata: dict[str, Any],
    table_name: str,
    columns: list[tuple[str, str]],
) -> dict[str, Any] | None:
    if table_name in metadata:
        print(f'Ошибка: Таблица "{table_name}" уже существует.')
        return None
    for _, col_type in columns:
        if col_type not in VALID_TYPES:
            print(f"Некорректное значение: {col_type}. Попробуйте снова.")
            return None
    full_columns = [{"name": "ID", "type": "int"}]
    full_columns.extend({"name": n, "type": t} for n, t in columns)
    metadata[table_name] = {"columns": full_columns}
    cols_repr = ", ".join(f"{c['name']}:{c['type']}" for c in full_columns)
    print(f'Таблица "{table_name}" успешно создана со столбцами: {cols_repr}')
    return metadata


def drop_table(metadata: dict[str, Any], table_name: str) -> dict[str, Any] | None:
    if table_name not in metadata:
        print(f'Ошибка: Таблица "{table_name}" не существует.')
        return None
    del metadata[table_name]
    print(f'Таблица "{table_name}" успешно удалена.')
    return metadata


def list_tables(metadata: dict[str, Any]) -> None:
    if not metadata:
        print("Таблиц нет.")
        return
    for name in metadata:
        print(f"- {name}")


# ---------- CRUD ----------

def _convert_value(raw: str, target_type: str) -> Any:
    """'28' -> int(28), '"Sergei"' -> 'Sergei', 'true' -> True."""
    raw = raw.strip()
    if target_type == "int":
        try:
            return int(raw)
        except ValueError:
            raise ValueError(raw)
    if target_type == "bool":
        low = raw.lower()
        if low == "true":
            return True
        if low == "false":
            return False
        raise ValueError(raw)
    if target_type == "str":
        if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in ('"', "'"):
            return raw[1:-1]
        raise ValueError(raw)
    raise ValueError(f"Неизвестный тип: {target_type}")


def _row_matches(row: dict, where_clause: dict) -> bool:
    return all(row.get(k) == v for k, v in where_clause.items())


def insert(
    metadata: dict[str, Any],
    table_name: str,
    raw_values: list[str],
) -> list[dict] | None:
    """Вставляет запись. ID генерируется. Возвращает данные или None при ошибке."""
    if table_name not in metadata:
        print(f'Ошибка: Таблица "{table_name}" не существует.')
        return None

    columns = metadata[table_name]["columns"]
    data_columns = columns[1:]  # без ID

    if len(raw_values) != len(data_columns):
        print(
            f'Ошибка: Таблица "{table_name}" ожидает {len(data_columns)} '
            f"значений (без ID), получено {len(raw_values)}."
        )
        return None

    record: dict[str, Any] = {}
    for raw, col in zip(raw_values, data_columns):
        try:
            record[col["name"]] = _convert_value(raw, col["type"])
        except ValueError:
            print(
                f'Ошибка: Некорректное значение "{raw}" '
                f'для столбца "{col["name"]}" ({col["type"]}).'
            )
            return None

    table_data = load_table_data(table_name)
    new_id = max((r["ID"] for r in table_data), default=0) + 1
    record["ID"] = new_id
    row = {c["name"]: record[c["name"]] for c in columns}
    table_data.append(row)

    print(f'Запись с ID={new_id} успешно добавлена в таблицу "{table_name}".')
    return table_data


def select(
    table_data: list[dict],
    where_clause: dict | None = None,
) -> list[dict]:
    if where_clause is None:
        return list(table_data)
    return [row for row in table_data if _row_matches(row, where_clause)]


def update(
    table_data: list[dict],
    set_clause: dict,
    where_clause: dict,
) -> tuple[list[dict], list[int]]:
    """Возвращает (data, affected_ids)."""
    affected: list[int] = []
    for row in table_data:
        if _row_matches(row, where_clause):
            row.update(set_clause)
            affected.append(row["ID"])
    return table_data, affected


def delete(
    table_data: list[dict],
    where_clause: dict,
) -> tuple[list[dict], list[int]]:
    """Возвращает (data, deleted_ids)."""
    kept: list[dict] = []
    deleted: list[int] = []
    for row in table_data:
        if _row_matches(row, where_clause):
            deleted.append(row["ID"])
        else:
            kept.append(row)
    return kept, deleted