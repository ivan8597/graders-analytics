import argparse
import ast
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Any
from urllib.parse import urlparse

import psycopg2
import requests
from psycopg2.extras import execute_values

from config import API_CLIENT, API_CLIENT_KEY, API_URL, LOGS_DIR, get_db_config, validate_config

TABLE_NAME = "grader_statistics"
REQUIRED_PASSBACK_FIELDS = (
    "oauth_consumer_key",
    "lis_result_sourcedid",
    "lis_outcome_service_url",
)
ALLOWED_ATTEMPT_TYPES = {"run", "submit"}


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


def fetch_statistics(start: str, end: str) -> list[dict[str, Any]]:
    logger = logging.getLogger("api")
    params = {
        "client": API_CLIENT,
        "client_key": API_CLIENT_KEY,
        "start": start,
        "end": end,
    }

    logger.info("Скачивание данных из API началось")
    started_at = time.perf_counter()

    try:
        response = requests.get(API_URL, params=params, timeout=300)
    except requests.RequestException as exc:
        logger.error("Ошибка при обращении к API: %s", exc)
        raise

    if response.status_code != 200:
        logger.error("Ошибка доступа к API, status_code=%s", response.status_code)
        response.raise_for_status()

    data = response.json()
    elapsed = time.perf_counter() - started_at
    logger.info(
        "Скачивание данных из API завершилось за %.2f сек. Получено записей: %s",
        elapsed,
        len(data),
    )
    return data


def parse_passback_params(raw_value: Any) -> dict[str, Any] | None:
    if raw_value is None:
        return None

    if isinstance(raw_value, dict):
        return raw_value

    if not isinstance(raw_value, str):
        return None

    try:
        parsed = ast.literal_eval(raw_value)
    except (SyntaxError, ValueError):
        return None

    if not isinstance(parsed, dict):
        return None

    return parsed


def is_valid_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def validate_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None

    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue

    return None


def normalize_is_correct(value: Any, attempt_type: str) -> bool | None:
    if attempt_type == "run":
        return None

    if value in (0, False):
        return False
    if value in (1, True):
        return True

    return None


def transform_record(record: dict[str, Any]) -> dict[str, Any] | None:
    logger = logging.getLogger("transform")

    user_id = record.get("lti_user_id")
    if not isinstance(user_id, str) or not user_id.strip():
        logger.warning("Пропущена запись: некорректный lti_user_id: %s", user_id)
        return None

    attempt_type = record.get("attempt_type")
    if attempt_type not in ALLOWED_ATTEMPT_TYPES:
        logger.warning(
            "Пропущена запись user_id=%s: некорректный attempt_type=%s",
            user_id,
            attempt_type,
        )
        return None

    passback = parse_passback_params(record.get("passback_params"))
    if passback is None:
        logger.warning(
            "Пропущена запись user_id=%s: не удалось разобрать passback_params",
            user_id,
        )
        return None

    for field in REQUIRED_PASSBACK_FIELDS:
        if field not in passback:
            logger.warning(
                "Пропущена запись user_id=%s: отсутствует поле %s в passback_params",
                user_id,
                field,
            )
            return None

    oauth_consumer_key = passback.get("oauth_consumer_key")
    lis_result_sourcedid = passback.get("lis_result_sourcedid")
    lis_outcome_service_url = passback.get("lis_outcome_service_url")

    if not isinstance(oauth_consumer_key, str):
        logger.warning(
            "Пропущена запись user_id=%s: oauth_consumer_key имеет неверный тип",
            user_id,
        )
        return None

    if not isinstance(lis_result_sourcedid, str) or not lis_result_sourcedid.strip():
        logger.warning(
            "Пропущена запись user_id=%s: некорректный lis_result_sourcedid",
            user_id,
        )
        return None

    if (
        not isinstance(lis_outcome_service_url, str)
        or not lis_outcome_service_url.strip()
        or not is_valid_url(lis_outcome_service_url)
    ):
        logger.warning(
            "Пропущена запись user_id=%s: некорректный lis_outcome_service_url",
            user_id,
        )
        return None

    created_at = validate_datetime(record.get("created_at"))
    if created_at is None:
        logger.warning(
            "Пропущена запись user_id=%s: некорректный created_at=%s",
            user_id,
            record.get("created_at"),
        )
        return None

    is_correct_raw = record.get("is_correct")
    if attempt_type == "run" and is_correct_raw is not None:
        logger.warning(
            "Пропущена запись user_id=%s: для run is_correct должен быть null",
            user_id,
        )
        return None

    if attempt_type == "submit" and is_correct_raw not in (0, 1, True, False):
        logger.warning(
            "Пропущена запись user_id=%s: для submit is_correct должен быть 0 или 1",
            user_id,
        )
        return None

    return {
        "user_id": user_id,
        "oauth_consumer_key": oauth_consumer_key,
        "lis_result_sourcedid": lis_result_sourcedid,
        "lis_outcome_service_url": lis_outcome_service_url,
        "is_correct": normalize_is_correct(is_correct_raw, attempt_type),
        "attempt_type": attempt_type,
        "created_at": created_at,
    }


def transform_records(raw_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    logger = logging.getLogger("transform")
    logger.info("Обработка данных началась")

    started_at = time.perf_counter()
    processed: list[dict[str, Any]] = []

    for record in raw_records:
        transformed = transform_record(record)
        if transformed is not None:
            processed.append(transformed)

    elapsed = time.perf_counter() - started_at
    skipped = len(raw_records) - len(processed)
    logger.info(
        "Обработка данных завершилась за %.2f сек. Готово к загрузке: %s, пропущено: %s",
        elapsed,
        len(processed),
        skipped,
    )
    return processed


def init_database(connection: psycopg2.extensions.connection) -> None:
    sql_path = os.path.join("sql", "create_table.sql")
    with open(sql_path, encoding="utf-8") as sql_file:
        ddl = sql_file.read()

    with connection.cursor() as cursor:
        cursor.execute(ddl)
    connection.commit()


def load_to_database(records: list[dict[str, Any]], db_config: dict[str, str]) -> None:
    logger = logging.getLogger("database")
    logger.info("Заполнение базы данных началось")
    started_at = time.perf_counter()

    if not records:
        logger.info("Нет данных для загрузки в базу")
        return

    connection = None
    try:
        connection = psycopg2.connect(**db_config)
        init_database(connection)

        values = [
            (
                record["user_id"],
                record["oauth_consumer_key"],
                record["lis_result_sourcedid"],
                record["lis_outcome_service_url"],
                record["is_correct"],
                record["attempt_type"],
                record["created_at"],
            )
            for record in records
        ]

        insert_query = f"""
            INSERT INTO {TABLE_NAME} (
                user_id,
                oauth_consumer_key,
                lis_result_sourcedid,
                lis_outcome_service_url,
                is_correct,
                attempt_type,
                created_at
            ) VALUES %s
        """

        with connection.cursor() as cursor:
            execute_values(cursor, insert_query, values)
        connection.commit()

        elapsed = time.perf_counter() - started_at
        logger.info(
            "Заполнение базы данных завершилось за %.2f сек. Загружено записей: %s",
            elapsed,
            len(records),
        )
    except psycopg2.Error as exc:
        logger.error("Ошибка при работе с PostgreSQL: %s", exc)
        if connection is not None:
            connection.rollback()
        raise
    finally:
        if connection is not None:
            connection.close()


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
