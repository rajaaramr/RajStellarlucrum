import streamlit as st
import datetime
import asyncio
import nest_asyncio
import gspread_asyncio
from google.oauth2.service_account import Credentials

# ✅ Required for nested event loops in Streamlit
nest_asyncio.apply()

# ---- ✅ Google Sheets Credentials from st.secrets ----
def get_creds():
    return Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
    )

# ✅ Create Async Client Manager
agcm = gspread_asyncio.AsyncioGspreadClientManager(get_creds)

# ---- 🖥️ Streamlit UI ----
st.set_page_config(page_title="RajTask 7 – Option Analytics Logger")
st.title("📊 RajTask 7 – Option Analytics Logger")
st.write("Click below to fetch Option Data and log it into **Sheet1** and **TrendHistory**.")

# ---- 🔧 Dummy Option Data Generator (to be replaced by Zerodha API) ----
def get_option_data():
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return [
        now,                        # A: Timestamp
        "NIFTY",                    # B: Symbol
        22450,                      # C: Spot Price
        22520,                      # D: Futures Price
        153250,                     # E: Futures OI
        1200,                       # F: Futures OI Δ
        215,                        # G: CE Price
        58000,                      # H: CE OI
        500,                        # I: CE OI Δ
        250,                        # J: PE Price
        63000,                      # K: PE OI
        200,                        # L: PE OI Δ
        465,                        # M: Straddle Price
        13.8,                       # N: IV
        "Put Writing (Bullish)",   # O: Inference
        "Only PE Change",          # P: Option Writer Bias
        "Bullish Confirmation"     # Q: Market Sentiment
    ]

# ---- 📂 Google Sheet Access ----
async def get_sheets():
    try:
        client = await agcm.authorize()
        gsheet = await client.open("RajTask7_OptionData")
        sheet1 = await gsheet.worksheet("Sheet1")           # Ensure exact spelling
        history_sheet = await gsheet.worksheet("TrendHistory")
        return sheet1, history_sheet
    except Exception as e:
        st.error(f"⚠️ Error accessing Google Sheets: {e}")
        return None, None

# ---- 📤 Append Data Logic ----
async def append_data_to_sheets():
    sheet1, history_sheet = await get_sheets()
    if not sheet1 or not history_sheet:
        return

    data = get_option_data()
    
    # ✅ Debug output
    st.write("🧪 Row Preview:", data)
    st.write("✅ Row Length:", len(data))  # Expect 17

    try:
        await sheet1.append_row(data, value_input_option="USER_ENTERED")
        await history_sheet.append_row(data, value_input_option="USER_ENTERED")
        st.success("✅ Data successfully logged to Google Sheets.")
    except Exception as e:
        st.error(f"❌ Error logging to sheets: {e}")

# ---- 🚀 Run on Button Press ----
if st.button("📥 Fetch Option Data"):
    asyncio.run(append_data_to_sheets())
