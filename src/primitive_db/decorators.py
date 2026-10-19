"""Декораторы: обработка ошибок, подтверждение, тайминг, кэширование."""

import time
from functools import wraps


def handle_db_errors(func):
    """Централизованная обработка ошибок БД."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except FileNotFoundError:
            print("Ошибка: Файл данных не найден. Возможно, база данных не инициализирована.") # noqa: E501
        except KeyError as e:
            print(f"Ошибка: Таблица или столбец {e} не найден.")
        except ValueError as e:
            print(f"Ошибка валидации: {e}")
        except Exception as e:
            print(f"Произошла непредвиденная ошибка: {e}")
        return None
    return wrapper


def confirm_action(action_name: str):
    """Фабрика декораторов: спрашивает подтверждение перед опасной операцией."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            answer = input(
                f'Вы уверены, что хотите выполнить "{action_name}"? [y/n]: '
            ).strip().lower()
            if answer != "y":
                print("Операция отменена.")
                return None
            return func(*args, **kwargs)
        return wrapper
    return decorator


def log_time(func):
    """Замеряет время выполнения функции."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.monotonic()
        try:
            return func(*args, **kwargs)
        finally:
            elapsed = time.monotonic() - start
            print(f"Функция {func.__name__} выполнилась за {elapsed:.3f} секунд.")
    return wrapper


def create_cacher():
    """Замыкание-кэш. Возвращает cache_result(key, value_func)."""
    cache: dict = {}

    def cache_result(key, value_func):
        if key in cache:
            return cache[key]
        value = value_func()
        cache[key] = value
        return value

    def clear():
        cache.clear()

    # Расширение: инвалидация кэша при записи
    cache_result.clear = clear
    return cache_result