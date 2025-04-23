import streamlit as st
from utils.config_markdown import apply_all_configs

apply_all_configs()

LANDINGS = [
    "Proyectos", "Licencias", "Equipo", "Asignación a proyectos", "Asignación total", "Métricas", "Boost",
    "Asignación a Boost"
]

def main():
    from pages.projects import show_projects
    from pages.holidays import show_holidays
    from pages.team import show_team
    from pages.assignation_projects import show_assignation_projects
    from pages.assignation_total import show_assignation_total
    from pages.metrics import show_metrics
    from pages.boost import show_boost
    from pages.assignation_boost import show_assignation_boost

    # st.title("Project Management System")

    if 'selected_tab' not in st.session_state:
        st.session_state.selected_tab = LANDINGS[0]

    tabs = st.tabs(LANDINGS)

    for i, (tab, landing) in enumerate(zip(tabs, LANDINGS)):
        with tab:
            if landing == "Proyectos":
                show_projects()
            elif landing == "Licencias":
                show_holidays()
            elif landing == "Equipo":
                show_team()
            elif landing == "Asignación a proyectos":
                show_assignation_projects()
            elif landing == "Asignación total":
                show_assignation_total()
            elif landing == "Métricas":
                show_metrics()
            elif landing == "Boost":
                show_boost()
            elif landing == "Asignación a Boost":
                show_assignation_boost()
        if tab:
            st.session_state.selected_tab = landing
            st.query_params = {"selected_tab": st.session_state.selected_tab}

if __name__ == "__main__":
    main()