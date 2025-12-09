from datetime import datetime, timedelta
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
    global current_user
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
        current_user = user
        return f"Вы вошли как '{username}'"


def show_portfolio(base: str = "USD") -> str:
    if current_user == None:
        return "Сначала введите логин"
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
        temp_portfolio = Portfolio(current_user.user_id, wallets={code: wallet})
        value_in_base = temp_portfolio.get_total_value(base_currency=base)
        result += f"- {code}: {wallet.balance:.2f} → {value_in_base:.2f} {base}\n"
    result += f"---------------------------------\n"
    result += f"ИТОГО: {total:.2f} {base}"
    return result

def buy(currency: str, amount: float) -> str:
    if current_user is None:
        return "Сначала выполните login"

    code = validate_currency_code(currency)
    amt = validate_amount(amount)

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
        }

        if key in rates and "rate" in rates[key]:
            rate = rates[key]["rate"]
        elif key in default_rates:
            rate = default_rates[key]
        else:
            return f"Не удалось получить курс для {code}→USD"

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

    if code not in wallets_dict:
        wallets_dict[code] = {"balance": 0.0}

    wallet = Wallet(code, wallets_dict[code].get("balance", 0.0))
    old_balance = wallet.balance
    wallet.deposit(amt)
    wallets_dict[code] = {"balance": wallet.balance}

    save_portfolios(portfolios)

    return (
    f"Покупка выполнена: {amt:.4f} {code} по курсу {rate:.2f} USD/{code}\n"
    f"Изменения в портфеле:\n"
    f"- {code}: было {old_balance:.4f} → стало {wallet.balance:.4f}\n"
    f"Оценочная стоимость покупки: {cost_usd:,.2f} USD"
)

def sell(currency: str, amount: float) -> str:
    if current_user is None:
        return "Сначала выполните login"

    code = validate_currency_code(currency)
    amt = validate_amount(amount)

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
        }

        if key in rates and "rate" in rates[key]:
            rate = rates[key]["rate"]
        elif key in default_rates:
            rate = default_rates[key]
        else:
            return f"Не удалось получить курс для {code}→USD"

    revenue_usd = amt * rate

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
        return "Кошелек не существует"
    wallet = Wallet(code, wallets_dict[code].get("balance", 0.0))
    if wallet.balance < revenue_usd:
        return "Недостаточно средств"

    old_balance = wallet.balance
    wallet.withdraw(amt)
    wallets_dict[code] = {"balance": wallet.balance}

    save_portfolios(portfolios)

    return (
    f"Продажа выполнена: {amt:.4f} {code} по курсу {rate:.2f} USD/{code}\n"
    f"Изменения в портфеле:\n"
    f"- {code}: было {old_balance:.4f} → стало {wallet.balance:.4f}\n"
    f"Оценочная стоимость выручки: {revenue_usd:,.2f} USD"
)

def get_rate(cur_from: str, cur_to: str) -> str:
    pass
