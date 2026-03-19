import logging
import sys

from keep_alive.config import APP_LOGGER_NAME
from keep_alive.paths import LOG_FILE, ensure_runtime_dir


def setup_logging(daemon_mode: bool = False) -> logging.Logger:
    ensure_runtime_dir()

    handlers: list[logging.Handler] = [logging.FileHandler(LOG_FILE, encoding="utf-8")]
    if not daemon_mode:
        handlers.insert(0, logging.StreamHandler(sys.stdout))

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s │ %(levelname)-7s │ %(message)s",
        datefmt="%H:%M:%S",
        handlers=handlers,
        force=True,
    )
    return logging.getLogger(APP_LOGGER_NAME)


def get_logger() -> logging.Logger:
    return logging.getLogger(APP_LOGGER_NAME)
