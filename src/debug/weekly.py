
import pandas as pd
import numpy as np
import calendar
import streamlit as st
from datetime import datetime, timedelta

from src.pages.team import load_team_members
from src.pages.projects import load_projects
from src.pages.boost import generate_weeks

YEAR = 2025
MONTHS = [
    'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
    'Julio', 'Agosto', 'Setiembre', 'Octubre', 'Noviembre', 'Diciembre'
]


# Team members
load_team_members()
team_members = st.session_state.team_data
team_members_names = team_members['Nombre'].tolist()


def get_month(week_start, week_end):
    month = week_start.month
    if week_start.year != YEAR:
        month = week_end.month
    return month


def compute_month_business_days(month):
    return len(pd.date_range(
        start=pd.Timestamp(year=YEAR, month=month, day=1),
        end=pd.Timestamp(year=YEAR, month=month, day=calendar.monthrange(YEAR, month)[1]),
        freq='B'
    ))


def distribute_hours(project_start_date, project_end_date, hours_by_month, week_start, week_end):
    year_start = datetime(YEAR, 1, 1)
    year_end = datetime(YEAR, 12, 31)

    # Working days in the project in the month of the week
    month_business_days = compute_month_business_days(get_month(week_start, week_end))

    # Business days in the current week
    week_days = pd.date_range(
        start=max(week_start, project_start_date, year_start),
        end=min(week_end, project_end_date, year_end),
        freq='B'
    )
    week_business_days = len(week_days)

    # Calculate hours for this week
    exact_hours_by_month = float(hours_by_month) * month_business_days / 20
    try:
        hours_this_week = exact_hours_by_month * week_business_days / month_business_days
    except ZeroDivisionError:
        hours_this_week = 0

    return hours_this_week


# def compute_assignation_hours():
load_projects()
projects = st.session_state.projects_data

weeks = generate_weeks(YEAR)

assignation = pd.concat([
    weeks.loc[['Monday', 'Sunday']],
    pd.DataFrame(0, index=team_members_names, columns=weeks.columns)
])

for week_idx, week in weeks.T.iterrows():
    week_start = pd.to_datetime(week['Monday'])
    week_end = pd.to_datetime(week['Sunday'])

    for _, project in projects.iterrows():
        team_member = project['Equipo']
        if (project['Fin'] >= week_start) and (project['Inicio'] <= week_end):
            hours = distribute_hours(
                project['Inicio'], project['Fin'],
                project['HorasMes'], week_start, week_end
            )
            assignation.loc[team_member, week_idx] += hours

print(assignation.head())

free_hours = assignation.copy()
free_hours.loc[team_members_names]=0

for team_member in team_members_names:
    for week in assignation.columns:
        week_start = pd.to_datetime(weeks[week]['Monday'])
        week_end = pd.to_datetime(weeks[week]['Sunday'])

        month = get_month(week_start, week_end)
        month_hours_available = team_members.loc[team_members['Nombre'] == team_member, MONTHS[month - 1]].item()

        available_hours = distribute_hours(week_start, week_end, month_hours_available, week_start, week_end)

        free_hours.loc[team_member, week] = available_hours - assignation.loc[team_member, week]

print(free_hours.head())