from abc import ABC, abstractmethod
from typing import Dict
from .exceptions import CurrencyNotFoundError


class Currency(ABC):

    def __init__(self, code: str, name: str):
        code = code.strip().upper()
        if not (2 <= len(code) <= 5):
            raise ValueError(f"Код валюты должен быть 2-5 символов: {code}")
        if not name or not name.strip():
            raise ValueError("Название валюты не может быть пустым")
        self._code = code
        self._name = name

    @property
    def code(self) -> str:
        return self._code

    @property
    def name(self) -> str:
        return self._name

    @abstractmethod
    def get_display_info(self) -> str:
        """Вернуть строковое представление валюты"""
        pass


class FiatCurrency(Currency):
    """Фиатная валюта (доллары, евро, рубли и тд.)"""

    def __init__(self, code: str, name: str, issuing_country: str):
        super().__init__(code, name)
        self._issuing_country = issuing_country

    @property
    def issuing_country(self) -> str:
        return self._issuing_country

    def get_display_info(self) -> str:
        """Вернуть строку в формате: [FIAT] USD — US Dollar (Issuing: United States)"""

        return f"[FIAT] {self._code} - {self._name} (Issuing: {self._issuing_country})"


class CryptoCurrency(Currency):
    """Криптовалюта (Bitcoin, Ethereum и тд.)"""

    def __init__(self, code: str, name: str, algorithm: str, market_cap: float = 0.0):
        super().__init__(code, name)
        self._algorithm = algorithm
        self._market_cap = float(market_cap)

    @property
    def algorithm(self) -> str:
        return self._algorithm

    @property
    def market_cap(self) -> float:
        return self._market_cap

    def get_display_info(self) -> str:
        """Вернуть строку в формате: [CRYPTO] BTC — Bitcoin (Algo: SHA-256, MCAP: 1.12e12)"""

        return f"[CRYPTO] {self._code} - {self.name} (Algo: {self._algorithm}, MCAP: {self._market_cap:.2e})"


_SUPPORTED_CURRENCIES: Dict[str, Currency] = {
    "USD": FiatCurrency("USD", "US Dollar", "United States"),
    "EUR": FiatCurrency("EUR", "Euro", "Eurozone"),
    "RUB": FiatCurrency("RUB", "Russian Ruble", "Russia"),
    "GBP": FiatCurrency("GBP", "British Pound", "United Kingdom"),
    "JPY": FiatCurrency("JPY", "Japanese Yen", "Japan"),
    "BTC": CryptoCurrency("BTC", "Bitcoin", "SHA-256", 1_200_000_000_000),
    "ETH": CryptoCurrency("ETH", "Ethereum", "Ethash", 400_000_000_000),
}

def get_currency(code: str) -> Currency:
    """Получит валюту по коду"""
    code = code.strip().upper()
    if code in _SUPPORTED_CURRENCIES:
        return _SUPPORTED_CURRENCIES[code]
    else:
        raise CurrencyNotFoundError(code)


class SettingsLoader:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance


    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self._config = self._load_config()

    def _load_config(self):
        """Загружает настройки"""
        return {
            "data_dir": "data",
            "rates_ttl_seconds": 3600,
            "default_base_currency": "USD",
            "log_file": "logs/actions.log",
            "log_level": "INFO"
        }

    def get(self, key, default=None):
        """Получить настройку"""
        return self._config.get(key, default)

    def reload(self):
        pass
