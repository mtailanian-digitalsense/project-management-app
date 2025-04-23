import time
import streamlit as st
import pandas as pd
from datetime import date, datetime
from sqlalchemy import create_engine, text

from .team import load_team_members

# Database connection
DATABASE_URL = "sqlite:///data/projects.db"
engine = create_engine(DATABASE_URL)

COLUMNS = ['Proyecto', 'Tipo', 'Inicio', 'Fin', 'Equipo', 'HorasMes']


def create_projects_table():
    create_table_query = """
    CREATE TABLE IF NOT EXISTS projects (
        Proyecto TEXT,
        Tipo TEXT,
        Inicio DATETIME,
        Fin DATETIME,
        Equipo TEXT,
        HorasMes NUMBER
    )
    """
    with engine.connect() as connection:
        connection.execute(text(create_table_query))


def load_projects():

    # Create the table if it doesn't exist
    create_projects_table()

    if 'projects_data' not in st.session_state:
        try:
            query = "SELECT * FROM projects"
            df = pd.read_sql(query, engine)
            df['Inicio'] = pd.to_datetime(df['Inicio'])
            df['Fin'] = pd.to_datetime(df['Fin'])
            st.session_state.projects_data = df
        except Exception as e:
            st.error(f"Error loading projects: {e}")
            st.session_state.projects_data = pd.DataFrame(columns=COLUMNS)


def save_projects(df):
    df.to_sql('projects', engine, if_exists='replace', index=False)


def calculate_project_progress(start_date, end_date):
    today = datetime.today()
    if today < start_date:
        return 0
    elif today > end_date:
        return 100
    else:
        total_duration = (end_date - start_date).days
        elapsed_duration = (today - start_date).days
        try:
            return int((elapsed_duration / total_duration) * 100)
        except ValueError:
            return 0


def show_projects():

    load_projects()
    load_team_members()

    # Calculate progress for each project
    st.session_state.projects_data['Progreso'] = st.session_state.projects_data.apply(
        lambda row: calculate_project_progress(row['Inicio'], row['Fin']), axis=1
    )

    def save_changes():
        try:
            save_projects(st.session_state.edited_projects_data)
            message = st.success('Changes saved successfully!', )
        except Exception as e:
            message = st.error(f"Error saving changes: {e}")
        time.sleep(1)
        message.empty()

    st.session_state.edited_projects_data = st.data_editor(
        st.session_state.projects_data,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        height=600,
        # on_change=save_changes,
        column_config={
            "Tipo": st.column_config.SelectboxColumn(
                "Tipo",
                help="Facturable o no. Sirve para diferenciar proyectos internos, y calcular métricas de ocupación",
                width="small",
                options=[
                    "Facturable",
                    "No facturable",
                ],
                # required=True,
            ),
            "Inicio": st.column_config.DateColumn(
                "Inicio",
                help="Fecha de inicio de la asignación del miembro del equipo al proyecto",
                width="small",
                min_value=date(2025, 1, 1),
                max_value=date(2025, 12, 31),
                format="YYYY.MM.DD",
                step=1,
                # required=True,
            ),
            "Fin": st.column_config.DateColumn(
                "Fin",
                help="Fecha de fin de la asignación del miembro del equipo al proyecto",
                width="small",
                min_value=date(2025, 1, 1),
                max_value=date(2025, 12, 31),
                format="YYYY.MM.DD",
                step=1,
                # required=True,
            ),
            "Equipo": st.column_config.SelectboxColumn(
                "Equipo",
                help="Miembro del equipo asignado. Tiene que ser dado de alta con anterioridad en la solapa 'Equipo'",
                width="small",
                options=st.session_state.team_data['Nombre'].tolist(),
                # required=True,
            ),
            "Progreso": st.column_config.ProgressColumn(
                "Progreso",
                help="Porcentaje del proyecto ejecutado basado en la fecha actual",
                width="small",
            ),
        },
    )
    save_changes()

    # if st.button("Refresh Team Data"):
    # refresh_team_data()
