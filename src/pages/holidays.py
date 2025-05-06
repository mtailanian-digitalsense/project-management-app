import streamlit as st
import pandas as pd
import datetime
import os.path
from unidecode import unidecode
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

CALENDAR_ID = "hunf5b8n0rpad4o898t54h5trl69l66r@import.calendar.google.com"
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
MONTHS = [
    'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
    'Julio', 'Agosto', 'Setiembre', 'Octubre', 'Noviembre', 'Diciembre'
]

def show_holidays():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('calendar', 'v3', credentials=creds)

    events_result = service.events().list(
        calendarId=CALENDAR_ID,  # 'primary',
        timeMin='2025-01-01T00:00:00Z',
        timeMax='2025-12-31T23:59:59Z',
        maxResults=1000,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    events = events_result.get('items', [])

    # Create dataframe with events
    events_data = []
    for event in events:
        name = event.get('summary')
        start = event['start'].get('dateTime', event['start'].get('date'))
        end = event['end'].get('dateTime', event['end'].get('date'))
        status = event.get('status')
        events_data.append({'name': name, 'start': start, 'end': end, 'status': status})

    # Create a DataFrame with all holidays
    df = pd.DataFrame(events_data, columns=['name', 'start', 'end', 'status'])
    df = df.sort_values(by='name')
    df['name_sort'] = df['name'].apply(unidecode)
    df = df.sort_values(by=['name_sort']).drop(columns=['name_sort'])

    # _, col1, _ = st.columns([2, 3, 2])
    # with col1:
    #     st.dataframe(
    #         df,
    #         use_container_width=True,
    #         height=750,
    #         hide_index=True,
    #     )

    # How many days from each month are holidays
    holidays = df.join(
        df.apply(lambda p: pd.Series(pd.date_range(pd.to_datetime(p['start']), pd.to_datetime(p['end']) - pd.Timedelta(days=1), freq='B').to_period('M')), axis=1)
        .apply(lambda x: pd.Series(x).value_counts(), axis=1)
        .fillna(0)
        .astype(int)
    )
    ## Rename columns to Spanish month names
    holidays.columns = holidays.columns.astype(str)
    month_mapping = {f'2025-{i + 1:02d}': month for i, month in enumerate(MONTHS)}
    holidays.rename(columns=month_mapping, inplace=True)
    for month in MONTHS:
        if month not in holidays.columns:
            holidays[month] = 0
    columns_to_keep = ['name'] + MONTHS
    holidays = holidays[columns_to_keep]

    ## Group by name and sum
    holidays = holidays.groupby('name').sum().reset_index()
    holidays['name_sort'] = holidays['name'].apply(unidecode)
    holidays = holidays.sort_values(by=['name_sort']).reset_index().drop(columns=['name_sort', 'index'])

    # Style the table
    def highlight_rows(row):
        return ['background-color: #ffffff' if row.name % 2 == 0 else 'background-color: #f5f5f5' for _ in row]

    holidays_styled = holidays.style.apply(highlight_rows, axis=1)

    # _, col1, _ = st.columns([1, 4, 1])
    # with col1:
    st.dataframe(
        holidays_styled,
        use_container_width=True,
        height=750,
        hide_index=True,
        column_config={
            # 'name': {'width': 150},
            # **{month: {'width': 50} for month in MONTHS}
            "name": st.column_config.TextColumn("Nombre"),#, width="medium"),
            "Enero": st.column_config.NumberColumn("Enero"),#, width="small"),
            "Febrero": st.column_config.NumberColumn("Feb."),#, width="small"),
            "Marzo": st.column_config.NumberColumn("Marzo"),#, width="small"),
            "Abril": st.column_config.NumberColumn("Abril"),#, width="small"),
            "Mayo": st.column_config.NumberColumn("Mayo"),#, width="small"),
            "Junio": st.column_config.NumberColumn("Junio"),#, width="small"),
            "Julio": st.column_config.NumberColumn("Julio"),#, width="small"),
            "Agosto": st.column_config.NumberColumn("Agosto"),#, width="small"),
            "Setiembre": st.column_config.NumberColumn("Set."),#, width="small"),
            "Octubre": st.column_config.NumberColumn("Oct."),#, width="small"),
            "Noviembre": st.column_config.NumberColumn("Nov."),#, width="small"),
            "Diciembre": st.column_config.NumberColumn("Dic."),#, width="small"),

        },
    )


if __name__ == '__main__':
    show_holidays()