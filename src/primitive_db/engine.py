"""Движок: запуск, цикл команд, парсинг, вывод."""

import re
import shlex

from prettytable import PrettyTable

from primitive_db.core import (
    _convert_value,
    create_table,
    delete,
    drop_table,
    insert,
    list_tables,
    select,
    update,
)
from primitive_db.decorators import create_cacher
from primitive_db.utils import (
    delete_table_data,
    load_metadata,
    load_table_data,
    save_metadata,
    save_table_data,
)

DEFAULT_DB_PATH = "db_meta.json"

# Кэш результатов select (per-process)
_select_cacher = create_cacher()

INSERT_RE = re.compile(
    r"^insert\s+into\s+(\w+)\s+values\s*\(\s*(.*?)\s*\)\s*$",
    re.IGNORECASE | re.DOTALL,
)
SELECT_RE = re.compile(
    r"^select\s+from\s+(\w+)(?:\s+where\s+(\w+)\s*=\s*(.+))?\s*$",
    re.IGNORECASE,
)
UPDATE_RE = re.compile(
    r"^update\s+(\w+)\s+set\s+(\w+)\s*=\s*(.+?)\s+where\s+(\w+)\s*=\s*(.+)\s*$",
    re.IGNORECASE,
)
DELETE_RE = re.compile(
    r"^delete\s+from\s+(\w+)\s+where\s+(\w+)\s*=\s*(.+)\s*$",
    re.IGNORECASE,
)


# ---------- Сообщения ----------

def print_welcome() -> None:
    print("\n***База данных***\n")
    _print_commands_block()
    print()


def print_help() -> None:
    print("\n***Операции с данными***")
    _print_commands_block()
    print()


def _print_commands_block() -> None:
    print("Функции:")
    print("<command> create_table <имя_таблицы> <столбец1:тип> .. - создать таблицу")
    print("<command> list_tables - показать список всех таблиц")
    print("<command> drop_table <имя_таблицы> - удалить таблицу")
    print("<command> info <имя_таблицы> - информация о таблице")
    print(
        "<command> insert into <имя_таблицы> values (<зн1>, <зн2>, ...) "
        "- добавить запись"
    )
    print(
        "<command> select from <имя_таблицы> [where <столбец> = <значение>] "
        "- прочитать"
    )
    print(
        "<command> update <имя_таблицы> set <столбец> = <значение> "
        "where <условие> - обновить"
    )
    print(
        "<command> delete from <имя_таблицы> where <столбец> = <значение> "
        "- удалить"
    )
    print()
    print("Общие команды:")
    print("<command> exit - выход из программы")
    print("<command> help - справочная информация")


# ---------- Вспомогательные парсеры ----------

def _split_values(text: str) -> list[str]:
    """'\"Sergei\", 28, true' -> ['\"Sergei\"', '28', 'true']."""
    parts: list[str] = []
    buf: list[str] = []
    quote: str | None = None
    for ch in text:
        if quote:
            buf.append(ch)
            if ch == quote:
                quote = None
        elif ch in ('"', "'"):
            quote = ch
            buf.append(ch)
        elif ch == ",":
            parts.append("".join(buf).strip())
            buf = []
        else:
            buf.append(ch)
    last = "".join(buf).strip()
    if last or parts:
        parts.append(last)
    return parts


def _parse_where(
    metadata: dict,
    table_name: str,
    col_name: str,
    raw_value: str,
) -> dict:
    """'age', '28' -> {'age': 28} с учётом типа столбца из metadata."""
    for col in metadata[table_name]["columns"]:
        if col["name"] == col_name:
            return {col_name: _convert_value(raw_value, col["type"])}
    raise ValueError(f"неизвестный столбец: {col_name}")


# ---------- Вывод таблицы ----------

def _print_table(data: list[dict], columns: list[dict]) -> None:
    if not data:
        print("Нет записей.")
        return
    table = PrettyTable()
    table.field_names = [c["name"] for c in columns]
    for row in data:
        table.add_row([row[c["name"]] for c in columns])
    table.align = "c"
    print(table)


# ---------- Обработчики команд ----------

def _handle_create(rest: list[str], db_path: str) -> None:
    if len(rest) < 2:
        print(f"Некорректное значение: {' '.join(rest)}. Попробуйте снова.")
        return
    table_name, *col_args = rest
    try:
        columns: list[tuple[str, str]] = []
        for arg in col_args:
            if ":" not in arg:
                raise ValueError(arg)
            name, typ = arg.split(":", 1)
            if not name or not typ:
                raise ValueError(arg)
            columns.append((name, typ))
    except ValueError as exc:
        print(f"Некорректное значение: {exc}. Попробуйте снова.")
        return
    metadata = load_metadata(db_path)
    result = create_table(metadata, table_name, columns)
    if result is not None:
        save_metadata(db_path, result)


def _handle_drop(rest: list[str], db_path: str) -> None:
    if len(rest) != 1:
        print(f"Некорректное значение: {' '.join(rest)}. Попробуйте снова.")
        return
    table_name = rest[0]
    metadata = load_metadata(db_path)
    result = drop_table(metadata, table_name)
    if result is not None:
        save_metadata(db_path, result)
        delete_table_data(table_name)
        _select_cacher.clear()


