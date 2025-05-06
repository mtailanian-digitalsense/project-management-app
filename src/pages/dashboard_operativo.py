import time
import streamlit as st
import pandas as pd
from datetime import date, datetime
from sqlalchemy import create_engine, text


# Database connection
DATABASE_URL = "sqlite:///data/dashboard_operativo.db"
engine = create_engine(DATABASE_URL)

COLUMNS = [
    'Proyecto', 'TL', 'Status', 'Fecha_fin', 'Porcentaje_avance', 'Burndown_rate', 'Desvio_[semanas]',
    'Desvio_en_[%]_de horas', 'Checklist grade', 'Satisfaccion_percibida_por_cliente', 'Project_Leader_Alert',
    'Issues_Risks_Blockers', 'Comments', 'Proxima_fecha_de_entregables', 'Proximos_entregables',
    'Proximas_licencias', 'Link_a_tech_checklist'
]


def create_dashboard_operativo_table():
    create_table_query = """
    CREATE TABLE IF NOT EXISTS dashboard_operativo (
    Proyecto TEXT,
    TL TEXT,
    Status TEXT,
    Fecha_fin TEXT,
    Porcentaje_avance TEXT,
    Burndown_rate TEXT,
    Desvio_en_semanas TEXT,
    Desvio_en_porcentaje_de_horas TEXT,
    Checklist_grade TEXT,
    Satisfaccion_percibida_por_cliente TEXT,
    Project_Leader_Alert TEXT, 
    Issues_Risks_Blockers TEXT,
    Comments TEXT,
    Proxima_fecha_de_entregables TEXT,
    Proximos_entregables TEXT, 
    Proximas_licencias TEXT,
    Link_a_tech_checklist TEXT
    )
    """
    with engine.connect() as connection:
        connection.execute(text(create_table_query))


def load_dashboard_operativo():

    # Create the table if it doesn't exist
    create_dashboard_operativo_table()

    if 'dashboard_operativo' not in st.session_state:
        try:
            query = "SELECT * FROM dashboard_operativo"
            df = pd.read_sql(query, engine)
            st.session_state.dashboard_operativo = df
        except Exception as e:
            st.error(f"Error loading dashboard_operativo: {e}")
            st.session_state.dashboard_operativo = pd.DataFrame(columns=COLUMNS)


def save_dashboard_operativo(df):
    df.to_sql('dashboard_operativo', engine, if_exists='replace', index=False)


def show_dashboard_operativo():

    load_dashboard_operativo()

    def save_changes():
        try:
            save_dashboard_operativo(st.session_state.edited_dashboard_operativo)
            message = st.success('Changes saved successfully!', )
        except Exception as e:
            message = st.error(f"Error saving changes: {e}")
        time.sleep(1)
        message.empty()

    with st.form("dashboard_operativo_form"):
        # Submit button
        _, col1, _ = st.columns([4, 2, 4])
        with col1:
            submitted = st.form_submit_button("Guardar cambios", use_container_width=True)

        st.session_state.edited_dashboard_operativo = st.data_editor(
            st.session_state.dashboard_operativo,
            num_rows="dynamic",
            use_container_width=True,
            hide_index=True,
            height=600,
        )

    if submitted:
        save_changes()
