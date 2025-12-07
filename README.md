# Final Project: Валютный кошелёк

## Описание

Консольное приложение для управления виртуальным портфелем фиатных и криптовалют.

## Структура проекта

- `valutatrade_hub/` - основной пакет
  - `core/models.py` - классы User, Wallet, Portfolio
  - `core/utils.py` - работа с JSON файлами
  - `core/usecases.py` - бизнес-логика
  - `cli/interface.py` - консольный интерфейс
- `data/` - JSON файлы для хранения данных
- `main.py` - точка входа

## Установка

make install## Использование
h
make project## Разработка
h
make lint  # Проверка кода
make build  # Сборка пакета## Технологии

- Python 3.12+
- Poetry (управление зависимостями)
- Ruff (линтинг)
- PrettyTable (форматированный вывод)
