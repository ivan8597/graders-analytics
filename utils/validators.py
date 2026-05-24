import ast
from datetime import datetime
from typing import Any
from urllib.parse import urlparse

REQUIRED_PASSBACK_FIELDS = (
    "oauth_consumer_key",
    "lis_result_sourcedid",
    "lis_outcome_service_url",
)
ALLOWED_ATTEMPT_TYPES = {"run", "submit"}


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


def validate_passback(
    passback: dict[str, Any] | None,
) -> tuple[tuple[str, str, str] | None, str | None]:
    if passback is None:
        return None, "не удалось разобрать passback_params"

    for field in REQUIRED_PASSBACK_FIELDS:
        if field not in passback:
            return None, f"отсутствует поле {field} в passback_params"

    oauth_consumer_key = passback.get("oauth_consumer_key")
    lis_result_sourcedid = passback.get("lis_result_sourcedid")
    lis_outcome_service_url = passback.get("lis_outcome_service_url")

    if not isinstance(oauth_consumer_key, str):
        return None, "oauth_consumer_key имеет неверный тип"

    if not isinstance(lis_result_sourcedid, str) or not lis_result_sourcedid.strip():
        return None, "некорректный lis_result_sourcedid"

    if (
        not isinstance(lis_outcome_service_url, str)
        or not lis_outcome_service_url.strip()
        or not is_valid_url(lis_outcome_service_url)
    ):
        return None, "некорректный lis_outcome_service_url"

    return (oauth_consumer_key, lis_result_sourcedid, lis_outcome_service_url), None


def validate_is_correct(
    value: Any, attempt_type: str
) -> tuple[bool | None, str | None]:
    if attempt_type == "run":
        if value is not None:
            return None, "для run is_correct должен быть null"
        return None, None

    if value not in (0, 1, True, False):
        return None, "для submit is_correct должен быть 0 или 1"

    if value in (0, False):
        return False, None
    return True, None
