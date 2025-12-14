"""
Singleton для загрузки конфигурации
Реализация через __new__ для гарантии одного экземпляра
"""

import os
import tomllib
from typing import Any


class SettingsLoader:
    """Singleton для загрузки и кэширования конфигурации"""

    _instance = None

    def __new__(cls):
        """Реализация Singleton через __new__"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            # Инициализация выполняется только один раз
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Инициализация настроек (выполняется только один раз)"""
        if not hasattr(self, '_initialized') or not self._initialized:
            self._initialized = True
            self._config = self._load_config()

    def _load_config(self) -> dict[str, Any]:
        """Загружает конфигурацию из pyproject.toml и env переменных"""
        config = {
            # Пути к данным
            "data_dir": "data",
            "logs_dir": "logs",

            # Настройки курсов
            "rates_ttl_seconds": 3600,  # 1 час
            "default_base_currency": "USD",
            "supported_currencies": ["USD", "EUR", "RUB", "GBP", "JPY", "BTC", "ETH"],

            # Настройки логов
            "log_file": "logs/actions.log",
            "log_level": "INFO",
            "log_max_bytes": 10485760,  # 10 MB
            "log_backup_count": 5,

            # Настройки пользователей
            "initial_usd_balance": 1000.0,
            "min_password_length": 4,

            # Настройки API (заглушка)
            "api_timeout": 10,
            "api_max_retries": 3,
        }

        # Пытаемся загрузить из pyproject.toml
        try:
            with open("pyproject.toml", "rb") as f:
                toml_data = tomllib.load(f)

            if "tool" in toml_data and "valutatrade" in toml_data["tool"]:
                user_config = toml_data["tool"]["valutatrade"]
                config.update(user_config)

        except (FileNotFoundError, KeyError, tomllib.TOMLDecodeError):
            pass  # Используем значения по умолчанию

        # Можно добавить загрузку из переменных окружения
        for key in config:
            env_key = f"VALUTATRADE_{key.upper()}"
            if env_key in os.environ:
                value = os.environ[env_key]
                # Преобразование типов
                if isinstance(config[key], bool):
                    config[key] = value.lower() in ("true", "1", "yes")
                elif isinstance(config[key], int):
                    config[key] = int(value)
                elif isinstance(config[key], float):
                    config[key] = float(value)
                else:
                    config[key] = value

        return config

    def get(self, key: str, default: Any = None) -> Any:
        """Получить значение настройки"""
        return self._config.get(key, default)

    def reload(self) -> None:
        """Перезагрузить конфигурацию"""
        self._config = self._load_config()

    def __getitem__(self, key: str) -> Any:
        """Получить значение настройки через квадратные скобки"""
        return self._config[key]

    def __contains__(self, key: str) -> bool:
        """Проверить наличие настройки"""
        return key in self._config
