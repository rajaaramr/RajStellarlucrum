import streamlit as st
import asyncio
from gspread_asyncio import AsyncioGspreadClientManager
from google.oauth2.service_account import Credentials
import datetime

# === Google Sheets Setup ===
from google.oauth2.service_account import Credentials

def get_creds():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"  # Needed to read/write sheets or use file access
    ]
    return Credentials.from_service_account_info(st.secrets["google"], scopes=scopes)

agcm = AsyncioGspreadClientManager(get_creds)

async def get_gsheet():
    try:
        client = await agcm.authorize()
        sheet = (await client.open("RajTask7_OptionData")).sheet1
        return sheet
    except Exception as e:
        st.error(f"⚠️ Error accessing Google Sheets: {e}")
        return None

# === Option Data Fetcher ===
def fetch_option_data():
    # Dummy example, replace with actual option logic
    return {
        "timestamp": str(datetime.datetime.now()),
        "CE_price": 123.45,
        "PE_price": 98.76,
        "IV": 22.5
    }

# === Main Streamlit App ===
st.title("RajTask 7 – Option Analytics HUD")
st.markdown("Click the button below to fetch CE/PE and IV, and log it to Google Sheets.")

if st.button("📥 Fetch Option Data"):
    data = fetch_option_data()
    try:
        sheet = asyncio.run(get_gsheet())
        if sheet:
            sheet.append_row([data["timestamp"], data["CE_price"], data["PE_price"], data["IV"]])
            st.success("✅ Data successfully logged to Google Sheets.")
    except Exception as e:
        st.error(f"❌ Error writing to Google Sheets:\n\n'{e}'")
