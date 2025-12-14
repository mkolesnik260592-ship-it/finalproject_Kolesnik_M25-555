"""
Модуль для работы с хранилищами данных о курсах валют
"""

import json
import os
import tempfile
from typing import Dict, Any
from datetime import datetime, timezone
from pathlib import Path
from .config import config, DataSource


class RatesStorage:
    def __init__(self):
        self.rates_file = Path(config.RATES_FILE_PATH)
        self.history_file = Path(config.HISTORY_FILE_PATH)

        self.rates_file.parent.mkdir(parents=True, exist_ok=True)
        self.history_file.parent.mkdir(parents=True, exist_ok=True)

    def save_current_rates(self, rates_data: Dict[str, Any]) -> None:
        current_time = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        pairs = {}
        for pair_key, rate in rates_data.get("rates", {}).items():
            pairs[pair_key] = {
                "rate": float(rate),
                "updated_at": rates_data.get("timestamp", current_time),
                "source": rates_data.get("source", DataSource.FALLBACK)
            }

        data = {
            "pairs": pairs,
            "last_refresh": current_time,
            "total_pairs": len(pairs)
        }

        self._atomic_write(self.rates_file, data)

        print(f"Сохранено {len(pairs)} курсов в {self.rates_file}")

    def load_current_rates(self) -> Dict[str, Any]:
        if not self.rates_file.exists():
            return {"pairs": {}, "last_refresh": None}

        try:
            with open(self.rates_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Ошибка загрузки rates.json: {e}")
            return {"pairs": {}, "last_refresh": None}

    def is_cache_valid(self) -> bool:
        data = self.load_current_rates()
        if not data.get("last_refresh"):
            return False

        try:
            last_refresh = datetime.fromisoformat(
                data["last_refresh"].replace('Z', '+00:00')
            )
            age = datetime.now(timezone.utc) - last_refresh
            return age.total_seconds() < config.CACHE_TTL
        except (ValueError, TypeError):
            return False

    def save_to_history(self, rates_data: Dict[str, Any]) -> None:
        if not rates_data.get("rates"):
            return

        history = self._load_history()

        timestamp = rates_data.get("timestamp",
                                  datetime.now(timezone.utc).isoformat() + "Z")
        source = rates_data.get("source", DataSource.FALLBACK)

        for pair_key, rate in rates_data["rates"].items():
            parts = pair_key.split('_')
            if len(parts) != 2:
                continue

            from_curr, to_curr = parts

            record_id = f"{from_curr}_{to_curr}_{timestamp}"

            record = {
                "id": record_id,
                "from_currency": from_curr,
                "to_currency": to_curr,
                "rate": float(rate),
                "timestamp": timestamp,
                "source": source,
                "meta": {
                    "request_ms": 0,
                    "status_code": 200
                }
            }

            history[record_id] = record

        self._atomic_write(self.history_file, history)

        print(f"Добавлено в историю: {len(rates_data['rates'])} записей")

    def _load_history(self) -> Dict[str, Any]:
        if not self.history_file.exists():
            return {}

        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}

    def _atomic_write(self, filepath: Path, data: Dict[str, Any]) -> None:
        temp_fd, temp_path = tempfile.mkstemp(
            dir=filepath.parent,
            prefix=f".{filepath.name}.",
            suffix=".tmp"
        )

        try:
            with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            os.replace(temp_path, filepath)

        except Exception as e:
            try:
                os.unlink(temp_path)
            except OSError:
                pass
            raise e

    def get_rates_for_currency(self, currency_code: str) -> Dict[str, float]:
        data = self.load_current_rates()
        pairs = data.get("pairs", {})

        result = {}
        for pair_key, pair_data in pairs.items():
            if currency_code in pair_key:
                result[pair_key] = pair_data["rate"]

        return result

    def get_top_rates(self, n: int = 5) -> list:
        data = self.load_current_rates()
        pairs = data.get("pairs", {})

        sorted_pairs = sorted(
            pairs.items(),
            key=lambda x: x[1]["rate"],
            reverse=True
        )

        return [
            {"pair": pair, **data}
            for pair, data in sorted_pairs[:n]
        ]
