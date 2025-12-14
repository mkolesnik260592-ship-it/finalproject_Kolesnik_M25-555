"""
Планировщик для периодического обновления курсов валют
"""

import time
import threading
from typing import Optional
from datetime import datetime
from .updater import updater
from .config import config


class Scheduler:
    def __init__(self):
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._is_running = False

    def start(self, interval: Optional[int] = None) -> None:
        if self._is_running:
            print("Планировщик уже запущен")
            return

        update_interval = interval or config.UPDATE_INTERVAL

        print("=" * 50)
        print("ЗАПУСК ПЛАНИРОВЩИКА")
        print(f"   Интервал обновления: {update_interval} сек")
        print(f"   ({update_interval/3600:.1f} ч)")
        print(f"   Следующее обновление: через {update_interval} сек")
        print("=" * 50)

        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run_scheduler,
            args=(update_interval,),
            daemon=True
        )
        self._thread.start()
        self._is_running = True

        print("Планировщик запущен в фоновом режиме")

    def stop(self) -> None:
        if not self._is_running:
            print("Планировщик не запущен")
            return

        print("Остановка планировщика...")
        self._stop_event.set()

        if self._thread:
            self._thread.join(timeout=5)

        self._is_running = False
        print("Планировщик остановлен")

    def _run_scheduler(self, interval: int) -> None:
        last_update = None

        while not self._stop_event.is_set():
            try:
                current_time = datetime.now().strftime("%H:%M:%S")

                should_update = (
                    last_update is None or
                    (time.time() - last_update) >= interval or
                    not updater.storage.is_cache_valid()
                )

                if should_update:
                    print(f"\n[{current_time}] Запланированное обновление...")
                    result = updater.run_update("all")

                    if result["success"]:
                        last_update = time.time()
                        next_update = datetime.fromtimestamp(
                            last_update + interval
                        ).strftime("%H:%M:%S")
                        print(f"   Следующее обновление: {next_update}")
                    else:
                        print("   Обновление не удалось")

                time.sleep(60)

            except Exception as e:
                print(f"Ошибка в планировщике: {e}")
                time.sleep(300)

    def status(self) -> dict:
        cache_status = updater.get_status()

        return {
            "is_running": self._is_running,
            "thread_alive": self._thread.is_alive() if self._thread else False,
            "cache_status": cache_status,
            "config": {
                "update_interval": config.UPDATE_INTERVAL,
                "cache_ttl": config.CACHE_TTL
            }
        }


scheduler = Scheduler()
