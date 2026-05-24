import argparse
import logging

from config import get_db_config, validate_config
from core.fetcher import fetch_statistics
from core.loader import load_to_database
from core.transformer import transform_records
from utils.logging_setup import setup_logging


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Загрузка статистики грейдера из API в PostgreSQL"
    )
    parser.add_argument(
        "--start",
        default="2023-04-01 12:46:47.860798",
        help="Дата и время начала выборки (UTC)",
    )
    parser.add_argument(
        "--end",
        default="2023-05-31 23:59:59.999999",
        help="Дата и время окончания выборки (UTC)",
    )
    return parser.parse_args()


def main() -> None:
    validate_config()
    setup_logging()
    logger = logging.getLogger("main")
    args = parse_args()

    logger.info("Скрипт запущен")
    logger.info("Период выборки: %s — %s", args.start, args.end)

    try:
        raw_records = fetch_statistics(args.start, args.end)
        processed_records = transform_records(raw_records)
        db_config = get_db_config()
        load_to_database(processed_records, db_config)
    except Exception as exc:
        logger.exception("Скрипт завершился с ошибкой: %s", exc)
        raise

    logger.info("Скрипт успешно завершён")


if __name__ == "__main__":
    main()
