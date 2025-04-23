import streamlit as st
from unidecode import unidecode

from .assignation_projects import compute_assignation_hours


MONTHS = [
    'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
    'Julio', 'Agosto', 'Setiembre', 'Octubre', 'Noviembre', 'Diciembre'
]


def compute_assingation_hours_total():
    assignation_hours = compute_assignation_hours()

    assignation_hours_total = assignation_hours.groupby('Equipo').sum().reset_index().drop(columns=['Proyecto'])
    assignation_hours_total['Equipo_sort'] = assignation_hours_total['Equipo'].apply(unidecode)
    assignation_hours_total = assignation_hours_total.sort_values(by=['Equipo_sort']).reset_index().drop(columns=['Equipo_sort', 'index'])
    return assignation_hours_total

def show_assignation_total():

    assignation_hours_total = compute_assingation_hours_total()

    # Style the table
    def highlight_rows(row):
        return ['background-color: #ffffff' if row.name % 2 == 0 else 'background-color: #f5f5f5' for _ in row]
    assignation_hours_total_styled = assignation_hours_total.style.apply(highlight_rows, axis=1)

    st.dataframe(
        assignation_hours_total_styled,
        use_container_width=True,
        height=600,
        hide_index=True,
    )
