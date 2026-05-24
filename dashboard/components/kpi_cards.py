import dash_bootstrap_components as dbc
from dash import html


def _make_card(title: str, value: str) -> dbc.Col:
    return dbc.Col(
        dbc.Card(
            dbc.CardBody(
                [
                    html.Div(title, className="text-muted small"),
                    html.H3(value),
                ]
            ),
            className="shadow-sm",
        ),
        md=3,
        xs=6,
    )


def create_kpi_cards(overview: dict[str, float | int]) -> dbc.Row:
    return dbc.Row(
        [
            _make_card(
                "Всего попыток",
                f"{overview['total_attempts']:,}".replace(",", " "),
            ),
            _make_card(
                "Уникальных студентов",
                f"{overview['unique_users']:,}".replace(",", " "),
            ),
            _make_card(
                "Submit-попыток",
                f"{overview['submits']:,}".replace(",", " "),
            ),
            _make_card("Успешность submit, %", f"{overview['success_rate']}%"),
        ],
        className="g-3 mb-4",
    )
