"""
Конфигурация Parser Service
"""

import os
from dataclasses import dataclass, field
from typing import Dict, Tuple
from dotenv import load_dotenv

load_dotenv()


class DataSource:
    COINGECKO = "CoinGecko"
    EXCHANGERATE_API = "ExchangeRate-API"
    FALLBACK = "Fallback"


@dataclass
class ParserConfig:
    EXCHANGERATE_API_KEY: str = os.getenv("EXCHANGERATE_API_KEY", "")

    COINGECKO_URL: str = "https://api.coingecko.com/api/v3/simple/price"
    EXCHANGERATE_API_URL: str = "https://v6.exchangerate-api.com/v6"

    BASE_CURRENCY: str = "USD"

    FIAT_CURRENCIES: Tuple[str, ...] = ("EUR", "GBP", "RUB", "JPY", "CNY")
    CRYPTO_CURRENCIES: Tuple[str, ...] = ("BTC", "ETH", "SOL")

    CRYPTO_ID_MAP: Dict[str, str] = field(default_factory=lambda: {
        "BTC": "bitcoin",
        "ETH": "ethereum",
        "SOL": "solana",
    })

    RATES_FILE_PATH: str = "data/rates.json"
    HISTORY_FILE_PATH: str = "data/exchange_rates.json"

    REQUEST_TIMEOUT: int = 15
    MAX_RETRIES: int = 3
    RETRY_DELAY: int = 2

    UPDATE_INTERVAL: int = 3600
    CACHE_TTL: int = 900

    def __post_init__(self):
        if not self.EXCHANGERATE_API_KEY:
            print("ВНИМАНИЕ: EXCHANGERATE_API_KEY не найден.")
            print("Создайте файл .env с EXCHANGERATE_API_KEY=ваш_ключ")
            print("Будет использован Fallback режим")

        self.EXCHANGERATE_API_FULL_URL = (
            f"{self.EXCHANGERATE_API_URL}/"
            f"{self.EXCHANGERATE_API_KEY}/latest/{self.BASE_CURRENCY}"
        )


config = ParserConfig()
