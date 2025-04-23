import pandas as pd
import streamlit as st
import calendar
from unidecode import unidecode
import plotly.graph_objects as go
import plotly.express as px

from .team import load_team_members
from .projects import load_projects


MONTHS = [
    'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
    'Julio', 'Agosto', 'Setiembre', 'Octubre', 'Noviembre', 'Diciembre'
]


def compute_assignation_hours():
    load_projects()
    projects = st.session_state.projects_data

    # How many days from each month are assigned to each project for each team member
    assignation_days = projects.join(
        projects.apply(lambda p: pd.Series(pd.date_range(p['Inicio'], p['Fin'], freq='D').to_period('M')), axis=1)
        .apply(lambda x: pd.Series(x).value_counts(), axis=1)
        .fillna(0)
        .astype(int)
    )
    ## Rename columns to Spanish month names
    assignation_days.columns = assignation_days.columns.astype(str)
    month_mapping = {f'2025-{i + 1:02d}': month for i, month in enumerate(MONTHS)}
    assignation_days.rename(columns=month_mapping, inplace=True)

    # Convert to hours
    assignation_hours = assignation_days.copy()
    assignation_days['HorasMes'] = assignation_days['HorasMes'].astype(float)
    days_in_month = {month: calendar.monthrange(2025, i + 1)[1] for i, month in enumerate(MONTHS)}
    for month in MONTHS:
        assignation_hours[month] = assignation_hours[month] / days_in_month[month] * assignation_days['HorasMes']
    assignation_hours[MONTHS] = assignation_hours[MONTHS].fillna(0)
    assignation_hours[MONTHS] = assignation_hours[MONTHS].astype(int)

    columns_to_keep = ['Equipo', 'Proyecto'] + MONTHS
    assignation_hours = assignation_hours[columns_to_keep]
    return assignation_hours

def show_assignation_projects():
    load_team_members()
    team_members = st.session_state.team_data  # TODO: ensure all team members are in this table. It could happen when they have no project assigned, as the list of team members is taken from projects.db

    assignation_hours = compute_assignation_hours()

    assignation_hours['Equipo_sort'] = assignation_hours['Equipo'].apply(unidecode)
    assignation_hours = assignation_hours.sort_values(by=['Equipo_sort', 'Proyecto']).drop(columns=['Equipo_sort'])

    # Style rows
    def highlight_rows(row):
        if row.name == 0:
            highlight_rows.prev_equipo = row['Equipo']
            return ['background-color: #f5f5f5' for _ in row]
        elif row['Equipo'] != highlight_rows.prev_equipo:
            highlight_rows.prev_equipo = row['Equipo']
            highlight_rows.color = '#ffffff' if highlight_rows.color == '#f5f5f5' else '#f5f5f5'
        return [f'background-color: {highlight_rows.color}' for _ in row]

    highlight_rows.prev_equipo = None
    highlight_rows.color = '#f5f5f5'
    assignation_hours_styled = assignation_hours.style.apply(highlight_rows, axis=1)

    st.dataframe(
        assignation_hours_styled,
        use_container_width=True,
        height=600,
        hide_index=True,
    )

    # Chart: pie by project with plotly

    _, col1, _ = st.columns([2, 4, 2])

    project_hours = assignation_hours.groupby('Proyecto')[MONTHS].sum().sum(axis=1).reset_index()
    project_hours.columns = ['Proyecto', 'TotalHoras']

    with col1:
        fig = go.Figure(data=[go.Pie(
            labels=project_hours['Proyecto'],
            values=project_hours['TotalHoras'],
            title='Hours per Project',
            marker=dict(colors=px.colors.qualitative.Vivid),
            textinfo='label+percent',
            hole=0.4,
        )])
        fig.update_layout(
            title=dict(text='Tamaño de los proyectos', font=dict(size=24)),
            margin=dict(t=100, b=200, l=0, r=0),
            height=750,
        )
        st.plotly_chart(fig, use_container_width=True)