import streamlit as st
import pandas as pd
import gspread_asyncio
from google.oauth2.service_account import Credentials
import asyncio

st.set_page_config(page_title="RajTask 7 – Option Analytics HUD", layout="centered")
st.title("RajTask 7 – Option Analytics HUD")
st.markdown("Click the button below to fetch CE/PE and IV, and log it to Google Sheets.")

# --- STEP 1: Setup Google Sheets Access ---
def get_gsheet():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    creds_dict = st.secrets["google"]  # Make sure this is configured in Streamlit Cloud
    credentials = Credentials.from_service_account_info(creds_dict, scopes=scope)

    agcm = gspread_asyncio.AsyncioGspreadClientManager(lambda: credentials)
    client_future = agcm.get_client()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    client = loop.run_until_complete(client_future)
    spreadsheet = loop.run_until_complete(client.open("RajTask7_OptionData"))
    worksheet = loop.run_until_complete(spreadsheet.worksheet("Sheet1"))
    
    return worksheet

# --- STEP 2: Dummy Option Data (Replace with real logic) ---
def fetch_option_data():
    # Dummy DataFrame – Replace this with actual option chain data
    df = pd.DataFrame({
        "Strike Price": [19500, 19600, 19700],
        "CE Price": [105.5, 82.4, 67.0],
        "PE Price": [95.2, 108.1, 121.6],
        "IV (%)": [14.2, 13.9, 13.5]
    })
    return df

# --- STEP 3: Write to Google Sheet ---
def write_to_gsheet(sheet, df):
    sheet.clear()
    sheet.update([df.columns.values.tolist()] + df.values.tolist())

# --- STEP 4: UI Button ---
if st.button("📥 Fetch Option Data"):
    try:
        sheet = get_gsheet()
        df = fetch_option_data()
        write_to_gsheet(sheet, df)
        st.success("✅ Data written to Google Sheet successfully!")
        st.dataframe(df)
    except Exception as e:
        st.error(f"❌ Error writing to Google Sheets:\n\n{str(e)}")
