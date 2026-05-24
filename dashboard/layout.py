import dash_bootstrap_components as dbc
import pandas as pd
from dash import dcc, html

from dashboard.components.figures import (
    create_activity_figure,
    create_courses_figure,
    create_submit_figure,
    create_types_figure,
)
from dashboard.components.kpi_cards import create_kpi_cards
from dashboard.components.recent_table import create_recent_table


def build_layout(
    overview: dict[str, float | int],
    daily: pd.DataFrame,
    submit_success: pd.DataFrame,
    top_courses: pd.DataFrame,
    recent: pd.DataFrame,
) -> dbc.Container:
    fig_activity = create_activity_figure(daily)
    fig_types = create_types_figure(daily)
    fig_submit = create_submit_figure(submit_success)
    fig_courses = create_courses_figure(top_courses)

    return dbc.Container(
        [
            html.H2("Grader Analytics", className="mt-4 mb-1"),
            html.P(
                "Визуализация данных из PostgreSQL (grader_db)",
                className="text-muted mb-4",
            ),
            create_kpi_cards(overview),
            dbc.Row(
                [
                    dbc.Col(dcc.Graph(figure=fig_activity), md=8, xs=12),
                    dbc.Col(dcc.Graph(figure=fig_types), md=4, xs=12),
                ],
                className="g-3 mb-3",
            ),
            dbc.Row(
                [
                    dbc.Col(dcc.Graph(figure=fig_submit), md=7, xs=12),
                    dbc.Col(dcc.Graph(figure=fig_courses), md=5, xs=12),
                ],
                className="g-3 mb-3",
            ),
            create_recent_table(recent),
        ],
        fluid=True,
    )
