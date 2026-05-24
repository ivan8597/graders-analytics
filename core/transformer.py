import logging
import time
from typing import Any

from utils.validators import (
    ALLOWED_ATTEMPT_TYPES,
    REQUIRED_PASSBACK_FIELDS,
    is_valid_url,
    normalize_is_correct,
    parse_passback_params,
    validate_datetime,
)


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
