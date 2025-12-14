import functools
import logging
from datetime import datetime
from typing import Callable, Any


logger = logging.getLogger("valutatrade.actions")

def log_action(func: Callable) -> Callable:
    """Декоратор для логирования действий пользователя"""

    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        action = func.__name__.upper()
        username = "anonymous"
        try:
            from valutatrade_hub.core.usecases import current_user
            if current_user:
                username = current_user.username
        except (ImportError, AttributeError):
            pass

        log_message = f"{action} user='{username}'"

        if action in ['BUY', 'SELL'] and len(args) >= 2:
            currency = args[0] if len(args) > 0 else kwargs.get('currency', 'unknown')
            amount = args[1] if len(args) > 1 else kwargs.get('amount', 0)
            log_message += f" currency='{currency}' amount={amount}"
        elif action == 'REGISTER' and len(args) >= 2:
            username_arg = args[0] if len(args) > 0 else kwargs.get('username', 'unknown')
            log_message += f" new_user='{username_arg}'"
        elif action == 'LOGIN' and len(args) >= 2:
            username_arg = args[0] if len(args) > 0 else kwargs.get('username', 'unknown')
            log_message += f" attempt_user='{username_arg}'"

        try:
            result = func(*args, **kwargs)
            logger.info(f"{log_message} result=OK")
            return result
        except Exception as e:
            error_msg = str(e).replace("'", "")  # Убираем кавычки для удобства
            logger.error(f"{log_message} result=ERROR error='{error_msg}'")
            raise

    return wrapper
