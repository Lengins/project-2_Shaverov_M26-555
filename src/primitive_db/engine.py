"""Движок: запуск, цикл команд, парсинг."""

import shlex

from primitive_db.core import create_table, drop_table, list_tables
from primitive_db.utils import load_metadata, save_metadata



def welcome() -> None:
    """Первая попытка запустить проект: баннер и цикл команд."""
    print("Первая попытка запустить проект!")
    print()

    while True:
        print("***")
        print("<command> exit - выйти из программы")
        print("<command> help - справочная информация")

        command = input("Введите команду: ").strip()

        if command == "exit":
            print("Выход из программы.")
            break
        elif command == "help":
            print("Справка: доступны команды help и exit.")
        else:
            print(f"Неизвестная команда: {command}")



DEFAULT_DB_PATH = "db_meta.json"


def print_welcome() -> None:
    """Приветствие при старте программы."""
    print("\n***База данных***\n")
    print("Функции:")
    print("<command> create_table <имя_таблицы> <столбец1:тип> <столбец2:тип> .. - создать таблицу")
    print("<command> list_tables - показать список всех таблиц")
    print("<command> drop_table <имя_таблицы> - удалить таблицу")
    print("<command> exit - выход из программы")
    print("<command> help - справочная информация\n")


def print_help() -> None:
    """Справка по командам (код из задания)."""
    print("\n***Процесс работы с таблицей***")
    print("Функции:")
    print("<command> create_table <имя_таблицы> <столбец1:тип> .. - создать таблицу")
    print("<command> list_tables - показать список всех таблиц")
    print("<command> drop_table <имя_таблицы> - удалить таблицу")

    print("\nОбщие команды:")
    print("<command> exit - выход из программы")
    print("<command> help - справочная информация\n")


def _parse_columns(args: list[str]) -> list[tuple[str, str]]:
    """['name:str', 'age:int'] -> [('name', 'str'), ('age', 'int')]."""
    columns: list[tuple[str, str]] = []
    for arg in args:
        if ":" not in arg:
            raise ValueError(arg)
        name, typ = arg.split(":", 1)
        if not name or not typ:
            raise ValueError(arg)
        columns.append((name, typ))
    return columns


def run(db_path: str = DEFAULT_DB_PATH) -> None:
    """Главный цикл программы."""
    print_welcome()

    while True:
        try:
            user_input = input(">>>Введите команду: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not user_input:
            continue

        try:
            args = shlex.split(user_input)
        except ValueError as exc:
            print(f"Некорректное значение: {exc}. Попробуйте снова.")
            continue

        command, *rest = args

        if command == "exit":
            print("Выход из программы.")
            break

        elif command == "help":
            print_help()

        elif command == "create_table":
            # нужно минимум: имя таблицы + один столбец
            if len(rest) < 2:
                print(f"Некорректное значение: {user_input}. Попробуйте снова.")
                continue
            table_name = rest[0]
            try:
                columns = _parse_columns(rest[1:])
            except ValueError as exc:
                print(f"Некорректное значение: {exc}. Попробуйте снова.")
                continue
            metadata = load_metadata(db_path)
            result = create_table(metadata, table_name, columns)
            if result is not None:
                save_metadata(db_path, result)

        elif command == "drop_table":
            if len(rest) != 1:
                print(f"Некорректное значение: {user_input}. Попробуйте снова.")
                continue
            metadata = load_metadata(db_path)
            result = drop_table(metadata, rest[0])
            if result is not None:
                save_metadata(db_path, result)

        elif command == "list_tables":
            metadata = load_metadata(db_path)
            list_tables(metadata)

        else:
            print(f"Функции {command} нет. Попробуйте снова.")