def _handle_info(rest: list[str], db_path: str) -> None:
    if len(rest) != 1:
        print(f"Некорректное значение: {' '.join(rest)}. Попробуйте снова.")
        return
    table_name = rest[0]
    metadata = load_metadata(db_path)
    if table_name not in metadata:
        print(f'Ошибка: Таблица "{table_name}" не существует.')
        return
    columns = metadata[table_name]["columns"]
    data = load_table_data(table_name)
    cols_repr = ", ".join(f"{c['name']}:{c['type']}" for c in columns)
    print(f"Таблица: {table_name}")
    print(f"Столбцы: {cols_repr}")
    print(f"Количество записей: {len(data)}")


def _handle_insert(m: re.Match, db_path: str) -> None:
    table_name = m.group(1)
    raw_values = _split_values(m.group(2))
    metadata = load_metadata(db_path)
    result = insert(metadata, table_name, raw_values)
    if result is not None:
        save_table_data(table_name, result)
        _select_cacher.clear()


def _handle_select(m: re.Match, db_path: str) -> None:
    table_name = m.group(1)
    where_col = m.group(2)
    where_val = m.group(3)

    metadata = load_metadata(db_path)
    if table_name not in metadata:
        print(f'Ошибка: Таблица "{table_name}" не существует.')
        return

    where_clause = None
    if where_col:
        try:
            where_clause = _parse_where(metadata, table_name, where_col, where_val)
        except ValueError as exc:
            print(f"Некорректное значение: {exc}. Попробуйте снова.")
            return

    def fetch() -> list[dict]:
        return select(load_table_data(table_name), where_clause)

    key = (
        table_name,
        tuple(sorted(where_clause.items())) if where_clause else None,
    )
    data = _select_cacher(key, fetch)
    _print_table(data, metadata[table_name]["columns"])


def _handle_update(m: re.Match, db_path: str) -> None:
    table_name = m.group(1)
    set_col, set_val = m.group(2), m.group(3)
    where_col, where_val = m.group(4), m.group(5)

    metadata = load_metadata(db_path)
    if table_name not in metadata:
        print(f'Ошибка: Таблица "{table_name}" не существует.')
        return

    try:
        set_clause = _parse_where(metadata, table_name, set_col, set_val)
        where_clause = _parse_where(metadata, table_name, where_col, where_val)
    except ValueError as exc:
        print(f"Некорректное значение: {exc}. Попробуйте снова.")
        return

    data = load_table_data(table_name)
    result = update(data, set_clause, where_clause)
    if result is None:
        return  # декоратор уже напечатал ошибку
    data, affected = result
    save_table_data(table_name, data)
    _select_cacher.clear()

    if not affected:
        print("Нет записей, подходящих под условие.")
    for id_ in affected:
        print(f'Запись с ID={id_} в таблице "{table_name}" успешно обновлена.')


def _handle_delete(m: re.Match, db_path: str) -> None:
    table_name = m.group(1)
    where_col, where_val = m.group(2), m.group(3)

    metadata = load_metadata(db_path)
    if table_name not in metadata:
        print(f'Ошибка: Таблица "{table_name}" не существует.')
        return

    try:
        where_clause = _parse_where(metadata, table_name, where_col, where_val)
    except ValueError as exc:
        print(f"Некорректное значение: {exc}. Попробуйте снова.")
        return

    data = load_table_data(table_name)
    result = delete(data, where_clause)
    if result is None:
        return  # либо отменили, либо ошибка — декоратор уже сообщил
    data, deleted = result
    save_table_data(table_name, data)
    _select_cacher.clear()

    if not deleted:
        print("Нет записей, подходящих под условие.")
    for id_ in deleted:
        print(f'Запись с ID={id_} успешно удалена из таблицы "{table_name}".')


# ---------- Главный цикл ----------

def run(db_path: str = DEFAULT_DB_PATH) -> None:
    print_welcome()
    while True:
        try:
            user_input = input(">>>Введите команду: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not user_input:
            continue

        # Структурные команды с нетривиальным синтаксисом — через regex
        if m := INSERT_RE.match(user_input):
            _handle_insert(m, db_path)
            continue
        if m := SELECT_RE.match(user_input):
            _handle_select(m, db_path)
            continue
        if m := UPDATE_RE.match(user_input):
            _handle_update(m, db_path)
            continue
        if m := DELETE_RE.match(user_input):
            _handle_delete(m, db_path)
            continue

        # Простые команды — через shlex
        try:
            args = shlex.split(user_input)
        except ValueError as exc:
            print(f"Некорректное значение: {exc}. Попробуйте снова.")
            continue
        if not args:
            continue
        command, *rest = args

        if command == "exit":
            print("Выход из программы.")
            break
        elif command == "help":
            print_help()
        elif command == "create_table":
            _handle_create(rest, db_path)
        elif command == "drop_table":
            _handle_drop(rest, db_path)
        elif command == "list_tables":
            list_tables(load_metadata(db_path))
        elif command == "info":
            _handle_info(rest, db_path)
        else:
            print(f"Функции {command} нет. Попробуйте снова.")