import time
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import plotly.graph_objects as go
import plotly.express as px


# Database connection
DATABASE_URL = "sqlite:///data/team_members.db"  # Update this with your database URL
engine = create_engine(DATABASE_URL)

COLUMNS = [
    'Nombre', 'Rol', 'Grado', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Setiembre',
    'Octubre', 'Noviembre', 'Diciembre'
]

def create_team_members_table():
    create_table_query = """
    CREATE TABLE IF NOT EXISTS team_members (
        Nombre TEXT,
        Rol TEXT,
        Grado TEXT,
        Enero NUMBER,
        Febrero NUMBER,
        Marzo NUMBER,
        Abril NUMBER,
        Mayo NUMBER,
        Junio NUMBER,
        Julio NUMBER,
        Agosto NUMBER,
        Setiembre NUMBER,
        Octubre NUMBER,
        Noviembre NUMBER,
        Diciembre NUMBER
    )
    """
    with engine.connect() as connection:
        connection.execute(text(create_table_query))

def load_team_members():
    create_team_members_table()
    if 'team_data' not in st.session_state:
        try:
            query = "SELECT * FROM team_members"
            st.session_state.team_data =  pd.read_sql(query, engine)
        except Exception as e:
            st.error(f"Error loading team members: {e}")
            st.session_state.team_data = pd.DataFrame(columns=COLUMNS)


def save_team_members(df):
    df.to_sql('team_members', engine, if_exists='replace', index=False)

def show_team():

    load_team_members()

    def save_changes():
        try:
            save_team_members(st.session_state.edited_team_data)
            message = st.success('Changes saved successfully!', )
        except Exception as e:
            message = st.error(f"Error saving changes: {e}")
        time.sleep(1)
        message.empty()

    st.session_state.edited_team_data = st.data_editor(
        st.session_state.team_data,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        height=500,
        # on_change=save_changes,
        column_config={
            "Grado": st.column_config.SelectboxColumn(
                "Grado",
                help="Maximo nivel académico alcanzado",
                width="small",
                options=[
                    "Ph.D.",
                    "Msc.",
                    "Ing.",
                    "Estudiante",
                    "Otro",
                ],
                # required=True,
            ),
            "Rol": st.column_config.SelectboxColumn(
                "Rol",
                help="Cargo en Digital Sense",
                # width="medium",
                options=[
                    "Director",
                    "Team Leader",
                    "Senior Engineer",
                    "Engineer",
                    "Junior Engineer",
                    "Tech & Delivery",
                    "Developer",
                    "Consultant",
                    "Other",
                ],
                # required=True,
            ),
            "Enero": st.column_config.NumberColumn("Enero", width="small"),
            "Febrero": st.column_config.NumberColumn("Feb.", width="small"),
            "Marzo": st.column_config.NumberColumn("Marzo", width="small"),
            "Abril": st.column_config.NumberColumn("Abril", width="small"),
            "Mayo": st.column_config.NumberColumn("Mayo", width="small"),
            "Junio": st.column_config.NumberColumn("Junio", width="small"),
            "Julio": st.column_config.NumberColumn("Julio", width="small"),
            "Agosto": st.column_config.NumberColumn("Agosto", width="small"),
            "Setiembre": st.column_config.NumberColumn("Set.", width="small"),
            "Octubre": st.column_config.NumberColumn("Oct.", width="small"),
            "Noviembre": st.column_config.NumberColumn("Nov.", width="small"),
            "Diciembre": st.column_config.NumberColumn("Dic.", width="small"),
        },
    )
    save_changes()

    # ---------------------------------------------------------------
    # Add Charts
    chart_data_role = st.session_state.edited_team_data.groupby('Rol').size().reset_index(name='count')
    chart_data_grade = st.session_state.edited_team_data.groupby('Grado').size().reset_index(name='count')

    col1, col2 = st.columns([1, 1])  # Use equal ratio for dynamic adjustment

    with col1:
        fig1 = go.Figure(data=[go.Pie(
            labels=chart_data_role['Rol'],
            values=chart_data_role['count'],
            title='Team Members by Roles',
            marker=dict(colors=px.colors.qualitative.Vivid),
            textinfo='label+percent',
            hole=0.4
        )])
        fig1.update_layout(
            title=dict(font=dict(size=24)),
            margin=dict(t=0, b=0, l=0, r=0)
        )
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        fig2 = go.Figure(data=[go.Pie(
            labels=chart_data_grade['Grado'],
            values=chart_data_grade['count'],
            title='Team Members by Grade',
            marker=dict(colors=px.colors.qualitative.Vivid),
            textinfo='label+percent',
            hole=0.4
        )])
        fig2.update_layout(
            title=dict(font=dict(size=24)),
            margin=dict(t=0, b=0, l=0, r=0)
        )
        st.plotly_chart(fig2, use_container_width=True)
