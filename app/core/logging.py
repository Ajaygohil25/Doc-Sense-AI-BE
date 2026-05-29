import logging
from logging.handlers import RotatingFileHandler
import os

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE_PATH = os.path.join(LOG_DIR, "app.log")

formatter = logging.Formatter(
    "[%(asctime)s] [%(levelname)s] [%(name)s] - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

handler = RotatingFileHandler(LOG_FILE_PATH, maxBytes=5_000_000, backupCount=5)
handler.setFormatter(formatter)
handler.setLevel(logging.INFO)

# Shared root logger
logger = logging.getLogger("app")
logger.setLevel(logging.INFO)
logger.addHandler(handler)
logger.propagate = False  # Avoid duplicate logs if using uvicorn/gunicorn

def get_logger(name: str = None):
    return logger if name is None else logger.getChild(name)
