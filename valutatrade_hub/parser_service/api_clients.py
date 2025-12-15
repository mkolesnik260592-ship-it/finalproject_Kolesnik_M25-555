
"""Клиенты для работы с внешними API курсов валют"""

import time
import requests
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
from .config import config, DataSource
from ..core.exceptions import ApiRequestError


class BaseApiClient(ABC):
    """Абстрактный базовый класс для API клиентов"""

    def __init__(self, source_name: str):
        self.source_name = source_name
        self._session = requests.Session()
        self._last_request_time = 0
        self._request_count = 0

    @abstractmethod
    def fetch_rates(self) -> Dict[str, Any]:
        """Получить курсы валют от API"""
        pass

    def _make_request(self, url: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Выполнить HTTP запрос с обработкой ошибок и rate limiting"""

        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        if time_since_last < 1.0:
            time.sleep(1.0 - time_since_last)

        headers = {
            "User-Agent": "ValutaTradeHub/1.0",
            "Accept": "application/json"
        }

        try:
            response = self._session.get(
                url,
                params=params,
                headers=headers,
                timeout=config.REQUEST_TIMEOUT
            )
            response.raise_for_status()

            self._last_request_time = time.time()
            self._request_count += 1

            return response.json()

        except requests.exceptions.Timeout:
            raise ApiRequestError(f"Таймаут при запросе к {self.source_name}")
        except requests.exceptions.ConnectionError:
            raise ApiRequestError(f"Ошибка соединения с {self.source_name}")
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code
            if status_code == 429:
                raise ApiRequestError(f"Превышен лимит запросов к {self.source_name}")
            elif status_code == 401:
                raise ApiRequestError(f"Неверный API ключ для {self.source_name}")
            else:
                raise ApiRequestError(f"HTTP ошибка {status_code}")
        except ValueError as e:
            raise ApiRequestError(f"Некорректный JSON ответ от {self.source_name}: {e}")
        except Exception as e:
                raise ApiRequestError(f"Неизвестная ошибка: {e}")


class CoinGeckoClient(BaseApiClient):
    """Клиент для CoinGecko API (криптовалюты)"""

    def __init__(self):
        super().__init__(DataSource.COINGECKO)

    def fetch_rates(self) -> Dict[str, Any]:
        """Получить курсы криптовалют от CoinGecko"""

        crypto_ids = [config.CRYPTO_ID_MAP[code] for code in config.CRYPTO_CURRENCIES]
        ids_param = ",".join(crypto_ids)

        params = {
            "ids": ids_param,
            "vs_currencies": "usd"
        }

        print(f"Запрос к CoinGecko: {config.CRYPTO_CURRENCIES}")

        data = self._make_request(config.COINGECKO_URL, params)

        standardized_rates = {}
        for currency_code, gecko_id in config.CRYPTO_ID_MAP.items():
            if gecko_id in data and "usd" in data[gecko_id]:
                pair_key = f"{currency_code}_{config.BASE_CURRENCY}"
                standardized_rates[pair_key] = data[gecko_id]["usd"]

        return {
            "source": DataSource.COINGECKO,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "base_currency": config.BASE_CURRENCY,
            "rates": standardized_rates,
            "count": len(standardized_rates)
        }


class ExchangeRateApiClient(BaseApiClient):
    """Клиент для ExchangeRate-API (фиатные валюты)"""

    def __init__(self):
        super().__init__(DataSource.EXCHANGERATE_API)

        if not config.EXCHANGERATE_API_KEY:
            raise ApiRequestError(
                "API ключ для ExchangeRate-API не найден. "
                "Добавьте EXCHANGERATE_API_KEY в .env файл или переменные окружения."
            )

    def fetch_rates(self) -> Dict[str, Any]:
        """Получить курсы фиатных валют от ExchangeRate-API"""

        print(f"Запрос к ExchangeRate-API: {config.FIAT_CURRENCIES}")

        data = self._make_request(config.EXCHANGERATE_API_FULL_URL)

        if data.get("result") != "success":
            raise ApiRequestError(f"Ошибка: {data.get("error-type", "unknown")}")

        standardized_rates = {}
        all_rates = data.get("conversion_rates", {})

        for currency in config.FIAT_CURRENCIES:
            if currency in all_rates:
                pair_key = f"{currency}_{config.BASE_CURRENCY}"
                standardized_rates[pair_key] = all_rates[currency]

        for currency in config.FIAT_CURRENCIES:
            if currency in all_rates and currency != config.BASE_CURRENCY:
                pair_key = f"{config.BASE_CURRENCY}_{currency}"
                rate = all_rates[currency]
                if rate != 0:
                    standardized_rates[pair_key] = 1 / rate

        return {
            "source": DataSource.EXCHANGERATE_API,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "base_currency": config.BASE_CURRENCY,
            "rates": standardized_rates,
            "count": len(standardized_rates)
        }


class FallbackClient(BaseApiClient):
    """Резервный клиент с фиксированными курсами (если API недоступны)"""

    def __init__(self):
        super().__init__(DataSource.FALLBACK)

    def fetch_rates(self) -> Dict[str, Any]:
        """Возвращает фиксированные курсы для демонстрации"""

        print("Используются фиксированные курсы (Fallback режим)")


        fixed_rates = {
            # Криптовалюты
            "BTC_USD": 59337.21,
            "ETH_USD": 3720.00,
            "SOL_USD": 145.12,

            # Фиатные валюты
            "EUR_USD": 1.0786,
            "GBP_USD": 1.2589,
            "RUB_USD": 0.01016,
            "JPY_USD": 0.0064,
            "CNY_USD": 0.1378,

            # Обратные пары
            "USD_EUR": 0.9271,
            "USD_GBP": 0.7942,
            "USD_RUB": 98.4252,
            "USD_JPY": 156.25,
            "USD_CNY": 7.2556,
        }

        return {
            "source": DataSource.FALLBACK,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "base_currency": config.BASE_CURRENCY,
            "rates": fixed_rates,
            "count": len(fixed_rates)
        }


def get_api_client(source: str):
    """Фабрика для создания клиентов API"""
    clients = {
        "coingecko": CoinGeckoClient,
        "exchangerate": ExchangeRateApiClient,
        "fallback": FallbackClient
    }

    client_class = clients.get(source.lower())
    if not client_class:
        raise ValueError(f"Неизвестный источник: {source}")

    return client_class()
