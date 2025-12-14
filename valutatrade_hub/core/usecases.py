"""
Сценарии использования (бизнес-логика) приложения
"""

from datetime import datetime
from typing import Optional
from .models import User, Wallet, Portfolio
from .utils import (
    load_users, save_users,
    load_portfolios, save_portfolios,
    load_rates, find_user_by_id,
    find_user, next_user_id,
    validate_currency_code, validate_amount, load_session,
    save_session, clear_session,
    should_refresh_rates, get_currency_display_info
)
from .exceptions import (
    InsufficientFundsError, CurrencyNotFoundError,
    ApiRequestError, UserNotFoundError
)
from .currencies import get_currency
from ..decorators import log_action
from ..infra.settings import SettingsLoader


current_user: Optional[User] = None

session = load_session()
if session and "user_id" in session:
    users = load_users()
    user_data = find_user_by_id(users, session["user_id"])
    if user_data:
        current_user = User(
            user_data["user_id"], user_data["username"],
            hashed_password=user_data["hashed_password"],
            salt=user_data["salt"],
            registration_date=datetime.fromisoformat(user_data["registration_date"]),
        )


@log_action
def register(username: str, password: str) -> str:
    if not username or not username.strip():
        raise ValueError("Имя не может быть пустым")

    settings = SettingsLoader()
    min_password_length = settings.get("min_password_length", 4)

    if len(password) < min_password_length:
        raise ValueError(f"Пароль должен быть минимум {min_password_length} символа")

    users = load_users()
    if find_user(users, username):
        raise ValueError(f'Имя {username} занято')

    user_id = next_user_id(users)
    user = User(user_id, username, password=password)

    users.append({
        "user_id": user.user_id,
        "username": user.username,
        "hashed_password": user.hashed_password,
        "salt": user.salt,
        "registration_date": user.registration_date.isoformat()
    })
    save_users(users)

    portfolios = load_portfolios()
    initial_balance = settings.get("initial_usd_balance", 1000.0)

    portfolios.append({
        "user_id": user_id,
        "wallets": {"USD": {"balance": initial_balance}}
    })
    save_portfolios(portfolios)

    return (f"Пользователь '{username}' зарегистрирован (id={user_id}). "
            f"Начальный баланс: {initial_balance:.2f} USD")


@log_action
def login(username: str, password: str) -> str:
    global current_user

    users = load_users()
    user_data = find_user(users, username)
    if not user_data:
        raise UserNotFoundError(username=username)

    user = User(
        user_data["user_id"], user_data["username"],
        hashed_password=user_data["hashed_password"],
        salt=user_data["salt"],
        registration_date=datetime.fromisoformat(user_data["registration_date"]),
    )

    if not user.verify_password(password):
        raise ValueError("Неверный пароль")

    current_user = user
    save_session(user.user_id, user.username)

    return f"Вы вошли как '{username}'"


@log_action
def buy(currency: str, amount: float) -> str:
    global current_user

    if current_user is None:
        raise ValueError("Сначала выполните login")

    code = validate_currency_code(currency)
    amt = validate_amount(amount)

    currency_obj = get_currency(code)

    rates = load_rates()
    key = f"{code}_USD"

    if code == "USD":
        rate = 1.0
    else:
        default_rates = {
            "EUR_USD": 1.0786,
            "BTC_USD": 59337.21,
            "RUB_USD": 0.01016,
            "ETH_USD": 3720.00,
            "GBP_USD": 1.2589,
            "JPY_USD": 0.0064,
        }

        if key in rates and "rate" in rates[key]:
            rate = rates[key]["rate"]
        elif key in default_rates:
            rate = default_rates[key]
        else:
            raise ApiRequestError(f"Не удалось получить курс для {code}→USD")

    cost_usd = amt * rate

    portfolios = load_portfolios()
    portfolio_data = None

    for p in portfolios:
        if p.get("user_id") == current_user.user_id:
            portfolio_data = p
            break

    if portfolio_data is None:
        portfolio_data = {"user_id": current_user.user_id, "wallets": {}}
        portfolios.append(portfolio_data)

    wallets_dict = portfolio_data.get("wallets", {})

    if "USD" not in wallets_dict:
        raise InsufficientFundsError(available=0.0, required=cost_usd, code="USD")

    usd_wallet = Wallet("USD", wallets_dict["USD"].get("balance", 0.0))

    if usd_wallet.balance < cost_usd:
        raise InsufficientFundsError(
            available=usd_wallet.balance,
            required=cost_usd,
            code="USD"
        )

    old_usd_balance = usd_wallet.balance

    usd_wallet.withdraw(cost_usd)
    wallets_dict["USD"] = {"balance": usd_wallet.balance}

    if code not in wallets_dict:
        wallets_dict[code] = {"balance": 0.0}

    target_wallet = Wallet(code, wallets_dict[code].get("balance", 0.0))
    old_target_balance = target_wallet.balance
    target_wallet.deposit(amt)
    wallets_dict[code] = {"balance": target_wallet.balance}

    save_portfolios(portfolios)

    return (
        f"Покупка выполнена: {amt:.4f} {code} ({currency_obj.name}) "
        f"по курсу {rate:.4f} USD/{code}\n"
        f"Изменения в портфеле:\n"
        f"- USD: было {old_usd_balance:.2f} → стало {usd_wallet.balance:.2f}\n"
        f"- {code}: было {old_target_balance:.4f} → стало {target_wallet.balance:.4f}\n"
        f"Стоимость покупки: {cost_usd:,.2f} USD"
    )


