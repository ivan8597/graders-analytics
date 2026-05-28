import logging
import time
from typing import Any

import requests

from config import API_CLIENT, API_CLIENT_KEY, API_URL

CONNECT_TIMEOUT = 10
READ_TIMEOUT = 120
MAX_RETRIES = 3
INITIAL_BACKOFF = 2
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


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
    last_error: Exception | None = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(
                API_URL,
                params=params,
                timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
            )
        except requests.RequestException as exc:
            last_error = exc
            logger.warning(
                "Попытка %s/%s: ошибка сети при обращении к API: %s",
                attempt,
                MAX_RETRIES,
                exc,
            )
        else:
            if response.status_code == 200:
                data = response.json()
                elapsed = time.perf_counter() - started_at
                logger.info(
                    "Скачивание данных из API завершилось за %.2f сек. "
                    "Получено записей: %s (попытка %s/%s)",
                    elapsed,
                    len(data),
                    attempt,
                    MAX_RETRIES,
                )
                return data

            last_error = requests.HTTPError(
                f"status_code={response.status_code}",
                response=response,
            )
            if response.status_code not in RETRYABLE_STATUS_CODES:
                logger.error("Ошибка доступа к API, status_code=%s", response.status_code)
                response.raise_for_status()

            logger.warning(
                "Попытка %s/%s: API вернул status_code=%s",
                attempt,
                MAX_RETRIES,
                response.status_code,
            )

        if attempt < MAX_RETRIES:
            delay = INITIAL_BACKOFF ** (attempt - 1)
            logger.info("Повтор через %s сек...", delay)
            time.sleep(delay)

    logger.error("Не удалось получить данные из API после %s попыток", MAX_RETRIES)
    if last_error is not None:
        raise last_error
    raise RuntimeError("Не удалось получить данные из API")
