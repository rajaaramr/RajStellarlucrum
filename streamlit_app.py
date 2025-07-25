import streamlit as st
import asyncio
from gspread_asyncio import AsyncioGspreadClientManager
from google.oauth2.service_account import Credentials
import datetime

# === Google Sheets Setup ===
def get_creds():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    return Credentials.from_service_account_info(st.secrets["google"], scopes=scopes)

agcm = AsyncioGspreadClientManager(get_creds)

async def get_worksheet():
    try:
        client = await agcm.authorize()
        spreadsheet = await client.open("RajTask7_OptionData")  # Make sure this matches your actual Google Sheet name
        worksheet = await spreadsheet.worksheet("Sheet1")       # Change "Sheet1" if your tab has a different name
        return worksheet
    except Exception as e:
        st.error(f"⚠️ Error accessing Google Sheets:\n\n{e}")
        return None

# === Option Data Fetcher ===
def fetch_option_data():
    # Dummy data for now – replace with actual option data fetch logic
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
        worksheet = asyncio.run(get_worksheet())
        if worksheet:
            asyncio.run(worksheet.append_row([
                data["timestamp"],
                data["CE_price"],
                data["PE_price"],
                data["IV"]
            ]))
            st.success("✅ Data successfully logged to Google Sheets.")
    except Exception as e:
        st.error(f"❌ Error writing to Google Sheets:\n\n{e}")
