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

make project## Разработка

make lint  # Проверка кода
make build  # Сборка пакета## Технологии

- Python 3.12+
- Poetry (управление зависимостями)
- Ruff (линтинг)
- PrettyTable (форматированный вывод)

## Использование

### Базовые команды:

```bash
# Регистрация нового пользователя
poetry run project register --username <имя> --password <пароль>

# Вход в систему
poetry run project login --username <имя> --password <пароль>

# Показать текущего пользователя
poetry run project whoami

# Показать портфель
poetry run project show-portfolio [--base <валюта>]

# Купить валюту
poetry run project buy --currency <код> --amount <количество>

# Продать валюту
poetry run project sell --currency <код> --amount <количество>

# Получить курс валют
poetry run project get-rate --from <валюта> --to <валюта>

# Выйти из системы
poetry run project logout
