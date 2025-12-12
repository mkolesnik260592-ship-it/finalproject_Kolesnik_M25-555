from datetime import datetime
import json
from pathlib import Path


USERS_PATH = Path("data/users.json")
PORTFOLIOS_PATH = Path("data/portfolios.json")
RATES_PATH = Path("data/rates.json")

def load_json(path: Path | str, default):
    if not Path(path).exists():
        return default
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(data, path: Path | str):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_users(path=USERS_PATH):
    return load_json(path, default=[])

def save_users(users, path=USERS_PATH):
    save_json(users, path)

def load_portfolios(path=PORTFOLIOS_PATH):
    return load_json(path, default=[])

def save_portfolios(portfolios, path=PORTFOLIOS_PATH):
    save_json(portfolios, path)

def load_rates(path=RATES_PATH):
    return load_json(path, default={})

def save_rates(rates, path=RATES_PATH):
    save_json(rates, path)

def find_user(users, username: str):
    return next((u for u in users if u.get("username") == username), None)

def next_user_id(users):
    if not users:
        return 1
    return max(u.get("user_id", 0) for u in users) + 1

def validate_currency_code(code: str) -> str:
    if not code or not code.strip():
        raise ValueError("Код валюты не может быть пустым")
    return code.strip().upper()

def validate_amount(amount: float) -> float:
    if not isinstance(amount, (int, float)) or amount <= 0:
        raise ValueError("Сумма не может быть отрицательной")
    return float(amount)


SESSION_PATH = Path("data/session.json")

def load_session():
    """Загрузить сессию из файла"""
    if not SESSION_PATH.exists():
        return None
    data = load_json(SESSION_PATH, default=None)
    return data

def save_session(user_id: int, username: str):
    """Сохранить сессию в файл"""
    data = {
        "user_id": user_id,
        "username": username,
        "timestamp": datetime.now().isoformat()
    }
    save_json(data, SESSION_PATH)

def clear_session():
    """Очистить сессию"""
    if SESSION_PATH.exists():
        SESSION_PATH.unlink()

def find_user_by_id(users, user_id: int):
    """Найти пользователя по ID"""
    return next((u for u in users if u.get("user_id") == user_id), None)
