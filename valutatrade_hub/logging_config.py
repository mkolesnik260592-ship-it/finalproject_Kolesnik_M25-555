import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logging():
    """Настройка логирования для приложения"""

    logger = logging.getLogger("valutatrade.actions")

    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    file_handler = RotatingFileHandler(
        filename=os.path.join(log_dir, "actions.log"),
        maxBytes=10_485_760,  # 10 MB
        backupCount=5,
        encoding='utf-8'
    )

    formatter = logging.Formatter(
        '%(levelname)s %(asctime)s %(message)s',
        datefmt='%Y-%m-%dT%H:%M:%S'
    )
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)

    logger.propagate = False
    return logger
