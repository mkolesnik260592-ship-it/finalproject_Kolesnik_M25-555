# Final Project: ValutaTrade Hub - Платформа для отслеживания и симуляции торговли валютами

## Описание

**ValutaTrade Hub** - консольное приложение для управления виртуальным портфелем фиатных и криптовалют. Приложение реализует полноценную платформу для симуляции торговли валютами с поддержкой регистрации пользователей, покупки/продажи валют по актуальным курсам, отслеживания состояния портфеля и логирования всех операций.

## Архитектура и принципы проектирования

Проект реализован с использованием современных принципов проектирования ПО:

- **Модульная архитектура** - разделение на слои (core, infra, cli)
- **Объектно-ориентированное программирование** - наследование, полиморфизм, инкапсуляция
- **Паттерны проектирования** - Singleton, Factory Method, Decorator
- **Принцип единственной ответственности** - каждый класс/модуль имеет одну четкую задачу
- **Обработка ошибок** - система пользовательских исключений с понятными сообщениями

## Реализованная функциональность

### 1. Иерархия валют с наследованием и полиморфизмом

- Абстрактный базовый класс `Currency`
- Наследники: `FiatCurrency` (фиатные валюты) и `CryptoCurrency` (криптовалюты)
- Полиморфный метод `get_display_info()` с разным поведением для разных типов валют
- Фабричный метод `get_currency(code)` для создания объектов валют
- Поддержка 7 валют (5 фиатных, 2 крипто)

### 2. Пользовательские исключения

- `InsufficientFundsError` - недостаточно средств для операции
- `CurrencyNotFoundError` - неизвестный код валюты
- `ApiRequestError` - ошибка при обращении к внешнему API
- `UserNotFoundError` - пользователь не найден

### 3. Паттерн Singleton

- `SettingsLoader` - единая точка конфигурации приложения
- `DatabaseManager` - абстракция над JSON-хранилищем данных
- Реализация через `__new__` с гарантией единственного экземпляра

### 4. Декоратор для логирования операций

- `@log_action` - декоратор для прозрачного логирования доменных операций
- Логирование на уровне INFO для успешных операций
- Логирование на уровне ERROR для операций с исключениями
- Ротация логов (10MB на файл, 5 файлов бэкапа)

### 5. Обновленная бизнес-логика

- Интеграция новой иерархии валют в операции покупки/продажи
- Использование пользовательских исключений вместо строковых ошибок
- Валидация кодов валют через фабричный метод
- TTL для кэша курсов валют (настраивается через SettingsLoader)

### 6. Расширенный CLI интерфейс

- Обработка пользовательских исключений с контекстными сообщениями
- Новая команда `list-currencies` для просмотра поддерживаемых валют
- Улучшенные сообщения об ошибках с подсказками
- Полная документация для каждой команды

### 7. Parser Service для получения курсов валют

- Конфигурация через `config.py` с загрузкой API ключей из .env файла
- API клиенты для работы с CoinGecko (криптовалюты) и ExchangeRate-API (фиатные валюты)
- Основной модуль обновления курсов `updater.py`
- Атомарное сохранение данных в `storage.py`
- Планировщик автоматического обновления в `scheduler.py`
- Историческое хранилище курсов в `exchange_rates.json`
- Текущий кеш курсов в `rates.json`
- Новые CLI команды:
  - `update-rates` - обновить курсы из внешних API
  - `show-rates` - показать текущие курсы из локального кеша
  - `parser-status` - статус Parser Service
  - `start-scheduler` - запустить планировщик автоматического обновления
  - `stop-scheduler` - остановить планировщик

## Структура проекта

finalproject_Kolesnik_M25-555/
├── valutatrade_hub/              # Основной Python пакет
│   ├── core/                     # Бизнес-логика и доменные модели
│   │   ├── currencies.py         # Иерархия валют: Currency, FiatCurrency, CryptoCurrency
│   │   ├── exceptions.py         # Пользовательские исключения (4 класса)
│   │   ├── models.py             # Доменные модели: User, Wallet, Portfolio
│   │   ├── usecases.py           # Сценарии использования с @log_action
│   │   └── utils.py              # Вспомогательные функции и валидация
│   ├── infra/                    # Инфраструктурный слой
│   │   ├── settings.py           # Singleton SettingsLoader (конфигурация)
│   │   └── database.py           # Singleton DatabaseManager (работа с JSON)
│   ├── parser_service/           # Сервис парсинга курсов валют
│   │   ├── config.py             # Конфигурация API и параметров обновления
│   │   ├── api_clients.py        # Клиенты для работы с внешними API
│   │   ├── updater.py            # Основной модуль обновления курсов
│   │   ├── storage.py            # Операции чтения/записи exchange_rates.json
│   │   └── scheduler.py          # Планировщик периодического обновления
│   ├── cli/                      # Интерфейс командной строки
│   │   └── interface.py          # CLI интерфейс с обработкой исключений
│   ├── decorators.py             # Декоратор @log_action
│   └── logging_config.py         # Настройка системы логирования
├── data/                         # Хранение данных (JSON файлы)
│   ├── users.json                # Зарегистрированные пользователи
│   ├── portfolios.json           # Портфели пользователей
│   ├── rates.json                # Курсы валют с временными метками
│   └── exchange_rates.json       # Исторические данные курсов валют
├── logs/                         # Логи операций (автоматически создается)
│   └── actions.log               # Ротируемый файл логов
├── main.py                       # Точка входа в приложение
├── pyproject.toml                # Конфигурация Poetry и проекта
├── Makefile                      # Автоматизация задач
└── README.md                     # Документация

