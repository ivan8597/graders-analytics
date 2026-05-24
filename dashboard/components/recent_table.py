import dash_bootstrap_components as dbc
import pandas as pd
from dash import dash_table


def create_recent_table(recent: pd.DataFrame) -> dbc.Card:
    recent_display = recent.copy()
    recent_display["created_at"] = pd.to_datetime(recent_display["created_at"]).dt.strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    recent_display["is_correct"] = recent_display["is_correct"].map(
        {True: "да", False: "нет", None: "—"}
    )

    return dbc.Card(
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
    )
