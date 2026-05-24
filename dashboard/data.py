import pandas as pd
from sqlalchemy.engine import Engine


def load_overview(engine: Engine) -> dict[str, float | int]:
    query = """
        SELECT
            COUNT(*) AS total_attempts,
            COUNT(DISTINCT user_id) AS unique_users,
            COUNT(*) FILTER (WHERE attempt_type = 'submit') AS submits,
            COUNT(*) FILTER (WHERE attempt_type = 'submit' AND is_correct = TRUE) AS correct_submits
        FROM grader_statistics;
    """
    row = pd.read_sql(query, engine).iloc[0]

    success_rate = 0.0
    if row["submits"] > 0:
        success_rate = round(100 * row["correct_submits"] / row["submits"], 1)

    return {
        "total_attempts": int(row["total_attempts"]),
        "unique_users": int(row["unique_users"]),
        "submits": int(row["submits"]),
        "success_rate": success_rate,
    }


def load_daily_activity(engine: Engine) -> pd.DataFrame:
    query = """
        SELECT
            DATE(created_at) AS day,
            attempt_type,
            COUNT(*) AS attempts
        FROM grader_statistics
        GROUP BY DATE(created_at), attempt_type
        ORDER BY day;
    """
    return pd.read_sql(query, engine)


def load_submit_success(engine: Engine) -> pd.DataFrame:
    query = """
        SELECT
            DATE(created_at) AS day,
            COUNT(*) FILTER (WHERE is_correct = TRUE) AS correct,
            COUNT(*) FILTER (WHERE is_correct = FALSE) AS incorrect
        FROM grader_statistics
        WHERE attempt_type = 'submit'
        GROUP BY DATE(created_at)
        ORDER BY day;
    """
    return pd.read_sql(query, engine)


def load_top_courses(engine: Engine, limit: int = 10) -> pd.DataFrame:
    query = f"""
        SELECT
            split_part(lis_result_sourcedid, ':', 2) AS course,
            COUNT(*) AS attempts
        FROM grader_statistics
        GROUP BY course
        ORDER BY attempts DESC
        LIMIT {int(limit)};
    """
    return pd.read_sql(query, engine)


def load_recent_attempts(engine: Engine, limit: int = 20) -> pd.DataFrame:
    query = f"""
        SELECT
            user_id,
            split_part(lis_result_sourcedid, ':', 2) AS course,
            attempt_type,
            is_correct,
            created_at
        FROM grader_statistics
        ORDER BY created_at DESC
        LIMIT {int(limit)};
    """
    return pd.read_sql(query, engine)
