import logging
import os
from datetime import datetime, timedelta

from config import LOGS_DIR


def setup_logging(logs_dir: str = LOGS_DIR) -> None:
    os.makedirs(logs_dir, exist_ok=True)
    cleanup_old_logs(logs_dir)

    log_filename = datetime.now().strftime("%Y-%m-%d") + ".log"
    log_path = os.path.join(logs_dir, log_filename)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
            logging.StreamHandler(),
        ],
        force=True,
    )


def cleanup_old_logs(logs_dir: str, keep_days: int = 3) -> None:
    if not os.path.isdir(logs_dir):
        return

    cutoff_date = datetime.now().date() - timedelta(days=keep_days - 1)
    for filename in os.listdir(logs_dir):
        if not filename.endswith(".log"):
            continue

        date_part = filename.removesuffix(".log")
        try:
            log_date = datetime.strptime(date_part, "%Y-%m-%d").date()
        except ValueError:
            continue

        if log_date < cutoff_date:
            os.remove(os.path.join(logs_dir, filename))
