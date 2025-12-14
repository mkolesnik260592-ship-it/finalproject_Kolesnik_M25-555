import json
import os
from typing import Dict, List
from .settings import SettingsLoader


class DatabaseManager:
    """Singleton для работы с JSON-хранилищем"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self._settings = SettingsLoader()
            self._cache = {}

    def _get_filepath(self, filename: str) -> str:
        """Получить полный путь к файлу"""
        data_dir = self._settings.get("data_dir","data")
        filepath = os.path.join(data_dir, filename)
        return filepath

    def _load_json(self, filename: str) -> List[Dict] | Dict:
        """Загрузить данные из JSON файла"""
        filepath = self._get_filepath(filename)

        if not os.path.exists(filepath):
            return [] if filename in ["users.json", "portfolios.json"] else {}

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return [] if filename in ["users.json", "portfolios.json"] else {}

    def _save_json(self, filename: str, data: List[Dict] | Dict) -> None:
        """Сохранить данные в JSON файл"""
        filepath = self._get_filepath(filename)

        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


    def get_users(self) -> List[Dict]:
        """Получить всех пользователей"""
        return self._load_json("users.json")

    def save_users(self, users: List[Dict]) -> None:
        """Сохранить пользователей"""
        self._save_json("users.json", users)

    def get_portfolios(self) -> List[Dict]:
        """Получить все портфели"""
        return self._load_json("portfolios.json")

    def save_portfolios(self, portfolios: List[Dict]) -> None:
        """Сохранить портфели"""
        self._save_json("portfolios.json", portfolios)

    def get_rates(self) -> Dict:
        """Получить курсы валют"""
        return self._load_json("rates.json")

    def save_rates(self, rates: Dict) -> None:
        """Сохранить курсы валют"""
        self._save_json("rates.json", rates)
