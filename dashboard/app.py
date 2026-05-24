import dash
import dash_bootstrap_components as dbc
from sqlalchemy.engine import Engine

from dashboard.data import (
    load_daily_activity,
    load_overview,
    load_recent_attempts,
    load_submit_success,
    load_top_courses,
)
from dashboard.layout import build_layout


def create_app(engine: Engine) -> dash.Dash:
    app = dash.Dash(
        __name__,
        external_stylesheets=[dbc.themes.FLATLY],
        title="Grader Analytics",
    )

    overview = load_overview(engine)
    daily = load_daily_activity(engine)
    submit_success = load_submit_success(engine)
    top_courses = load_top_courses(engine)
    recent = load_recent_attempts(engine)

    app.layout = build_layout(overview, daily, submit_success, top_courses, recent)
    return app


if __name__ == "__main__":
    from dashboard.main import run

    run()
