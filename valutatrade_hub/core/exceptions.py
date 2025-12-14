"""
Пользовательские исключения для валютного кошелька
"""


class InsufficientFundsError(Exception):
    def __init__(self, available: float, required: float, code: str):
        self.available = available
        self.required = required
        self.code = code
        message = (f"Недостаточно средств: доступно {available} {code}, "
                   f"требуется {required} {code}")
        super().__init__(message)


class CurrencyNotFoundError(Exception):
    def __init__(self, code: str):
        self.code = code
        message = f"Неизвестная валюта '{code}'"
        super().__init__(message)


class ApiRequestError(Exception):
    def __init__(self, reason: str):
        self.reason = reason
        message = f"Ошибка при обращении к внешнему API: {reason}"
        super().__init__(message)


class UserNotFoundError(Exception):
    def __init__(self, username: str = None, user_id: int = None):
        self.username = username
        self.user_id = user_id

        if username:
            message = f"Пользователь '{username}' не найден"
        elif user_id:
            message = f"Пользователь с ID {user_id} не найден"
        else:
            message = "Пользователь не найден"

        super().__init__(message)