@log_action
def sell(currency: str, amount: float) -> str:
    global current_user

    if current_user is None:
        raise ValueError("Сначала выполните login")

    code = validate_currency_code(currency)
    amt = validate_amount(amount)

    currency_obj = get_currency(code)

    rates = load_rates()
    key = f"{code}_USD"

    if code == "USD":
        rate = 1.0
    else:
        default_rates = {
            "EUR_USD": 1.0786,
            "BTC_USD": 59337.21,
            "RUB_USD": 0.01016,
            "ETH_USD": 3720.00,
            "GBP_USD": 1.2589,
            "JPY_USD": 0.0064,
        }

        if key in rates and "rate" in rates[key]:
            rate = rates[key]["rate"]
        elif key in default_rates:
            rate = default_rates[key]
        else:
            raise ApiRequestError(f"Не удалось получить курс для {code}→USD")

    revenue_usd = amt * rate

    portfolios = load_portfolios()
    portfolio_data = None

    for p in portfolios:
        if p.get("user_id") == current_user.user_id:
            portfolio_data = p
            break

    if portfolio_data is None:
        raise ValueError("Портфель не найден")

    wallets_dict = portfolio_data.get("wallets", {})

    if code not in wallets_dict:
        raise InsufficientFundsError(available=0.0, required=amt, code=code)

    wallet = Wallet(code, wallets_dict[code].get("balance", 0.0))

    if wallet.balance < amt:
        raise InsufficientFundsError(
            available=wallet.balance,
            required=amt,
            code=code
        )

    if "USD" not in wallets_dict:
        wallets_dict["USD"] = {"balance": 0.0}

    usd_wallet = Wallet("USD", wallets_dict["USD"].get("balance", 0.0))

    old_balance = wallet.balance
    old_usd_balance = usd_wallet.balance

    wallet.withdraw(amt)
    wallets_dict[code] = {"balance": wallet.balance}

    usd_wallet.deposit(revenue_usd)
    wallets_dict["USD"] = {"balance": usd_wallet.balance}

    save_portfolios(portfolios)

    return (
        f"Продажа выполнена: {amt:.4f} {code} ({currency_obj.name}) "
        f"по курсу {rate:.4f} USD/{code}\n"
        f"Изменения в портфеле:\n"
        f"- {code}: было {old_balance:.4f} → стало {wallet.balance:.4f}\n"
        f"- USD: было {old_usd_balance:.2f} → стало {usd_wallet.balance:.2f}\n"
        f"Выручка от продажи: {revenue_usd:,.2f} USD"
    )


