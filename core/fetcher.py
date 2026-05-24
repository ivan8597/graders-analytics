import logging
import time
from typing import Any

import requests

from config import API_CLIENT, API_CLIENT_KEY, API_URL


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
