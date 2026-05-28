import logging
import os
import time
from typing import Any

import psycopg2
from psycopg2.extras import execute_values

TABLE_NAME = "grader_statistics"


def init_database(connection: psycopg2.extensions.connection) -> None:
    sql_path = os.path.join("sql", "create_table.sql")
    with open(sql_path, encoding="utf-8") as sql_file:
        ddl = sql_file.read()

    with connection.cursor() as cursor:
        cursor.execute(ddl)
    connection.commit()


def load_to_database(
    records: list[dict[str, Any]],
    db_config: dict[str, str],
    *,
    source_count: int | None = None,
) -> None:
    logger = logging.getLogger("database")
    logger.info("Заполнение базы данных началось")
    started_at = time.perf_counter()
    skipped = (source_count - len(records)) if source_count is not None else None

    if not records:
        logger.info("Нет данных для загрузки в базу")
        if source_count is not None:
            logger.info(
                "Итог загрузки: получено из API=%s, загружено=0, пропущено при валидации=%s",
                source_count,
                skipped,
            )
        return

    connection = None
    inserted = 0
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
        inserted = len(records)

        elapsed = time.perf_counter() - started_at
        logger.info(
            "Заполнение базы данных завершилось за %.2f сек. Загружено записей: %s",
            elapsed,
            inserted,
        )
        if source_count is not None:
            logger.info(
                "Итог загрузки: получено из API=%s, загружено=%s, "
                "пропущено при валидации=%s, ошибок вставки=0",
                source_count,
                inserted,
                skipped,
            )
    except psycopg2.Error as exc:
        logger.error("Ошибка при работе с PostgreSQL: %s", exc)
        logger.error(
            "Откат транзакции. Не загружено записей: %s",
            len(records),
        )
        if source_count is not None:
            logger.error(
                "Итог загрузки: получено из API=%s, загружено=0, "
                "пропущено при валидации=%s, ошибок вставки=%s",
                source_count,
                skipped,
                len(records),
            )
        if connection is not None:
            connection.rollback()
        raise
    finally:
        if connection is not None:
            connection.close()
