"""
Иерархия валют с использованием наследования и полиморфизма
"""

from abc import ABC, abstractmethod
from typing import Dict
from .exceptions import CurrencyNotFoundError


class Currency(ABC):
    """Абстрактный базовый класс для валют"""
    
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
        """Вернуть строковое представление валюты для UI/логов"""
        pass


class FiatCurrency(Currency):
    """Фиатная валюта (доллары, евро, рубли и т.д.)"""
    
    def __init__(self, code: str, name: str, issuing_country: str):
        super().__init__(code, name)
        self._issuing_country = issuing_country
    
    @property
    def issuing_country(self) -> str:
        return self._issuing_country
    
    def get_display_info(self) -> str:
        """[FIAT] USD — US Dollar (Issuing: United States)"""
        return f"[FIAT] {self._code} — {self._name} (Issuing: {self._issuing_country})"


class CryptoCurrency(Currency):
    """Криптовалюта (Bitcoin, Ethereum и т.д.)"""
    
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
        """[CRYPTO] BTC — Bitcoin (Algo: SHA-256, MCAP: 1.12e12)"""
        return f"[CRYPTO] {self._code} — {self._name} (Algo: {self._algorithm}, MCAP: {self._market_cap:.2e})"


# Реестр поддерживаемых валют
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
    """
    Фабричный метод для получения валюты по коду
    
    Args:
        code: Код валюты (USD, EUR, BTC и т.д.)
    
    Returns:
        Экземпляр Currency (FiatCurrency или CryptoCurrency)
    
    Raises:
        CurrencyNotFoundError: если валюта не поддерживается
    """
    code = code.strip().upper()
    if code in _SUPPORTED_CURRENCIES:
        return _SUPPORTED_CURRENCIES[code]
    else:
        raise CurrencyNotFoundError(code)


def get_supported_currencies() -> list[str]:
    """Получить список всех поддерживаемых валют"""
    return list(_SUPPORTED_CURRENCIES.keys())
