import plotly.express as px
import pandas as pd


def create_activity_figure(daily: pd.DataFrame):
    fig = px.line(
        daily,
        x="day",
        y="attempts",
        color="attempt_type",
        markers=True,
        title="Попытки по дням",
        labels={"day": "Дата", "attempts": "Количество", "attempt_type": "Тип"},
    )
    fig.update_layout(legend_title_text="Тип попытки", hovermode="x unified")
    return fig


def create_submit_figure(submit_success: pd.DataFrame):
    fig = px.area(
        submit_success,
        x="day",
        y=["correct", "incorrect"],
        title="Submit: верные и неверные решения",
        labels={"day": "Дата", "value": "Количество", "variable": "Результат"},
    )
    name_map = {"correct": "Верно", "incorrect": "Неверно"}
    fig.for_each_trace(lambda trace: trace.update(name=name_map.get(trace.name, trace.name)))
    return fig


def create_courses_figure(top_courses: pd.DataFrame):
    fig = px.bar(
        top_courses,
        x="attempts",
        y="course",
        orientation="h",
        title="Топ-10 курсов по активности",
        labels={"attempts": "Попытки", "course": "Курс"},
    )
    fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=420)
    return fig


def create_types_figure(daily: pd.DataFrame):
    pie_data = daily.groupby("attempt_type", as_index=False)["attempts"].sum()
    return px.pie(
        pie_data,
        names="attempt_type",
        values="attempts",
        title="Run vs Submit",
        hole=0.4,
    )
