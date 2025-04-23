import pandas as pd
import numpy as np
import calendar
import streamlit as st
from datetime import datetime, timedelta

from src.pages.team import load_team_members
from src.pages.assignation_total import compute_assingation_hours_total

YEAR = 2025
MONTHS = [
    'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
    'Julio', 'Agosto', 'Setiembre', 'Octubre', 'Noviembre', 'Diciembre'
]


def compute_workable_days(month):
    # Calculate the total workable days (excluding Saturdays and Sundays) in the current month
    month_index = MONTHS.index(month) + 1
    month_start = datetime(2025, month_index, 1)
    month_end = datetime(2025, month_index, calendar.monthrange(2025, month_index)[1])
    all_days = pd.date_range(start=month_start, end=month_end, freq='D')
    workable_days = np.sum(np.isin(all_days.weekday, range(5)))
    return workable_days


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


# Team members
load_team_members()
team_members = st.session_state.team_data
team_members_names = team_members['Nombre'].tolist()

# Weeks of the year
weeks = generate_weeks(YEAR)

# Assignation for each week
assignation_weeks = pd.DataFrame(columns=weeks.columns, index=team_members_names)
monthly_hours = compute_assingation_hours_total()
for week in weeks.columns:
    for member in team_members_names:
        month = weeks[week][MONTHS].idxmax()

        week_days_in_current_month = weeks[week][month]
        working_days_in_current_month = compute_workable_days(month)

        month_hours_available = team_members.loc[team_members['Nombre'] == member, month].item()
        month_hours_available_exact = month_hours_available / 20 * working_days_in_current_month  # This is to fix our usual approximation of 20 working days per month

        month_hours = monthly_hours.loc[monthly_hours['Equipo'] == member, month]
        month_hours = 0 if month_hours.empty else month_hours.item()
        month_hours_exact = month_hours / 20 * working_days_in_current_month  # This is to fix our usual approximation of 20 working days per month

        week_hours = month_hours_exact / working_days_in_current_month * week_days_in_current_month
        week_hours_available = month_hours_available_exact / working_days_in_current_month * week_days_in_current_month

        assignation_weeks.loc[member, week] = (week_hours_available - week_hours).round().astype(int)

assignation_weeks.loc['Inicio'] = weeks.loc['Monday'].apply(lambda x: pd.to_datetime(x).strftime('%d/%m'))
assignation_weeks.loc['Fin'] = weeks.loc['Sunday'].apply(lambda x: pd.to_datetime(x).strftime('%d/%m'))
assignation_weeks = assignation_weeks.loc[['Inicio', 'Fin'] + [row for row in assignation_weeks.index if row not in ['Inicio', 'Fin']]]

assignation_weeks.columns = assignation_weeks.columns.map(str)
assignation_weeks.reset_index(inplace=True)
assignation_weeks = assignation_weeks.rename(columns={'index': 'Semana'})

print(assignation_weeks)

boost_assignation = pd.DataFrame(columns=assignation_weeks.columns, index=assignation_weeks['Semana'])
boost_assignation = boost_assignation.drop(columns=['Semana'])
boost_assignation.loc['_Inicio'] = weeks.loc['Monday'].values  # Full format of the date. useful for comparing with today()
boost_assignation.reset_index(inplace=True)
boost_assignation = boost_assignation.fillna('')
boost_assignation.iloc[0] = assignation_weeks.iloc[0].values  # Inicio
boost_assignation.iloc[1] = assignation_weeks.iloc[1].values  # Fin
