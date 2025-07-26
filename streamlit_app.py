import streamlit as st
import asyncio
from gspread_asyncio import AsyncioGspreadClientManager
from google.oauth2.service_account import Credentials
import datetime

# === Google Sheets Credentials from Streamlit Secrets ===
def get_creds():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    return Credentials.from_service_account_info(st.secrets["google"], scopes=scopes)

# === Setup gspread_asyncio client ===
agcm = AsyncioGspreadClientManager(get_creds)

# === Access Sheet ===
async def get_gsheet():
    try:
        client = await agcm.authorize()
        sheet = (await client.open("RajTask7_OptionData")).sheet1
        return sheet
    except Exception as e:
        st.error(f"⚠️ Error accessing Google Sheets: {e}")
        return None

# === Option Data Fetcher (you can later pull real-time data here) ===
def fetch_option_data():
    return {
        "timestamp": str(datetime.datetime.now()),
        "stock_name": "NIFTY",  # Future enhancement: dynamic symbol
        "underlying_price": 22200,
        "future_price": 22230,
        "CE_price": 140.25,
        "PE_price": 135.70,
        "IV": 21.4,
        "CE_OI": 32000,
        "PE_OI": 38000,
        "Fut_OI": 590000
    }

# === UI Layout ===
st.title("📊 RajTask 7 – Option Analytics HUD")
st.markdown("Click to fetch CE/PE prices, OI, IV, and Futures reference into Google Sheets.")

# === Button Trigger ===
if st.button("📥 Fetch Option Data"):
    data = fetch_option_data()

    # Attempt writing to sheet
    try:
        sheet = asyncio.run(get_gsheet())
        if sheet:
            sheet.append_row([
                data["timestamp"],
                data["stock_name"],
                data["underlying_price"],
                data["future_price"],
                data["CE_price"],
                data["PE_price"],
                data["IV"],
                data["CE_OI"],
                data["PE_OI"],
                data["Fut_OI"]
            ])
            st.success("✅ Data successfully logged to Google Sheets.")
    except Exception as e:
        st.error(f"❌ Error writing to Google Sheets:\n\n{e}")
