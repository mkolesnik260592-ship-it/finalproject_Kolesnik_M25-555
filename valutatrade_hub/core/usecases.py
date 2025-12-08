from datetime import datetime
from valutatrade_hub.core.models import User, Wallet, Portfolio
from valutatrade_hub.core.utils import (
    load_users, save_users,
    load_portfolios, save_portfolios,
    load_rates, save_rates,
    find_user, next_user_id,
    validate_currency_code, validate_amount,
)


current_user: User | None = None

def register(username: str, password: str) -> str:
        if not username or not username.strip():
            raise ValueError("Имя не может быть пустым")
        if len(password) < 4:
            raise ValueError("Пароль должен содержать минимум 4 символа")
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
        portfolios.append({
            "user_id": user_id,
            "wallets": {}
        })
        save_portfolios(portfolios)
        return f"Пользователь '{username}' зарегистрирован (id={user_id})."

def login(username: str, password: str) -> str:
    users = load_users()
    u = find_user(users, username)
    if not u:
        return f"Ошибка: пользователь {username} не найден"
    user = User(
        u["user_id"], u["username"],
        hashed_password=u["hashed_password"],
        salt=u["salt"],
        registration_date=datetime.fromisoformat(u["registration_date"]),
    )
    if not user.verify_password(password):
        return "Неверный пароль"
    else:
        global current_user
        current_user = user
        return f"Вы вошли как '{username}'"


def show_portfolio(base: str = "USD") -> str:
    if current_user is None:
        return "Сначала выполните login"

    portfolios = load_portfolios()

    portfolio_data = None
    for p in portfolios:
        if p.get("user_id") == current_user.user_id:
            portfolio_data = p
            break

    if portfolio_data is None:
        return "Портфель не найден"

    wallets_dict = portfolio_data.get("wallets", {})
    if not wallets_dict:
        return "Портфель пуст"

    wallets = {}
    for code, wallet_data in wallets_dict.items():
        wallets[code] = Wallet(code, wallet_data.get("balance", 0.0))

    portfolio = Portfolio(current_user.user_id, wallets=wallets)
    total = portfolio.get_total_value(base_currency=base)

    result = f"Портфель пользователя '{current_user.username}' (база: {base}):\n"
    for code, wallet in wallets.items():
        temp_portfolio = Portfolio(current_user.user_id, wallets={code: wallet})
        value_in_base = temp_portfolio.get_total_value(base_currency=base)
        result += f"- {code}: {wallet.balance:.2f} → {value_in_base:.2f} {base}\n"

    result += "---------------------------------\n"
    result += f"ИТОГО: {total:.2f} {base}"
    return result

def buy(currency: str, amount: float) -> str:
    if current_user is None:
        return "Сначала выполните login"

    code = validate_currency_code(currency)
    amt = validate_amount(amount)

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

    if code not in wallets_dict:
        wallets_dict[code] = {"balance": 0.0}

    wallet = Wallet(code, wallets_dict[code].get("balance", 0.0))
    wallet.deposit(amt)
    wallets_dict[code] = {"balance": wallet.balance}

    save_portfolios(portfolios)

    return f"Покупка выполнена: {amt:.4f} {code}. Баланс: {wallet.balance:.4f} {code}"

def sell(currency: str, amount: float) -> str:
    if current_user is None:
        return "Сначала выполните login"

    code = validate_currency_code(currency)
    amt = validate_amount(amount)

    portfolios = load_portfolios()

    portfolio_data = None
    for p in portfolios:
        if p.get("user_id") == current_user.user_id:
            portfolio_data = p
            break

    if portfolio_data is None:
        return "Портфель не найден"

    wallets_dict = portfolio_data.get("wallets", {})

    if code not in wallets_dict:
        return f"У вас нет кошелька '{code}'"

    wallet = Wallet(code, wallets_dict[code].get("balance", 0.0))

    if amt > wallet.balance:
        return f"Недостаточно средств: доступно {wallet.balance:.4f} {code}, требуется {amt:.4f} {code}"

    wallet.withdraw(amt)
    wallets_dict[code] = {"balance": wallet.balance}

    save_portfolios(portfolios)

    return f"Продажа выполнена: {amt:.4f} {code}. Баланс: {wallet.balance:.4f} {code}"

def get_rate(cur_from: str, cur_to: str) -> str:
    from_code = validate_currency_code(cur_from)
    to_code = validate_currency_code(cur_to)

    rates = load_rates()
    key = f"{from_code}_{to_code}"

    # Заглушка курсов (пока нет Parser Service)
    default_rates = {
        "EUR_USD": 1.0786,
        "BTC_USD": 59337.21,
        "RUB_USD": 0.01016,
        "ETH_USD": 3720.00,
        "USD_EUR": 1.0 / 1.0786,
        "USD_BTC": 1.0 / 59337.21,
        "USD_RUB": 1.0 / 0.01016,
        "USD_ETH": 1.0 / 3720.00,
    }

    if key in rates and "rate" in rates[key]:
        rate_data = rates[key]
        rate = rate_data["rate"]
        updated_at = rate_data.get("updated_at", "неизвестно")
    elif key in default_rates:
        rate = default_rates[key]
        updated_at = datetime.now().isoformat()
        # Сохранить в rates.json
        if key not in rates:
            rates[key] = {}
        rates[key]["rate"] = rate
        rates[key]["updated_at"] = updated_at
        save_rates(rates)
    else:
        return f"Курс {from_code}→{to_code} недоступен. Повторите попытку позже."

    reverse_rate = 1.0 / rate if rate != 0 else 0

    return (
        f"Курс {from_code}→{to_code}: {rate:.8f} "
        f"(обновлено: {updated_at})\n"
        f"Обратный курс {to_code}→{from_code}: {reverse_rate:.8f}"
    )
