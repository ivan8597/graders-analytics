import os

import dash
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
from dash import dash_table, dcc, html

from config import get_db_engine

from dashboard.data import (
    load_daily_activity,
    load_overview,
    load_recent_attempts,
    load_submit_success,
    load_top_courses,
)

DASH_HOST = os.getenv("DASH_HOST", "127.0.0.1")
DASH_PORT = int(os.getenv("DASH_PORT", "8050"))

engine = get_db_engine()
overview = load_overview(engine)
daily = load_daily_activity(engine)
submit_success = load_submit_success(engine)
top_courses = load_top_courses(engine)
recent = load_recent_attempts(engine)

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.FLATLY],
    title="Grader Analytics",
)

fig_activity = px.line(
    daily,
    x="day",
    y="attempts",
    color="attempt_type",
    markers=True,
    title="Попытки по дням",
    labels={"day": "Дата", "attempts": "Количество", "attempt_type": "Тип"},
)
fig_activity.update_layout(legend_title_text="Тип попытки", hovermode="x unified")

fig_submit = px.area(
    submit_success,
    x="day",
    y=["correct", "incorrect"],
    title="Submit: верные и неверные решения",
    labels={"day": "Дата", "value": "Количество", "variable": "Результат"},
)
name_map = {"correct": "Верно", "incorrect": "Неверно"}
fig_submit.for_each_trace(lambda trace: trace.update(name=name_map.get(trace.name, trace.name)))

fig_courses = px.bar(
    top_courses,
    x="attempts",
    y="course",
    orientation="h",
    title="Топ-10 курсов по активности",
    labels={"attempts": "Попытки", "course": "Курс"},
)
fig_courses.update_layout(yaxis={"categoryorder": "total ascending"}, height=420)

pie_data = daily.groupby("attempt_type", as_index=False)["attempts"].sum()
fig_types = px.pie(
    pie_data,
    names="attempt_type",
    values="attempts",
    title="Run vs Submit",
    hole=0.4,
)

kpi_cards = dbc.Row(
    [
        dbc.Col(
            dbc.Card(
                dbc.CardBody(
                    [
                        html.Div("Всего попыток", className="text-muted small"),
                        html.H3(f"{overview['total_attempts']:,}".replace(",", " ")),
                    ]
                ),
                className="shadow-sm",
            ),
            md=3,
            xs=6,
        ),
        dbc.Col(
            dbc.Card(
                dbc.CardBody(
                    [
                        html.Div("Уникальных студентов", className="text-muted small"),
                        html.H3(f"{overview['unique_users']:,}".replace(",", " ")),
                    ]
                ),
                className="shadow-sm",
            ),
            md=3,
            xs=6,
        ),
        dbc.Col(
            dbc.Card(
                dbc.CardBody(
                    [
                        html.Div("Submit-попыток", className="text-muted small"),
                        html.H3(f"{overview['submits']:,}".replace(",", " ")),
                    ]
                ),
                className="shadow-sm",
            ),
            md=3,
            xs=6,
        ),
        dbc.Col(
            dbc.Card(
                dbc.CardBody(
                    [
                        html.Div("Успешность submit, %", className="text-muted small"),
                        html.H3(f"{overview['success_rate']}%"),
                    ]
                ),
                className="shadow-sm",
            ),
            md=3,
            xs=6,
        ),
    ],
    className="g-3 mb-4",
)

recent_display = recent.copy()
recent_display["created_at"] = pd.to_datetime(recent_display["created_at"]).dt.strftime(
    "%Y-%m-%d %H:%M:%S"
)
recent_display["is_correct"] = recent_display["is_correct"].map(
    {True: "да", False: "нет", None: "—"}
)

app.layout = dbc.Container(
    [
        html.H2("Grader Analytics", className="mt-4 mb-1"),
        html.P(
            "Визуализация данных из PostgreSQL (grader_db)",
            className="text-muted mb-4",
        ),
        kpi_cards,
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
        dbc.Card(
            [
                dbc.CardHeader("Последние попытки"),
                dbc.CardBody(
                    dash_table.DataTable(
                        data=recent_display.to_dict("records"),
                        columns=[
                            {"name": "Студент", "id": "user_id"},
                            {"name": "Курс", "id": "course"},
                            {"name": "Тип", "id": "attempt_type"},
                            {"name": "Верно", "id": "is_correct"},
                            {"name": "Время", "id": "created_at"},
                        ],
                        page_size=10,
                        style_table={"overflowX": "auto"},
                        style_cell={"textAlign": "left", "padding": "8px"},
                        style_header={"fontWeight": "bold"},
                    )
                ),
            ],
            className="shadow-sm mb-5",
        ),
    ],
    fluid=True,
)


if __name__ == "__main__":
    app.run(host=DASH_HOST, port=DASH_PORT, debug=True)
