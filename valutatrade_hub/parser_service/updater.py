"""
Основной модуль обновления курсов валют
"""

from typing import Dict, Any
from datetime import datetime, timezone
from .config import config
from .api_clients import get_api_client
from .storage import RatesStorage
from ..core.exceptions import ApiRequestError
from ..decorators import log_action


class RatesUpdater:
    def __init__(self):
        self.storage = RatesStorage()
        self._sources_order = ["coingecko", "exchangerate"]

        print("=" * 50)
        print("ИНИЦИАЛИЗАЦИЯ PARSER SERVICE")
        print(f"   Базовая валюта: {config.BASE_CURRENCY}")
        print(f"   Фиатные валюты: {', '.join(config.FIAT_CURRENCIES)}")
        print(f"   Криптовалюты: {', '.join(config.CRYPTO_CURRENCIES)}")

        if not config.EXCHANGERATE_API_KEY:
            print("ВНИМАНИЕ: API ключ не найден. Используйте fallback режим или")
            print("добавьте EXCHANGERATE_API_KEY в .env файл")
        print("=" * 50)

    @log_action
    def run_update(self, source: str = "all") -> Dict[str, Any]:
        print("\n" + "=" * 50)
        print("ЗАПУСК ОБНОВЛЕНИЯ КУРСОВ")
        print(f"   Источник: {source}")
        print("=" * 50)

        all_rates = {}
        results = {
            "success": False,
            "total_rates": 0,
            "sources_processed": 0,
            "sources_failed": 0,
            "details": [],
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z"
        }

        sources_to_update = []
        if source == "all":
            sources_to_update = self._sources_order.copy()
        elif source in ["coingecko", "exchangerate"]:
            sources_to_update = [source]
        else:
            raise ValueError(f"Неизвестный источник: {source}. "
                           f"Используйте: all, coingecko, exchangerate")

        if "exchangerate" in sources_to_update and not config.EXCHANGERATE_API_KEY:
            print("API ключ не найден, заменяем exchangerate на fallback")
            sources_to_update[sources_to_update.index("exchangerate")] = "fallback"

        for src in sources_to_update:
            try:
                print(f"\nИсточник: {src.upper()}")

                client = get_api_client(src)
                rates_data = client.fetch_rates()

                all_rates.update(rates_data["rates"])

                self.storage.save_to_history(rates_data)

                results["details"].append({
                    "source": src,
                    "status": "success",
                    "rates_count": rates_data["count"],
                    "timestamp": rates_data["timestamp"]
                })

                print(f"   Успешно: {rates_data['count']} курсов")
                results["sources_processed"] += 1

            except ApiRequestError as e:
                error_msg = str(e)
                results["details"].append({
                    "source": src,
                    "status": "error",
                    "error": error_msg
                })
                results["sources_failed"] += 1
                print(f"   Ошибка: {error_msg}")

            except Exception as e:
                error_msg = f"Неизвестная ошибка: {e}"
                results["details"].append({
                    "source": src,
                    "status": "error",
                    "error": error_msg
                })
                results["sources_failed"] += 1
                print(f"   Критическая ошибка: {error_msg}")

        if all_rates:
            self.storage.save_current_rates({
                "rates": all_rates,
                "timestamp": results["timestamp"],
                "source": "mixed" if len(sources_to_update) > 1
                         else sources_to_update[0]
            })

            results["success"] = True
            results["total_rates"] = len(all_rates)

        print("\n" + "=" * 50)
        if results["success"]:
            print("ОБНОВЛЕНИЕ ЗАВЕРШЕНО")
            print(f"   Всего курсов: {results['total_rates']}")
            print(f"   Источников обработано: {results['sources_processed']}")
            if results["sources_failed"] > 0:
                print(f"   Источников с ошибками: {results['sources_failed']}")
        else:
            print("ОБНОВЛЕНИЕ НЕ УДАЛОСЬ")
            print("   Не удалось получить ни одного курса")

        print(f"   Время: {results['timestamp']}")
        print("=" * 50)

        return results

    def get_status(self) -> Dict[str, Any]:
        cache_data = self.storage.load_current_rates()

        return {
            "cache_exists": self.storage.rates_file.exists(),
            "cache_valid": self.storage.is_cache_valid(),
            "last_refresh": cache_data.get("last_refresh"),
            "total_pairs": cache_data.get("total_pairs", 0),
            "config": {
                "base_currency": config.BASE_CURRENCY,
                "fiat_currencies": config.FIAT_CURRENCIES,
                "crypto_currencies": config.CRYPTO_CURRENCIES,
                "has_api_key": bool(config.EXCHANGERATE_API_KEY)
            }
        }

    def force_update(self) -> Dict[str, Any]:
        print("ПРИНУДИТЕЛЬНОЕ ОБНОВЛЕНИЕ (игнорируя TTL)")
        return self.run_update("all")


updater = RatesUpdater()