## Установка и запуск

### Предварительные требования

- Python 3.12 или выше
- Poetry (система управления зависимостями)

### Установка

Установка зависимостей через Poetry:
make install

Альтернативный способ:
poetry install

Запуск:
make project

Запуск через Poetry:
poetry run project --help

Или напрямую через Python:
python main.py --help

## Использование

### Доступные команды

Команда | Описание | Пример использования

register | Регистрация нового пользователя | poetry run project register --username alice --password 1234

login | Вход в существующий профиль | poetry run project login --username alice --password 1234

show-portfolio | Просмотр портфеля | poetry run project show-portfolio --base EUR

buy | Покупка валюты | poetry run project buy --currency BTC --amount 0.01

sell | Продажа валюты | poetry run project sell --currency BTC --amount 0.005

get-rate | Получение курса валют | poetry run project get-rate --from USD --to EUR

list-currencies | Список поддерживаемых валют | poetry run project list-currencies

whoami | Текущий пользователь | poetry run project whoami

logout | Выход из системы | poetry run project logout

update-rates | Обновить курсы валют из внешних API | poetry run project update-rates --source coingecko

show-rates | Показать текущие курсы из локального кеша | poetry run project show-rates --top 3

parser-status | Показать статус Parser Service | poetry run project parser-status

start-scheduler | Запустить планировщик автоматического обновления | poetry run project start-scheduler

stop-scheduler | Остановить планировщик автоматического обновления | poetry run project stop-scheduler

Полный рабочий сеанс
Регистрация нового пользователя:
poetry run project register --username trader --password trade123

Вход в систему:
poetry run project login --username trader --password trade123

Просмотр списка доступных валют:
poetry run project list-currencies

Получение текущего курса:
poetry run project get-rate --from USD --to EUR

Обновление курсов валют:
poetry run project update-rates

Просмотр обновленных курсов:
poetry run project show-rates --top 3

Покупка евро:
poetry run project buy --currency EUR --amount 100

Просмотр обновленного портфеля:
poetry run project show-portfolio

Продажа части евро:
poetry run project sell --currency EUR --amount 50

Просмотр информации о текущем пользователе:
poetry run project whoami

Выход из системы:
poetry run project logout

## Поддерживаемые валюты

Фиатные валюты (FiatCurrency)

Код | Название | Страна/Зона эмиссии | Пример курса к USD

USD | US Dollar | United States | 1.0000 (базовая)
EUR | Euro | Eurozone | ~1.0786
RUB | Russian Ruble | Russia | ~0.01016
GBP | British Pound | United Kingdom | ~1.2589
JPY | Japanese Yen | Japan | ~0.0064

Криптовалюты (CryptoCurrency)

Код | Название | Алгоритм | Рыночная капитализация

BTC | Bitcoin | SHA-256 | ~1.2 трлн USD
ETH | Ethereum | Ethash | ~400 млрд USD

## Разработка и расширение

Запуск линтера:
make lint

Сборка пакета:
make build

### Добавление новой валюты

Откройте файл valutatrade_hub/core/currencies.py

Добавьте валюту в словарь _SUPPORTED_CURRENCIES:

python

"NEW": FiatCurrency("NEW", "New Currency", "Country")

или

python

"NEW": CryptoCurrency("NEW", "New Crypto", "Algorithm", market_cap)

### Настройка конфигурации

Конфигурация хранится в pyproject.toml в секции [tool.valutatrade]:

toml

[tool.valutatrade]

data_dir = "data"

rates_ttl_seconds = 3600

initial_usd_balance = 1000.0

log_level = "INFO"

### Настройка API ключей

Создайте файл .env в корне проекта

Добавьте API ключ для ExchangeRate-API:

EXCHANGERATE_API_KEY=ваш_api_ключ_здесь

### Особенности реализации

Безопасность:

- Пароли хранятся в виде хешей SHA256 с уникальной солью

- Сессионные данные валидируются при каждой загрузке

- API ключи загружаются из переменных окружения

Надежность:

- Все операции атомарно сохраняются в JSON файлы

- Обработка исключений на всех уровнях приложения

- Ротация логов для предотвращения переполнения диска

- Fallback режим при недоступности внешних API

Удобство использования:

- Сохранение сессии между вызовами команд

- Контекстные сообщения об ошибках с подсказками

- Полная документация для каждой команды CLI

- Автоматическое обновление курсов по расписанию

Расширяемость:

- Модульная архитектура для легкого добавления функциональности

- Абстрактные классы и интерфейсы для поддержки новых типов валют

- Конфигурация через файлы и переменные окружения

- Поддержка новых источников данных через API клиенты

### Технологии

Python 3.12+ - основной язык программирования

Poetry - управление зависимостями, сборка и публикация пакетов

argparse - парсинг аргументов командной строки

Ruff - линтинг и форматирование кода (dev зависимость)

JSON - хранение данных (пользователи, портфели, курсы, сессии)

logging - система логирования с ротацией файлов

abc - модуль для создания абстрактных классов

requests - HTTP запросы к внешним API

python-dotenv - загрузка переменных окружения из .env файлов

Лицензия
MIT

Автор
Колесник Матвей Анатольевич - студент группы M25-555
