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


def normalize_is_correct(value: Any, attempt_type: str) -> bool | None:
    if attempt_type == "run":
        return None

    if value in (0, False):
        return False
    if value in (1, True):
        return True

    return None
