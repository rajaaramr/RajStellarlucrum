import streamlit as st
import datetime
import asyncio
import nest_asyncio
import gspread_asyncio
from google.oauth2.service_account import Credentials

# Required for nested event loops in Streamlit
nest_asyncio.apply()

# ---- ✅ Google Sheets Credentials using st.secrets ----
def get_creds():
    return Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
    )

# ---- ✅ Create Async Client Manager ----
agcm = gspread_asyncio.AsyncioGspreadClientManager(get_creds)

# ---- Streamlit UI ----
st.set_page_config(page_title="RajTask 7 – Option Analytics Logger")
st.title("📊 RajTask 7 – Option Analytics Logger")
st.write("Click below to fetch Option Data and log it into **Sheet1** and **TrendHistory**.")

# ---- 🔧 Dummy Option Data Function (Replace with Zerodha API later) ----
def get_option_data():
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return [
        now,                        # Timestamp
        "NIFTY",  		    # Symbol (B) ✅ ADD THIS	
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
        "Put Writing (Bullish)",    # Inference (O)
        "Only PE Change",           # Option Writer Bias (P) ✅ ADD
        "Bullish Confirmation"      # Market Sentiment (Q) ✅ ADD
    ]

# ---- 🗂️ Access Sheets ----
async def get_sheets():
    try:
        client = await agcm.authorize()
        gsheet = await client.open("RajTask7_OptionData")
        sheet1 = await gsheet.worksheet("Sheet1")
        history_sheet = await gsheet.worksheet("TrendHistory")
        return sheet1, history_sheet
    except Exception as e:
        st.error(f"⚠️ Error accessing Google Sheets: {e}")
        return None, None

# ---- 📝 Append Data to Sheets ----
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

# ---- 📥 Button Trigger ----
if st.button("📥 Fetch Option Data"):
    asyncio.run(append_data_to_sheets())
