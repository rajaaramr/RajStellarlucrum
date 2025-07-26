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

async def get_sheets():
    try:
        client = await agcm.authorize()
        gsheet = await client.open("RajTask7_OptionData")
        sheet1 = gsheet.worksheet("Sheet1")
        history_sheet = gsheet.worksheet("TrendHistory")
        return sheet1, history_sheet
    except Exception as e:
        st.error(f"⚠️ Error accessing Google Sheets: {e}")
        return None, None

# === Dummy Data Fetcher (Replace with real logic) ===
def fetch_option_data():
    return {
        "timestamp": str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
        "price": 23450.75,
        "fut_price": 23480.20,
        "fut_oi": 1152000,
        "delta_fut_oi": 21000,
        "ce_price": 120.5,
        "pe_price": 95.25,
        "ce_oi": 875000,
        "pe_oi": 720000,
        "delta_ce_oi": 18500,
        "delta_pe_oi": 11000,
        "iv": 16.7,
        "straddle": 215.75,
        "inference": "Long Buildup",
        "writer_bias": "Put Writing (Bullish)",
        "sentiment": "Bullish Confirmation"
    }

# === Streamlit App ===
st.title("RajTask 7 – Option Analytics Logger")
st.markdown("Click below to fetch Option Data and log it into **Sheet1** and **TrendHistory**.")

if st.button("📥 Fetch Option Data"):
    data = fetch_option_data()
    try:
        sheet1, history_sheet = asyncio.run(get_sheets())
        if sheet1 and history_sheet:
            row = [
                data["timestamp"], data["price"], data["fut_price"], data["fut_oi"], data["delta_fut_oi"],
                data["ce_price"], data["pe_price"], data["ce_oi"], data["pe_oi"],
                data["delta_ce_oi"], data["delta_pe_oi"], data["iv"], data["straddle"],
                data["inference"], data["writer_bias"], data["sentiment"]
            ]
            sheet1.append_row(row)
            history_sheet.append_row(row)
            st.success("✅ Logged data to both Sheet1 and TrendHistory.")
    except Exception as e:
        st.error(f"❌ Error logging to sheets:\n\n{e}")
