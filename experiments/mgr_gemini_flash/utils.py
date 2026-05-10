import logging
import sys
import os

# Define log path relative to the data volume
LOG_FILE_PATH = os.getenv("LOG_FILE", "/app/data/finance.log")

logger = logging.getLogger("finance_track")
logger.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# Fixed: Redirecting log file to a writable directory
file_handler = logging.FileHandler(LOG_FILE_PATH, encoding="utf-8")
file_handler.setFormatter(formatter)

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)