# Run
```bash
streamlit run src/app.py
```

# Create env
```bash
conda create -n project-management python=3.11
conda activate project-management
pip install -r requirements.txt
```

# Subscribe to the calendar

1. Go to [Google Cloud Console](https://console.cloud.google.com/welcome?pli=1&inv=1&invt=AbqhwA&project=diffusion-426801)
2. Create or select a project
3. Navigate to the API & Services Dashboard: In the left-hand navigation menu, click on "APIs & Services". Then click on "Credentials".
4. Create Credentials: Click on the "Create credentials" button at the top of the page. Select "API key" from the dropdown menu.

Also enable Google Calendar API, from the Enabled APIs & services menu.

Go to the Google Cloud Console.
Select your project or create a new one.
Navigate to "APIs & Services" > "Credentials".
Click "Create credentials" and select "OAuth 2.0 Client IDs".
Configure the consent screen and create the OAuth 2.0 client ID.
Download the credentials.json file.