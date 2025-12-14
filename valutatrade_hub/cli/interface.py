"""
CLI интерфейс приложения
"""

import argparse
import sys
import os
from valutatrade_hub.core.usecases import (
    register,
    login,
    show_portfolio,
    buy,
    sell,
    get_rate,
    logout_user,
    get_current_user_info,
    list_supported_currencies
)
from valutatrade_hub.core.exceptions import (
    InsufficientFundsError,
    CurrencyNotFoundError,
    ApiRequestError,
    UserNotFoundError
)
from valutatrade_hub.parser_service.updater import updater
from valutatrade_hub.parser_service.scheduler import scheduler


def main():
    parser = argparse.ArgumentParser(
        description="Валютный кошелек - управление виртуальным портфелем",
        prog="valutatrade",
        epilog="Используйте 'valutatrade <команда> --help' для справки по команде"
    )

    subparsers = parser.add_subparsers(
        dest="command",
        help="Доступные команды"
    )

    register_parser = subparsers.add_parser(
        "register",
        help="Регистрация нового пользователя"
    )
    register_parser.add_argument(
        "--username",
        required=True,
        help="Имя пользователя"
    )
    register_parser.add_argument(
        "--password",
        required=True,
        help="Пароль (минимум 4 символа)"
    )

    login_parser = subparsers.add_parser(
        "login",
        help="Вход в существующий профиль"
    )
    login_parser.add_argument(
        "--username",
        required=True,
        help="Имя пользователя"
    )
    login_parser.add_argument(
        "--password",
        required=True,
        help="Пароль"
    )

    portfolio_parser = subparsers.add_parser(
        "show-portfolio",
        help="Информация о кошельке"
    )
    portfolio_parser.add_argument(
        "--base",
        default="USD",
        help="Базовая валюта для конвертации (по умолчанию USD)"
    )

    buy_parser = subparsers.add_parser(
        "buy",
        help="Покупка валюты"
    )
    buy_parser.add_argument(
        "--currency",
        required=True,
        help="Выбранная валюта для покупки"
    )
    buy_parser.add_argument(
        "--amount",
        type=float,
        required=True,
        help="Количество для покупки"
    )

    sell_parser = subparsers.add_parser(
        "sell",
        help="Продажа валюты"
    )
    sell_parser.add_argument(
        "--currency",
        required=True,
        help="Код валюты для продажи"
    )
    sell_parser.add_argument(
        "--amount",
        type=float,
        required=True,
        help="Количество для продажи"
    )

    rate_parser = subparsers.add_parser(
        "get-rate",
        help="Получить курс валюты"
    )
    rate_parser.add_argument(
        "--from",
        dest="cur_from",
        required=True,
        help="Исходная валюта"
    )
    rate_parser.add_argument(
        "--to",
        dest="cur_to",
        required=True,
        help="Целевая валюта"
    )

    subparsers.add_parser(
        "logout",
        help="Выход из системы"
    )

    subparsers.add_parser(
        "whoami",
        help="Показать текущего пользователя"
    )

    subparsers.add_parser(
        "list-currencies",
        help="Показать список поддерживаемых валют"
    )

    update_parser = subparsers.add_parser(
        "update-rates",
        help="Обновить курсы валют из внешних API"
    )
    update_parser.add_argument(
        "--source",
        choices=["all", "coingecko", "exchangerate"],
        default="all",
        help="Источник для обновления (по умолчанию: все)"
    )
    update_parser.add_argument(
        "--force",
        action="store_true",
        help="Принудительное обновление (игнорирует TTL кеша)"
    )

    show_rates_parser = subparsers.add_parser(
        "show-rates",
        help="Показать текущие курсы из локального кеша"
    )
    show_rates_parser.add_argument(
        "--currency",
        help="Показать курс только для указанной валюты"
    )
    show_rates_parser.add_argument(
        "--top",
        type=int,
        help="Показать N самых дорогих валют"
    )
    show_rates_parser.add_argument(
        "--base",
        default="USD",
        help="Базовая валюта для отображения (по умолчани USD)"
    )
    show_rates_parser.add_argument(
        "--verbose",
        action="store_true",
        help="Подробный вывод с временем обновления"
    )

    subparsers.add_parser(
        "parser-status",
        help="Показать статус Parser Service"
    )

    subparsers.add_parser(
        "start-scheduler",
        help="Запустить планировщик автоматического обновления"
    )

    subparsers.add_parser(
        "stop-scheduler",
        help="Остановить планировщик автоматического обновления"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        result = handle_command(args)
        if result:
            print(result)
    except InsufficientFundsError as e:
        print(f"Ошибка: {e}")
        print("Проверьте баланс и попробуйте снова.")
        sys.exit(1)
    except CurrencyNotFoundError as e:
        print(f"Ошибка: {e}")
        print("Используйте команду 'list-currencies' чтобы увидеть доступные валюты.")
        sys.exit(1)
    except ApiRequestError as e:
        print(f"Ошибка API: {e}")
        print("Пожалуйста, повторите попытку позже или проверьте соединение.")
        sys.exit(1)
    except UserNotFoundError as e:
        print(f"Ошибка: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"Ошибка: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Неизвестная ошибка: {e}")
        sys.exit(1)


def handle_command(args):
    if args.command == "register":
        return register(args.username, args.password)
    elif args.command == "login":
        return login(args.username, args.password)
    elif args.command == "show-portfolio":
        return show_portfolio(args.base)
    elif args.command == "buy":
        return buy(args.currency, args.amount)
    elif args.command == "sell":
        return sell(args.currency, args.amount)
    elif args.command == "get-rate":
        return get_rate(args.cur_from, args.cur_to)
    elif args.command == "logout":
        return logout_user()
    elif args.command == "whoami":
        return get_current_user_info()
    elif args.command == "list-currencies":
        return list_supported_currencies()
    elif args.command == "update-rates":
        return handle_update_rates(args)
    elif args.command == "show-rates":
        return handle_show_rates(args)
    elif args.command == "parser-status":
        return handle_parser_status()
    elif args.command == "start-scheduler":
        return handle_start_scheduler()
    elif args.command == "stop-scheduler":
        return handle_stop_scheduler()
    else:
        return "Неизвестная команда"


def handle_update_rates(args) -> str:
    try:
        if args.force:
            result = updater.force_update()
        else:
            result = updater.run_update(args.source)

        if result["success"]:
            return (
                f"Обновление завершено успешно!\n"
                f"Всего курсов: {result['total_rates']}\n"
                f"Источников обработано: {result['sources_processed']}\n"
                f"Время: {result['timestamp']}"
            )
        else:
            return (
                f"Обновление завершено с ошибками\n"
                f"Получено курсов: {result['total_rates']}\n"
                f"Ошибок источников: {result['sources_failed']}\n"
                f"Проверьте логи для деталей"
            )
    except Exception as e:
        return f"Ошибка при обновлении курсов: {e}"


def handle_show_rates(args) -> str:
    from valutatrade_hub.parser_service.storage import RatesStorage
    storage = RatesStorage()
    cache_data = storage.load_current_rates()

    if not cache_data.get("pairs"):
        return (
            "Локальный кеш курсов пуст.\n"
            "Выполните 'update-rates', чтобы загрузить данные."
        )

    pairs = cache_data["pairs"]
    last_refresh = cache_data.get("last_refresh", "неизвестно")

    if args.currency:
        currency = args.currency.upper()
        filtered_pairs = {
            k: v for k, v in pairs.items()
            if currency in k
        }
        if not filtered_pairs:
            return f"Курс для '{currency}' не найден в кеше."
        pairs = filtered_pairs

    if args.top:
        sorted_pairs = sorted(
            pairs.items(),
            key=lambda x: x[1]["rate"],
            reverse=True
        )[:args.top]
        pairs = dict(sorted_pairs)

    result = []
    if args.verbose:
        result.append(f"Курсы из кеша (обновлено: {last_refresh})")
        result.append("=" * 50)

        for pair_key, pair_data in sorted(pairs.items()):
            rate = pair_data["rate"]
            updated = pair_data.get("updated_at", "неизвестно")
            source = pair_data.get("source", "неизвестно")

            result.append(f"{pair_key:12} {rate:>15.6f}")
            result.append(f"               обновлено: {updated}")
            result.append(f"               источник: {source}")
            result.append("-" * 50)
    else:
        result.append(f"Актуальные курсы (база: {args.base})")
        result.append("=" * 30)

        for pair_key, pair_data in sorted(pairs.items()):
            if args.base != "USD" and pair_key.endswith("_USD"):
                base_rate = next(
                    (p["rate"] for k, p in pairs.items()
                     if k == f"{args.base}_USD"),
                    None
                )
                if base_rate:
                    converted_rate = pair_data["rate"] / base_rate
                    display_key = pair_key.replace("_USD", f"_{args.base}")
                    result.append(f"{display_key:12} {converted_rate:>15.6f}")
                    continue

            result.append(f"{pair_key:12} {pair_data['rate']:>15.6f}")

    result.append(f"\nВсего пар: {len(pairs)}")
    return "\n".join(result)


def handle_parser_status() -> str:
    status = updater.get_status()

    result = []
    result.append("СТАТУС PARSER SERVICE")
    result.append("=" * 50)

    result.append("Конфигурация:")
    result.append(f"  Базовая валюта: {status['config']['base_currency']}")

    fiat_str = ", ".join(status['config']['fiat_currencies'])
    result.append(f"  Фиатные валюты: {fiat_str}")

    crypto_str = ", ".join(status['config']['crypto_currencies'])
    result.append(f"  Криптовалюты: {crypto_str}")

    api_status = "установлен" if status['config']['has_api_key'] else "отсутствует"
    result.append(f"  API ключ: {api_status}")

    result.append("\nСтатус кеша:")
    cache_exists = "существует" if status['cache_exists'] else "отсутствует"
    result.append(f"  Файл кеша: {cache_exists}")

    cache_valid = "актуален" if status['cache_valid'] else "устарел"
    result.append(f"  Актуальность: {cache_valid}")

    result.append(f"  Последнее обновление: {status['last_refresh'] or 'никогда'}")
    result.append(f"  Всего пар в кеше: {status['total_pairs']}")

    rates_size = (os.path.getsize('data/rates.json')
                  if os.path.exists('data/rates.json') else 0)
    history_size = (os.path.getsize('data/exchange_rates.json')
                    if os.path.exists('data/exchange_rates.json') else 0)

    result.append("\nФайлы данных:")
    result.append(f"  rates.json: {rates_size / 1024:.1f} KB")
    result.append(f"  exchange_rates.json: {history_size / 1024:.1f} KB")

    result.append("\nРекомендации:")
    if not status['config']['has_api_key']:
        result.append("  Добавьте EXCHANGERATE_API_KEY в .env файл")
    if not status['cache_exists'] or status['total_pairs'] == 0:
        result.append("  Выполните 'update-rates' для загрузки курсов")
    elif not status['cache_valid']:
        result.append("  Выполните 'update-rates' для обновления кеша")

    return "\n".join(result)


def handle_start_scheduler() -> str:
    try:
        scheduler.start()
        return (
            "Планировщик запущен\n"
            "Курсы будут автоматически обновляться каждый час\n"
            "Используйте 'stop-scheduler' для остановки"
        )
    except Exception as e:
        return f"Ошибка при запуске планировщика: {e}"


def handle_stop_scheduler() -> str:
    try:
        scheduler.stop()
        return "Планировщик остановлен"
    except Exception as e:
        return f"Ошибка при остановке планировщика: {e}"


if __name__ == "__main__":
    main()
