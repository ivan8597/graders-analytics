import logging
import time
from typing import Any

from utils.validators import (
    ALLOWED_ATTEMPT_TYPES,
    parse_passback_params,
    validate_datetime,
    validate_is_correct,
    validate_passback,
)

logger = logging.getLogger("transform")


def transform_record(record: dict[str, Any]) -> dict[str, Any] | None:
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
    passback_fields, passback_error = validate_passback(passback)
    if passback_fields is None:
        logger.warning(
            "Пропущена запись user_id=%s: %s",
            user_id,
            passback_error,
        )
        return None

    oauth_consumer_key, lis_result_sourcedid, lis_outcome_service_url = passback_fields

    created_at = validate_datetime(record.get("created_at"))
    if created_at is None:
        logger.warning(
            "Пропущена запись user_id=%s: некорректный created_at=%s",
            user_id,
            record.get("created_at"),
        )
        return None

    is_correct, is_correct_error = validate_is_correct(
        record.get("is_correct"), attempt_type
    )
    if is_correct_error is not None:
        logger.warning(
            "Пропущена запись user_id=%s: %s",
            user_id,
            is_correct_error,
        )
        return None

    return {
        "user_id": user_id,
        "oauth_consumer_key": oauth_consumer_key,
        "lis_result_sourcedid": lis_result_sourcedid,
        "lis_outcome_service_url": lis_outcome_service_url,
        "is_correct": is_correct,
        "attempt_type": attempt_type,
        "created_at": created_at,
    }


def transform_records(raw_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
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
