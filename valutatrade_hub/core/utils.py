"""
Вспомогательные функции для работы с данными
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from .currencies import get_currency, get_supported_currencies
from ..infra.database import DatabaseManager
from ..infra.settings import SettingsLoader


def setup_data_directories() -> None:
    """Создать необходимые директории для данных"""
    settings = SettingsLoader()
    data_dir = settings.get("data_dir", "data")
    logs_dir = settings.get("logs_dir", "logs")

    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(logs_dir, exist_ok=True)


def validate_currency_code(code: str) -> str:
    """
    Валидация кода валюты
    Args:
        code: Код валюты для проверки
    Returns:
        Валидированный код в верхнем регистре
    Raises:
        CurrencyNotFoundError: если валюта не поддерживается
    """
    code = code.strip().upper()

    # Проверяем через get_currency, который бросит CurrencyNotFoundError
    get_currency(code)

    return code


def validate_amount(amount: float) -> float:
    """
    Валидация суммы
    Args:
        amount: Сумма для проверки
    Returns:
        Валидированную сумму
    Raises:
        ValueError: если сумма некорректна
    """
    if not isinstance(amount, (int, float)):
        raise ValueError("Сумма должна быть числом")
    if amount <= 0:
        raise ValueError("Сумма должна быть положительной")
    return float(amount)


def load_users() -> List[Dict[str, Any]]:
    """Загрузить всех пользователей через DatabaseManager"""
    db = DatabaseManager()
    return db.get_users()


def save_users(users: List[Dict[str, Any]]) -> None:
    """Сохранить пользователей через DatabaseManager"""
    db = DatabaseManager()
    db.save_users(users)


def load_portfolios() -> List[Dict[str, Any]]:
    """Загрузить все портфели через DatabaseManager"""
    db = DatabaseManager()
    return db.get_portfolios()


def save_portfolios(portfolios: List[Dict[str, Any]]) -> None:
    """Сохранить портфели через DatabaseManager"""
    db = DatabaseManager()
    db.save_portfolios(portfolios)


def load_rates() -> Dict[str, Any]:
    """Загрузить курсы валют через DatabaseManager"""
    db = DatabaseManager()
    return db.get_rates()


def save_rates(rates: Dict[str, Any]) -> None:
    """Сохранить курсы валют через DatabaseManager"""
    db = DatabaseManager()
    db.save_rates(rates)


def load_session() -> Dict[str, Any]:
    """Загрузить данные сессии"""
    try:
        with open("data/session.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_session(user_id: int, username: str) -> None:
    """Сохранить данные сессии"""
    session_data = {
        "user_id": user_id,
        "username": username,
        "timestamp": datetime.now().isoformat()
    }
    with open("data/session.json", "w", encoding="utf-8") as f:
        json.dump(session_data, f, indent=2, ensure_ascii=False)


def clear_session() -> None:
    """Очистить данные сессии"""
    try:
        os.remove("data/session.json")
    except FileNotFoundError:
        pass


def find_user(users: List[Dict], username: str) -> Optional[Dict]:
    """Найти пользователя по имени"""
    for user in users:
        if user.get("username") == username:
            return user
    return None


def find_user_by_id(users: List[Dict], user_id: int) -> Optional[Dict]:
    """Найти пользователя по ID"""
    for user in users:
        if user.get("user_id") == user_id:
            return user
    return None


def next_user_id(users: List[Dict]) -> int:
    """Получить следующий ID пользователя"""
    if not users:
        return 1
    return max(user.get("user_id", 0) for user in users) + 1


def should_refresh_rates() -> bool:
    """
    Проверить, нужно ли обновлять курсы валют
    Returns:
        True если курсы устарели, False если актуальны
    """
    settings = SettingsLoader()
    ttl_seconds = settings.get("rates_ttl_seconds", 3600)

    rates = load_rates()
    if not rates:
        return True

    # Проверяем время последнего обновления
    for rate_data in rates.values():
        if "updated_at" in rate_data:
            try:
                updated_at = datetime.fromisoformat(rate_data["updated_at"])
                age = datetime.now() - updated_at
                return age.total_seconds() > ttl_seconds
            except (ValueError, KeyError):
                return True

    return True


def get_currency_display_info(code: str) -> str:
    """
    Получить информацию о валюте для отображения
    Args:
        code: Код валюты
    Returns:
        Строковое представление валюты
    """
    currency = get_currency(code)
    return currency.get_display_info()


def get_supported_currencies_list() -> List[str]:
    """Получить список поддерживаемых валют"""
    return get_supported_currencies()
