from datetime import datetime
import hashlib
import secrets


class User:
    def __init__(self, user_id: int, username: str, password: str,
                 registration_date: datetime = None):
        self._user_id = user_id
        self._salt = secrets.token_urlsafe(8)
        password_salt = (password + self._salt).encode()
        self._hashed_password = hashlib.sha256(password_salt).hexdigest()
        self._username = username
        if registration_date:
            self._registration_date = registration_date
        else:
            self._registration_date = datetime.now()

    def verify_password(self, password: str) -> bool:
        hash = hashlib.sha256((password + self._salt).encode()).hexdigest()
        return hash == self._hashed_password

    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def username(self) -> str:
        return self._username

    @property
    def registration_date(self) -> datetime:
        return self._registration_date

    @username.setter
    def username(self, value: str) -> None:
        if not value or not value.strip():
            raise ValueError("Имя не может быть пустым")
        self._username = value

    def get_user_info(self) -> dict:
        return {
            "user_id": self.user_id,
            "username": self.username,
            "registration_date": self.registration_date.isoformat()
        }

    def change_password(self, new_password: str) -> None:
        if len(new_password) < 4:
            raise ValueError("Пароль должен быть не короче 4 символов")
        self._salt = secrets.token_urlsafe(8)
        new_password_salt = (new_password + self._salt).encode()
        self._hashed_password = hashlib.sha256(new_password_salt).hexdigest()


class Wallet:
    def __init__(self, currency_code: str, balance: float = 0.0):
        self.currency_code = currency_code
        self._balance = float(balance)

    @property
    def balance(self) -> float:
        return self._balance

    @balance.setter
    def balance(self, value: float) -> None:
        if value < 0:
            raise ValueError("Баланс не может быть отрицательным")
        if not isinstance(value, (int, float)):
            raise ValueError("Некорректный тип данных")
        self._balance = float(value)

    def deposit(self, amount: float) -> None:
        if amount <= 0:
            raise ValueError("Сумма должна быть положительной")
        self.balance += amount

    def withdraw(self, amount: float) -> None:
        if amount <= 0:
            raise ValueError("Сумма должна быть положительной")
        if amount > self.balance:
            raise ValueError(
                f'Недостаточно средств: доступно {self.balance}, требуется {amount}.'
            )
        self.balance -= amount

    def get_balance_info(self) -> dict:
        return {
            "currency_code": self.currency_code,
            "balance": self.balance
        }


class Portfolio:
    def __init__(self, user_id: int, wallets: dict[str, Wallet] = None):
        self._user_id = user_id
        self._wallets = wallets if wallets else {}

    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def wallets(self) -> dict[str, Wallet]:
        return self._wallets.copy()

    @property
    def user(self) -> User | None:
        return None

    def add_currency(self, currency_code: str) -> None:
        if currency_code in self._wallets:
            raise ValueError("Валюта уже добавлена")
        wallet = Wallet(currency_code, 0.0)
        self._wallets[currency_code] = wallet

    def get_wallet(self, currency_code: str) -> Wallet | None:
        if currency_code not in self._wallets:
            raise ValueError(f"Кошелек {currency_code} не найден")
        return self._wallets[currency_code]

    def get_total_value(self, base_currency: str = 'USD') -> float:

        exchange_rates = {
            "USD": 1.0,
            "EUR": 1.0786,
            "BTC": 59337.21,
            "RUB": 0.01016,
            "ETH": 3720.00
        }
        total = 0.0
        for currency_code, wallet in self._wallets.items():
            balance = wallet.balance
            if currency_code == base_currency:
                total += balance
            else:
                rate_to_usd = exchange_rates.get(currency_code, 0)
                if rate_to_usd == 0:
                    continue
                value_in_usd = balance * rate_to_usd
                if base_currency != "USD":
                    rate_from_usd = exchange_rates.get(base_currency, 1.0)
                    if rate_from_usd != 0:
                        value_in_base = value_in_usd / rate_from_usd
                    else:
                        value_in_base = 0
                else:
                    value_in_base = value_in_usd
                total += value_in_base
        return total
