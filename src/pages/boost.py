import pandas as pd
import numpy as np
import calendar
import streamlit as st
from datetime import datetime, timedelta

from .team import load_team_members
from .projects import load_projects
from .assignation_total import compute_assingation_hours_total

YEAR = 2025
MONTHS = [
    'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
    'Julio', 'Agosto', 'Setiembre', 'Octubre', 'Noviembre', 'Diciembre'
]


def generate_weeks(year):
    # Start from the first Monday of the year or the last Monday of the previous year
    start_date = datetime(year, 1, 1)
    if start_date.weekday() != 0:
        start_date -= timedelta(days=start_date.weekday())

    weeks = []
    week_number = 1
    while start_date.year == year or (start_date + timedelta(days=6)).year == year:
        end_date = start_date + timedelta(days=6)

        # How many days of this week belong to each month
        date_range = pd.date_range(start=start_date, end=end_date, freq='D')  # Date range for the current week
        # date_range = date_range[date_range.year == year]  # Filter dates to this year
        date_range = date_range[(date_range.year == year) & (date_range.weekday < 5)]  # Filter dates to this year and weekdays
        days_in_month = date_range.to_series().dt.month.value_counts().sort_index()
        days_in_month = {month: days_in_month.get(month, 0) for month in range(1, 13)}

        weeks.append({
            'index': week_number,
            'Monday': start_date.strftime('%Y-%m-%d'),
            'Sunday': end_date.strftime('%Y-%m-%d'),
            **{f'{MONTHS[month - 1]}': days for month, days in days_in_month.items()},
        })
        start_date += timedelta(days=7)
        week_number += 1

    return pd.DataFrame(weeks).set_index('index').T


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
    # week_days = pd.date_range(start=max(week_start, project_start_date), end=min(week_end, project_end_date), freq='B')
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

def compute_weekly_assignation(team_members, projects):
    # Team members
    load_team_members()
    team_members = st.session_state.team_data
    team_members_names = team_members['Nombre'].tolist()

    # Load projects
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

    return weeks, assignation

def compute_weekly_free_hours():
    load_team_members()
    team_members = st.session_state.team_data
    team_members_names = team_members['Nombre'].tolist()

    load_projects()
    projects = st.session_state.projects_data

    weeks, assignation = compute_weekly_assignation(team_members, projects)

    free_hours = assignation.copy()
    free_hours.loc[team_members_names] = 0

    for team_member in team_members_names:
        for week in assignation.columns:
            week_start = pd.to_datetime(weeks[week]['Monday'])
            week_end = pd.to_datetime(weeks[week]['Sunday'])

            month = get_month(week_start, week_end)
            month_hours_available = team_members.loc[team_members['Nombre'] == team_member, MONTHS[month - 1]].item()

            # available_hours = distribute_hours(
            #     pd.Timestamp(year=YEAR, month=month, day=1),
            #     pd.Timestamp(year=YEAR, month=month, day=calendar.monthrange(YEAR, month)[1]),
            #     month_hours_available, week_start, week_end
            # )
            available_hours = distribute_hours(week_start, week_end, month_hours_available, week_start, week_end)

            free_hours.loc[team_member, week] = available_hours - assignation.loc[team_member, week]


    free_hours.loc[team_members_names] = free_hours.loc[team_members_names].round().astype(int)
    free_hours.loc['Inicio'] = free_hours.loc['Monday'].apply(lambda x: pd.to_datetime(x).strftime('%d/%m'))
    free_hours.loc['Fin'] = free_hours.loc['Sunday'].apply(lambda x: pd.to_datetime(x).strftime('%d/%m'))
    free_hours.drop(['Monday', 'Sunday'], inplace=True)
    free_hours = free_hours.loc[
        ['Inicio', 'Fin'] + [row for row in free_hours.index if row not in ['Inicio', 'Fin']]
    ]

    free_hours.columns = free_hours.columns.map(str)
    free_hours.reset_index(inplace=True)
    free_hours = free_hours.rename(columns={'index': 'Semana'})

    return weeks, free_hours

