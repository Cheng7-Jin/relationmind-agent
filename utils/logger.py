import os
import logging
from logging.handlers import TimedRotatingFileHandler

if not os.path.exists("logs"):
    os.makedirs("logs", exist_ok=True)

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    logger.propagate = False

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    file_handler = TimedRotatingFileHandler(
        "logs/agent.log",
        when="D",
        interval=1,
        encoding="utf-8",
        backupCount=7,
        delay=True
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger