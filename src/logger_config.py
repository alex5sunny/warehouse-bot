import logging
import logging.handlers
from pathlib import Path

from globs import BASE_PATH


def setup_logger(name, log_file=BASE_PATH / 'bot.log', level=logging.INFO):
    logger = logging.getLogger(name)
    logger.setLevel(level)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - '
        '%(message)s'
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    # logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
