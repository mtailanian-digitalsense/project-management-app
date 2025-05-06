import streamlit as st

def set_page_config():
    st.session_state.page_config = (
        st.set_page_config(
            page_title="Gestión Operativa",
            layout="wide",
            initial_sidebar_state="collapsed",
            page_icon="🇦🇲",
        )
    )

def hide_sidebar():
    hide_sidebar_style = """
        <style>
            [data-testid="stSidebarNav"] {display: none;}
        </style>
    """
    st.markdown(hide_sidebar_style, unsafe_allow_html=True)

def apply_tabs_spacing():
    tabs_spacing = """
        <style>
            div[data-baseweb="tab-list"] {
                display: flex;
                justify-content: center;  /* Center the tabs container */
                gap: 30px;  /* Add gap between tabs */
            }
            div[data-baseweb="tab"] {
                flex-grow: 0;  /* Do not stretch tabs to fill space */
                text-align: center;  /* Center the tab labels */
            }
        </style>
    """
    st.markdown(tabs_spacing, unsafe_allow_html=True)

def remove_top_padding():
    top_padding = """
        <style>
            .block-container{
                    padding-top: 0px;
                }
        </style>
    """
    st.markdown(top_padding, unsafe_allow_html=True)

def add_title():
    st.markdown(
        """
        <h1 style='text-align: center;'>Gestión Operativa</h1>
        """,
        unsafe_allow_html=True
    )


def apply_all_configs():
    set_page_config()
    # hide_sidebar()  # Not needed anymore, as I added it in the .streamlit/config.toml
    apply_tabs_spacing()
    remove_top_padding()
    add_title()
