import calendar
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px

from .team import load_team_members
from .projects import load_projects
from .holidays import compute_monthly_holidays
from .assignation_total import compute_assingation_hours_total


MONTHS = [
    'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
    'Julio', 'Agosto', 'Setiembre', 'Octubre', 'Noviembre', 'Diciembre'
]
QUARTERS = {
    'Q1': ['Enero', 'Febrero', 'Marzo'],
    'Q2': ['Abril', 'Mayo', 'Junio'],
    'Q3': ['Julio', 'Agosto', 'Setiembre'],
    'Q4': ['Octubre', 'Noviembre', 'Diciembre']
}


def compute_assignation_hours():
    # TODO: refactor this. it is used at least in assignation_projects.py, assignation_total.py and metrics.py

    load_projects()
    projects = st.session_state.projects_data

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
    assignation_hours[MONTHS] = assignation_hours[MONTHS].astype(int)

    return assignation_hours


def show_assignation_metric_no_holidays(team_members):
    assignation_hours = compute_assignation_hours()

    available_hours = team_members[MONTHS].sum(axis=0)
    assigned_hours = assignation_hours[MONTHS].sum(axis=0)
    metric = assigned_hours / available_hours * 100

    show_metric(metric)


def show_assignation_metric_considering_holidays(team_members):

    monthly_assignation_h = compute_assingation_hours_total().set_index('Equipo')
    monthly_holidays_d = compute_monthly_holidays().rename(columns={"name": "Equipo"}).set_index('Equipo')
    monthly_availability_h = team_members[['Nombre'] + MONTHS].rename(columns={"Nombre": "Equipo"}).set_index('Equipo')

    # Keep only the indexes from the technical team (those listed in 'Equipo' column in the webapp)
    monthly_assignation_h = monthly_assignation_h.reindex(monthly_availability_h.index).fillna(0)
    monthly_holidays_d = monthly_holidays_d.reindex(monthly_availability_h.index)

    # Computing real availability
    # Note that this computation is an approximation. # TODO: fix to make it exact
    # This computation is not exact. It could be the case where someone has an assigned project + holidays during the
    #   same period, and then some free time during other days of the month. This computation will make it look like is
    #   all full.
    monthly_holidays_h = monthly_availability_h / 4 / 5 * monthly_holidays_d
    monthly_holidays_h = monthly_holidays_h.fillna(0)
    real_availability_h = monthly_availability_h - (monthly_assignation_h + monthly_holidays_h)
    # Clip at 0 because project assignations do not stop at holidays
    #   so we could have duplicated assignation: project + holidays
    real_availability_h = real_availability_h.clip(lower=0)


    available_hours = monthly_availability_h[MONTHS].sum(axis=0)
    assigned_hours = (monthly_availability_h - real_availability_h)[MONTHS].sum(axis=0)

    metric = assigned_hours / available_hours * 100

    show_metric(metric)


def show_metric(metric):
    metric = metric.round(0).astype(int)
    df_monthly_metric = metric.to_frame(name='% Asignación').T

    # Calculate metrics by quarter
    metric_by_quarter = {}
    for quarter, months in QUARTERS.items():
        metric_by_quarter[quarter] = metric[months].sum() / len(months)
    df_quarter_metric = pd.Series(metric_by_quarter).round(0).to_frame(name='% Asignación').T

    st.header("% de asignación por quarter")
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    with col1:
        fig = go.Figure(data=[go.Pie(
            labels=['Asignado', 'Libre'],
            values=[df_quarter_metric['Q1']['% Asignación'], 100 - df_quarter_metric['Q1']['% Asignación']],
            title=dict(text=f"Q1: {df_quarter_metric['Q1']['% Asignación']:.0f}%", font=dict(size=40)),
            marker=dict(colors=px.colors.qualitative.Vivid),
            textinfo='label+percent',
            hole=0.4,
        )])
        fig.update_layout(
            title=dict(text='', font=dict(size=24)),
            margin=dict(t=0, b=0, l=0, r=0),
        )
        st.plotly_chart(fig, use_container_width=True, key=f"key_{np.random.randint(1000)}")
    with col2:
        fig = go.Figure(data=[go.Pie(
            labels=['Asignado', 'Libre'],
            values=[df_quarter_metric['Q2']['% Asignación'], 100 - df_quarter_metric['Q2']['% Asignación']],
            title=dict(text=f"Q2: {df_quarter_metric['Q2']['% Asignación']:.0f}%", font=dict(size=40)),
            marker=dict(colors=px.colors.qualitative.Vivid),
            textinfo='label+percent',
            hole=0.4,
        )])
        fig.update_layout(
            title=dict(text='', font=dict(size=24)),
            margin=dict(t=0, b=0, l=0, r=0),
        )
        st.plotly_chart(fig, use_container_width=True, key=f"key_{np.random.randint(1000)}")
    with col3:
        fig = go.Figure(data=[go.Pie(
            labels=['Asignado', 'Libre'],
            values=[df_quarter_metric['Q3']['% Asignación'], 100 - df_quarter_metric['Q3']['% Asignación']],
            title=dict(text=f"Q3: {df_quarter_metric['Q3']['% Asignación']:.0f}%", font=dict(size=40)),
            marker=dict(colors=px.colors.qualitative.Vivid),
            textinfo='label+percent',
            hole=0.4,
        )])
        fig.update_layout(
            title=dict(text='', font=dict(size=24)),
            margin=dict(t=0, b=0, l=0, r=0),
        )
        st.plotly_chart(fig, use_container_width=True, key=f"key_{np.random.randint(1000)}")
    with col4:
        fig = go.Figure(data=[go.Pie(
            labels=['Asignado', 'Libre'],
            values=[df_quarter_metric['Q4']['% Asignación'], 100 - df_quarter_metric['Q4']['% Asignación']],
            title=dict(text=f"Q4: {df_quarter_metric['Q4']['% Asignación']:.0f}%", font=dict(size=40)),
            marker=dict(colors=px.colors.qualitative.Vivid),
            textinfo='label+percent',
            hole=0.4,
        )])
        fig.update_layout(
            title=dict(text='', font=dict(size=24)),
            margin=dict(t=0, b=0, l=0, r=0),
        )
        st.plotly_chart(fig, use_container_width=True, key=f"key_{np.random.randint(1000)}")

    _, col1, _ = st.columns([2, 4, 2])
    with col1:
        st.dataframe(
            df_quarter_metric,
            use_container_width=True,
            hide_index=True,
        )

    st.header("% de asignación por mes")
    _, col1, _ = st.columns([2, 4, 2])
    with col1:
        st.dataframe(
            df_monthly_metric,
            use_container_width=True,
            hide_index=True,
        )


def show_metrics():
    load_team_members()
    team_members = st.session_state.team_data
    team_members[MONTHS] = team_members[MONTHS].apply(lambda x: x.astype(int))

    st.header("Considerando licencias")
    show_assignation_metric_considering_holidays(team_members)
    st.header("Sin considerar licencias")
    show_assignation_metric_no_holidays(team_members)


if __name__ == '__main__':
    show_metrics()
