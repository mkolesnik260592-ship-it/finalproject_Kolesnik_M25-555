"""
CLI интерфейс приложения
"""

import argparse
import sys
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
    
    # Команда: register
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
    
    # Команда: login
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
    
    # Команда: show-portfolio
    portfolio_parser = subparsers.add_parser(
        "show-portfolio",
        help="Информация о кошельке"
    )
    portfolio_parser.add_argument(
        "--base",
        default="USD",
        help="Базовая валюта для конвертации (по умолчанию USD)"
    )
    
    # Команда: buy
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
    
    # Команда: sell
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
    
    # Команда: get-rate
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
    
    # Команда: logout
    subparsers.add_parser(
        "logout",
        help="Выход из системы"
    )
    
    # Команда: whoami
    subparsers.add_parser(
        "whoami",
        help="Показать текущего пользователя"
    )
    
    # Команда: list-currencies
    subparsers.add_parser(
        "list-currencies",
        help="Показать список поддерживаемых валют"
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    try:
        result = handle_command(args)
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
    """Обработка команд"""
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
    else:
        return "Неизвестная команда"


if __name__ == "__main__":
    main()
