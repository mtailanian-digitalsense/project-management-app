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
PROJECT_TYPES = ["Facturable", "No facturable"]


def create_projects_table():
    create_table_query = """
                         CREATE TABLE IF NOT EXISTS projects \
                         ( \
                             Proyecto \
                             TEXT, \
                             Tipo \
                             TEXT, \
                             Inicio \
                             DATETIME, \
                             Fin \
                             DATETIME, \
                             Equipo \
                             TEXT, \
                             HorasMes \
                             NUMBER
                         ) \
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


def add_project_form():

    with st.form("add_project_form"):
        st.subheader("Agregar nueva asignación")

        # Create form fields for each column
        proyecto = st.text_input("Proyecto", key="new_proyecto")
        tipo = st.selectbox("Tipo", options=PROJECT_TYPES, key="new_tipo")
        inicio = st.date_input("Inicio", value=date.today(), key="new_inicio")
        fin = st.date_input("Fin", value=date.today(), key="new_fin")
        equipo = st.selectbox("Equipo", options=st.session_state.team_data['Nombre'].tolist(), key="new_equipo")
        horas_mes = st.number_input("Horas Mes", min_value=0, key="new_horas_mes")

        submitted = st.form_submit_button("Agregar asignación")

        if submitted and proyecto:  # Basic validation
            # Convert to datetime objects for consistency with DataFrame
            inicio_dt = pd.to_datetime(inicio)
            fin_dt = pd.to_datetime(fin)

            # Create new row as a DataFrame
            new_row = pd.DataFrame([{
                'Proyecto': proyecto,
                'Tipo': tipo,
                'Inicio': inicio_dt,
                'Fin': fin_dt,
                'Equipo': equipo,
                'HorasMes': horas_mes
            }])

            # Append to existing data
            st.session_state.projects_data = pd.concat([st.session_state.projects_data, new_row], ignore_index=True)

            # Save to database
            save_projects(st.session_state.projects_data)

            st.success("Project added successfully!")
            time.sleep(1)
            st.rerun()  # Refresh the page to show the updated data


def show_projects():
    load_projects()
    load_team_members()

    def save_changes():
        try:
            save_projects(st.session_state.edited_projects_data)
            message = st.success('Changes saved successfully!', )
        except Exception as e:
            message = st.error(f"Error saving changes: {e}")
        time.sleep(1)
        message.empty()

    # Calculate progress for each project
    st.session_state.projects_data['Progreso'] = st.session_state.projects_data.apply(
        lambda row: calculate_project_progress(row['Inicio'], row['Fin']), axis=1
    )

    col1, col2 = st.columns([1, 4])
    with col1:

        sort_col = st.selectbox(
            "Ordenar por:",
            options=['Orden original'] + COLUMNS + ['Progreso'],
            index=0,
            key="sort_column"
        )
        # Apply sorting (always ascending)
        if sort_col in st.session_state.projects_data.columns:
            sorted_df = st.session_state.projects_data.sort_values(by=sort_col, ascending=True)
        else:
            sorted_df = st.session_state.projects_data

        add_project_form()

    with col2:
        st.session_state.edited_projects_data = st.data_editor(
            sorted_df,
            num_rows="dynamic",
            use_container_width=True,
            hide_index=True,
            height=800,
            # on_change=on_change_callback,
            disabled=["add_rows"],
            column_config={
                "Tipo": st.column_config.SelectboxColumn(
                    "Tipo",
                    help="Facturable o no. Sirve para diferenciar proyectos internos, y calcular métricas de ocupación",
                    width="small",
                    options=PROJECT_TYPES,
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