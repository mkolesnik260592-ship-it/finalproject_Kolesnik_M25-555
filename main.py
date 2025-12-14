#!/usr/bin/env python3
"""Точка входа в приложение ValutaTrade Hub"""

from valutatrade_hub.logging_config import setup_logging
from valutatrade_hub.core.utils import setup_data_directories
from valutatrade_hub.cli.interface import main

# Настраиваем логирование
setup_logging()

# Создаем необходимые директории
setup_data_directories()

if __name__ == "__main__":
    main()
