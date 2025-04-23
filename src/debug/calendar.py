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

now = datetime.datetime.utcnow().isoformat() + 'Z'
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
print(df)