# def compute_workable_days(month):
#     # Calculate the total workable days (excluding Saturdays and Sundays) in the current month
#     month_index = MONTHS.index(month) + 1
#     month_start = datetime(2025, month_index, 1)
#     month_end = datetime(2025, month_index, calendar.monthrange(2025, month_index)[1])
#     all_days = pd.date_range(start=month_start, end=month_end, freq='D')
#     workable_days = np.sum(np.isin(all_days.weekday, range(5)))
#     return workable_days
#
#
# def compute_free_hours_per_week():
#     # Team members
#     load_team_members()
#     team_members = st.session_state.team_data
#     team_members_names = team_members['Nombre'].tolist()
#
#     # Weeks of the year
#     weeks = generate_weeks(YEAR)
#
#     # Assignation for each week
#     assignation_weeks = pd.DataFrame(columns=weeks.columns, index=team_members_names)
#     monthly_hours = compute_assingation_hours_total()
#     for week in weeks.columns:
#         for member in team_members_names:
#             month = weeks[week][MONTHS].idxmax()
#
#             week_days_in_current_month = weeks[week][month]
#             working_days_in_current_month = compute_workable_days(month)
#
#             month_hours_available = team_members.loc[team_members['Nombre'] == member, month].item()
#             month_hours_available_exact = month_hours_available / 20 * working_days_in_current_month  # This is to fix our usual approximation of 20 working days per month
#
#             month_hours = monthly_hours.loc[monthly_hours['Equipo'] == member, month]
#             month_hours = 0 if month_hours.empty else month_hours.item()
#             month_hours_exact = month_hours / 20 * working_days_in_current_month  # This is to fix our usual approximation of 20 working days per month
#
#             week_hours = month_hours_exact / working_days_in_current_month * week_days_in_current_month
#             week_hours_available = month_hours_available_exact / working_days_in_current_month * week_days_in_current_month
#
#             assignation_weeks.loc[member, week] = (week_hours_available - week_hours).round().astype(int)
#
#     assignation_weeks.loc['Inicio'] = weeks.loc['Monday'].apply(lambda x: pd.to_datetime(x).strftime('%d/%m'))
#     assignation_weeks.loc['Fin'] = weeks.loc['Sunday'].apply(lambda x: pd.to_datetime(x).strftime('%d/%m'))
#     assignation_weeks = assignation_weeks.loc[
#         ['Inicio', 'Fin'] + [row for row in assignation_weeks.index if row not in ['Inicio', 'Fin']]
#     ]
#
#     assignation_weeks.columns = assignation_weeks.columns.map(str)
#     assignation_weeks.reset_index(inplace=True)
#     assignation_weeks = assignation_weeks.rename(columns={'index': 'Semana'})
#     return weeks, assignation_weeks


def compute_next_week_column(weeks, week_start_column='Monday'):
    today = datetime.today()
    next_week_col = None
    for week in weeks.columns:
        if pd.to_datetime(weeks.loc[week_start_column, week]) > today:
            next_week_col = str(week)
            break
    return next_week_col


def show_boost():

    weeks, assignation_weeks = compute_weekly_free_hours()

    # Ensure all columns are strings
    for col in assignation_weeks.columns:
        if assignation_weeks[col].dtype == 'object':
            assignation_weeks[col] = assignation_weeks[col].astype(str)

    # Style the table
    # ------------------------------------------------------------------------------------------------------------------
    def highlight_alternating_rows(row):
        return ['background-color: #ffffff' if row.name % 2 == 0 else 'background-color: #f5f5f5' for _ in row]

    def highlight_first_two_rows(row):
        if row.name < 2:
            return ['background-color: #dddddd'] * len(row)
        else:
            return [''] * len(row)


    next_week_col = compute_next_week_column(weeks)
    def highlight_next_week(col):
        if col.name == next_week_col:
            return ['background-color: #e8f5e9'] * len(col)
        else:
            return [''] * len(col)

    def highlight_greater_than_three(val):
        try:
            int_val = int(val)
            if int_val > 3:
                return 'color: #CF0515'
            return ''
        except ValueError:
            return ''

    assignation_weeks_styled = (
        assignation_weeks.style
        .apply(highlight_alternating_rows, axis=1)
        .apply(highlight_next_week, axis=0)
        .apply(highlight_first_two_rows, axis=1)
        .map(highlight_greater_than_three)
    )

    st.dataframe(
        assignation_weeks_styled,
        use_container_width=True,
        height=750,
        hide_index=True,
    )
