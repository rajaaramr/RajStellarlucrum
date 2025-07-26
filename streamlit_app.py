import streamlit as st
import datetime
import asyncio
import nest_asyncio
import gspread_asyncio
from oauth2client.service_account import ServiceAccountCredentials
from google.oauth2.service_account import Credentials

import json

# ✅ Properly define get_creds to load from st.secrets
def get_creds():
    return Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )

# ✅ Create the async client manager correctly
agcm = gspread_asyncio.AsyncioGspreadClientManager(get_creds)


# Required for running async loops in Streamlit
nest_asyncio.apply()


# ---- Google Sheet Auth Setup ----

def get_gspread_client():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    credentials_dict = st.secrets["gcp_service_account"]
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(json.loads(credentials_dict.to_json()), scope)
    return gspread_asyncio.AsyncioGspreadClientManager(lambda: credentials)


agcm = gspread_asyncio.AsyncioGspreadClientManager(get_creds)

# ---- UI ----
st.set_page_config(page_title="RajTask 7 – Option Analytics Logger")
st.title("📊 RajTask 7 – Option Analytics Logger")
st.write("Click below to fetch Option Data and log it into **Sheet1** and **TrendHistory**.")

# ---- Dummy Data (Replace with Zerodha API later) ----
def get_option_data():
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return [
        now,                        # Timestamp
        22450,                      # Spot Price
        22520,                      # Futures Price
        153250,                     # Futures OI
        1200,                       # Futures OI Δ
        215,                        # CE Price
        250,                        # PE Price
        58000,                      # CE OI
        63000,                      # PE OI
        500,                        # CE OI Δ
        200,                        # PE OI Δ
        465,                        # Straddle Price
        13.8,                       # IV %
        "Put Writing (Bullish)",   # Inference
        "Bullish Confirmation"     # Market Sentiment
    ]

# ---- Google Sheet Access ----
async def get_sheets():
    try:
        client = await agcm.authorize()
        gsheet = await client.open("RajTask7_OptionData")
        sheet1 = await gsheet.worksheet("Sheet1")             # ✅ FIXED: use await
        history_sheet = await gsheet.worksheet("TrendHistory")
        return sheet1, history_sheet
    except Exception as e:
        st.error(f"⚠️ Error accessing Google Sheets: {e}")
        return None, None

# ---- Append Row Logic ----
async def append_data_to_sheets():
    sheet1, history_sheet = await get_sheets()
    if not sheet1 or not history_sheet:
        return

    data = get_option_data()

    try:
        await sheet1.append_row(data)
        await history_sheet.append_row(data)
        st.success("✅ Data successfully logged to Google Sheets.")
    except Exception as e:
        st.error(f"❌ Error logging to sheets: {e}")

# ---- Button to Trigger ----
if st.button("📥 Fetch Option Data"):
    asyncio.run(append_data_to_sheets())
