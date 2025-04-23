import time
import pandas as pd
import sqlalchemy.exc
import streamlit as st
from sqlalchemy import create_engine, text
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode
from st_aggrid.grid_options_builder import GridOptionsBuilder

from .boost import compute_weekly_free_hours, compute_next_week_column

DATABASE_URL = "sqlite:///data/boost_assignation.db"
engine = create_engine(DATABASE_URL)


def load_boost_assignation():
    weeks, free_hours = compute_weekly_free_hours()

    try:
        query = "SELECT * FROM boost_assignation"
        df = pd.read_sql(query, engine)
        columns = ['Semana'] + [col for col in df.columns if col != 'Semana']
        boost_assignation = df[columns]

    except sqlalchemy.exc.OperationalError:
        # st.error(f"Error loading boost assignations: {e}")

        boost_assignation = pd.DataFrame(columns=free_hours.columns, index=free_hours['Semana'])
        boost_assignation = boost_assignation.drop(columns=['Semana'])
        boost_assignation.loc['_Inicio'] = weeks.loc[
            'Monday'].values  # Full format of the date. useful for comparing with today()
        boost_assignation.reset_index(inplace=True)
        boost_assignation = boost_assignation.fillna('')
        boost_assignation.iloc[0] = free_hours.iloc[0].values  # Inicio
        boost_assignation.iloc[1] = free_hours.iloc[1].values  # Fin

    return boost_assignation, free_hours


def save_boost_assignation(df):
    df.to_sql('boost_assignation', engine, if_exists='replace', index=False)


def show_assignation_boost():
    boost_assignation, free_hours = load_boost_assignation()

    def save_changes():
        try:
            # Get the updated data from session state
            if 'edited_data' in st.session_state:
                updated_df = pd.DataFrame(st.session_state.edited_data)
                save_boost_assignation(updated_df)
                message = st.success('Changes saved successfully!', icon="✅")
            else:
                message = st.warning('No changes to save.')

        except Exception as e:
            message = st.error(f"Error saving changes: {e}")

        time.sleep(1)
        message.empty()

    # Configure AgGrid options
    gb = GridOptionsBuilder.from_dataframe(boost_assignation)

    gb.configure_selection(selection_mode="multiple", use_checkbox=False)
    gb.configure_grid_options(
        domLayout="normal",
        rowHeight=40,
        headerHeight=40,
        enableRangeSelection=True
    )

    # Generate a JavaScript function to conditionally color cells based on free_hours
    # Convert free_hours DataFrame to a format usable in JavaScript
    free_hours_data = {}

    # Skip the first column ('Semana') and the first two rows (headers)
    for col in free_hours.columns[1:]:
        col_values = {}
        for idx, row in free_hours.iterrows():
            if idx > 1:  # Skip the first two header rows
                col_values[str(idx)] = float(row[col]) if pd.notna(row[col]) and row[col] != '' else 0
        free_hours_data[col] = col_values

    # Create JavaScript object string representation
    js_free_hours = str(free_hours_data).replace("'", '"')

    # JavaScript function to apply conditional styling based on free_hours values
    cell_style_function = JsCode(f"""
    function(params) {{
        // Free hours data from Python
        const freeHoursData = {js_free_hours};

        // Default style
        let style = {{
            'borderRight': '1px solid #ddd'
        }};

        // Skip the first column and the first two rows (headers)
        if (params.colDef.field !== 'Semana' && params.node.rowIndex > 1) {{
            const colName = params.colDef.field;
            const rowIdx = params.node.rowIndex;  // Adjust index to match free_hours DataFrame

            // Check if we have data for this cell
            if (freeHoursData[colName] && freeHoursData[colName][rowIdx] !== undefined) {{
                const freeHours = freeHoursData[colName][rowIdx];

                // Apply gray background color if free_hours <= 3
                if (freeHours <= 3) {{
                    style['backgroundColor'] = '#e0e0e0';  // Gray for cells with <=3 free hours
                }}
            }}
        }}

        return style;
    }}
    """)

    # Enable editing and apply the cell style function
    for col in boost_assignation.columns:
        gb.configure_column(
            col,
            editable=True if col != boost_assignation.columns[0] else False,
            width=50 if col != boost_assignation.columns[0] else 150,
            suppressSizeToFit=True,
            cellStyle=cell_style_function if col != boost_assignation.columns[0] else {
                "borderRight": "1px solid #ddd",
            }
        )

    # Highlight in green the next week column
    highlight_column = compute_next_week_column(boost_assignation.set_index('Semana'), week_start_column='_Inicio')

    # For the next week column, use a combined style that preserves both stylings
    next_week_cell_style = JsCode(f"""
    function(params) {{
        // Free hours data from Python
        const freeHoursData = {js_free_hours};

        // Default next week highlight style
        let style = {{
            'backgroundColor': '#e8f5e9',
            'color': '#1b5e20',
            'fontWeight': 'bold',
            'borderRight': '1px solid #ddd'
        }};

        // If it's not the Semana column and not in the first two rows
        if (params.node.rowIndex > 1) {{
            const colName = params.colDef.field;
            const rowIdx = params.node.rowIndex;  // Adjust index to match free_hours DataFrame

            // Check if we have data for this cell and free_hours <= 3
            if (freeHoursData[colName] && freeHoursData[colName][rowIdx] !== undefined) {{
                const freeHours = freeHoursData[colName][rowIdx];

                // If free_hours <= 3, use a gray-green blend for the next week column
                if (freeHours <= 3) {{
                    style['backgroundColor'] = '#d4dbd4';  // Grayish-green for next week with <=3 free hours
                }}
            }}
        }}

        return style;
    }}
    """)

    gb.configure_column(
        highlight_column,
        headerName=highlight_column,
        editable=True,
        width=200,
        cellStyle=next_week_cell_style
    )

    # Set row style for the first three rows
    get_row_style = JsCode("""
    function(params) {
        if (params.node.rowIndex < 2) {
            return { 'background-color': '#f0f0f0' };
        }
        return null;
    }
    """)
    gb.configure_grid_options(getRowStyle=get_row_style)

    grid_options = gb.build()

    # Create form for saving changes
    with st.form("aggrid_form"):

        # Submit button
        _, col1, _ = st.columns([4, 2, 4])
        with col1:
            submitted = st.form_submit_button("Guardar cambios", use_container_width=True)

        # Add the AgGrid component
        grid_response = AgGrid(
            boost_assignation,
            gridOptions=grid_options,
            update_mode='MODEL_CHANGED',
            fit_columns_on_grid_load=True,
            height=650,
            allow_unsafe_jscode=True,
            reload_data=False,
            key='aggrid'
        )

        # Get the updated data
        updated_data = grid_response['data']
        st.session_state.edited_data = updated_data

    if submitted:
        save_changes()