@log_action
def get_rate(cur_from: str, cur_to: str) -> str:
    from_curr = validate_currency_code(cur_from)
    to_curr = validate_currency_code(cur_to)

    if from_curr == to_curr:
        return f"Курс {from_curr} -> {to_curr}: 1.0"

    from_currency = get_currency(from_curr)
    to_currency = get_currency(to_curr)

    rates = load_rates()
    key = f"{from_curr}_{to_curr}"

    if should_refresh_rates():
        pass

    if key in rates:
        rate_data = rates[key]
        rate = rate_data["rate"]
        updated = rate_data["updated_at"]

        reverse_rate = 1.0 / rate if rate != 0 else 0

        return (
            f"Курс {from_curr}→{to_curr}: {rate:.6f}\n"
            f"{from_currency.get_display_info()}\n"
            f"{to_currency.get_display_info()}\n"
            f"Обратный курс {to_curr}→{from_curr}: {reverse_rate:.6f}\n"
            f"(обновлено: {updated})"
        )

    key2 = f"{to_curr}_{from_curr}"
    if key2 in rates:
        rate_data = rates[key2]
        reverse_rate = rate_data["rate"]
        updated = rate_data["updated_at"]

        rate = 1.0 / reverse_rate if reverse_rate != 0 else 0

        return (
            f"Курс {from_curr}→{to_curr}: {rate:.6f}\n"
            f"{from_currency.get_display_info()}\n"
            f"{to_currency.get_display_info()}\n"
            f"Обратный курс {to_curr}→{from_curr}: {reverse_rate:.6f}\n"
            f"(обновлено: {updated})"
        )

    default_rates = {
        "USD": 1.0,
        "EUR": 1.0786,
        "BTC": 59337.21,
        "RUB": 0.01016,
        "ETH": 3720.00,
        "GBP": 1.2589,
        "JPY": 0.0064,
    }

    from_to_usd = default_rates.get(from_curr)
    to_to_usd = default_rates.get(to_curr)

    if from_to_usd is not None and to_to_usd is not None:
        rate = from_to_usd / to_to_usd
        reverse_rate = to_to_usd / from_to_usd

        return (
            f"Курс {from_curr}→{to_curr}: {rate:.6f} (расчетный)\n"
            f"{from_currency.get_display_info()}\n"
            f"{to_currency.get_display_info()}\n"
            f"Обратный курс {to_curr}→{from_curr}: {reverse_rate:.6f}"
        )

    raise ApiRequestError(f"Курс {from_curr}→{to_curr} недоступен")


def show_portfolio(base: str = "USD") -> str:
    if current_user is None:
        return "Сначала введите логин"

    try:
        base = validate_currency_code(base)
    except CurrencyNotFoundError:
        return f"Неизвестная базовая валюта: {base}"

    portfolios = load_portfolios()
    portfolio_data = None

    for p in portfolios:
        if p.get("user_id") == current_user.user_id:
            portfolio_data = p
            break

    if portfolio_data is None:
        return "Портфель не найден"

    if not portfolio_data.get("wallets") or len(portfolio_data.get("wallets", {})) == 0:
        return "Портфель пуст"

    wallets_dict = portfolio_data.get("wallets", {})
    wallets = {}

    for code, wallet_data in wallets_dict.items():
        wallets[code] = Wallet(code, wallet_data.get("balance", 0.0))

    portfolio = Portfolio(current_user.user_id, wallets=wallets)
    total = portfolio.get_total_value(base_currency=base)

    result = f"Портфель пользователя '{current_user.username}' (база: {base}):\n"

    for code, wallet in wallets.items():
        try:
            currency_info = get_currency_display_info(code)
        except CurrencyNotFoundError:
            currency_info = f"[UNKNOWN] {code}"

        temp_portfolio = Portfolio(current_user.user_id, wallets={code: wallet})
        value_in_base = temp_portfolio.get_total_value(base_currency=base)

        result += f"- {currency_info}\n"
        result += f"  Баланс: {wallet.balance:.4f} {code} → "
        result += f"{value_in_base:.2f} {base}\n"

    result += "---------------------------------\n"
    result += f"ИТОГО: {total:.2f} {base}"

    return result


def logout_user() -> str:
    global current_user
    if current_user:
        username = current_user.username
        current_user = None
        clear_session()
        return f"Вы вышли из системы. До свидания, {username}!"
    else:
        return "Вы не вошли в систему"


def get_current_user_info() -> str:
    if current_user:
        return (f"Текущий пользователь: {current_user.username} "
                f"(id={current_user.user_id})")
    else:
        return "Вы не вошли в систему"


def list_supported_currencies() -> str:
    from .utils import get_supported_currencies_list

    currencies = get_supported_currencies_list()
    result = "Поддерживаемые валюты:\n"

    for code in currencies:
        try:
            currency = get_currency(code)
            result += f"- {currency.get_display_info()}\n"
        except CurrencyNotFoundError:
            result += f"- {code} (информация недоступна)\n"

    return result
