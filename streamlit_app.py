
import streamlit as st
import datetime
import asyncio
import nest_asyncio
import gspread_asyncio
from google.oauth2.service_account import Credentials
from kiteconnect import KiteConnect
import os

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

# ✅ Load Zerodha Config
Z_API_KEY = st.secrets["zerodha"]["api_key"]
Z_API_SECRET = st.secrets["zerodha"]["api_secret"]
Z_REDIRECT_URL = st.secrets["zerodha"]["redirect_url"]

# ✅ Setup session state
if "access_token" not in st.session_state:
    st.session_state.access_token = None

kite = KiteConnect(api_key=Z_API_KEY)

# ---- 🖥️ Streamlit UI ----
st.set_page_config(page_title="RajTask 7 – Option Analytics Logger")
st.title("📊 RajTask 7 – Option Analytics Logger")
st.write("Click below to fetch Option Data and log it into **Sheet1** and **TrendHistory**.")

# --- 📈 Symbol Input ---
user_symbol = st.text_input("Enter Stock Symbol or Index (e.g., NIFTY, RELIANCE, SBIN)", value="NIFTY").upper()

# ---- 🔐 Step 1: Zerodha Login ----
if not st.session_state.access_token:
    login_url = kite.login_url()
    st.write("🔐 Click below to login to Zerodha and get the Request Token:")
    st.markdown(f"[Login to Zerodha]({login_url})", unsafe_allow_html=True)
    request_token = st.text_input("Paste the Request Token here:")

    if request_token:
        try:
            session_data = kite.generate_session(request_token, api_secret=Z_API_SECRET)
            kite.set_access_token(session_data["access_token"])
            st.session_state.access_token = session_data["access_token"]
            st.success("✅ Zerodha login successful. You can now fetch live data.")
        except Exception as e:
            st.error(f"❌ Failed to authenticate: {e}")
else:
    kite.set_access_token(st.session_state.access_token)

# ✅ Symbol Mapping Helper
def get_zerodha_symbol(user_symbol: str) -> str:
    index_map = {
        "NIFTY": "NSE:NIFTY 50",
        "BANKNIFTY": "NSE:NIFTY BANK",
        "FINNIFTY": "NSE:NIFTY FIN SERVICE",
        "MIDCPNIFTY": "NSE:NIFTY MIDCAP SELECT"
    }
    return index_map.get(user_symbol, f"NSE:{user_symbol}")

# ✅ Zerodha Option Data Fetcher
def get_option_data_live(kite, user_symbol):
    try:
        instrument = get_zerodha_symbol(user_symbol)
        quote = kite.ltp(instrument)
        if instrument not in quote:
            st.error(f"⚠️ Symbol not found: {instrument}")
            return None
        ltp = quote[instrument]["last_price"]
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return [
            now,
            user_symbol,
            ltp,
            22520,
            153250,
            1200,
            215,
            58000,
            500,
            250,
            63000,
            200,
            465,
            13.8,
            "Put Writing (Bullish)",
            "Only PE Change",
            "Bullish Confirmation"
        ]
    except Exception as e:
        st.error(f"❌ Error fetching LTP for {user_symbol}: {e}")
        return None

# ---- 📂 Google Sheet Access ----
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

# ---- 📤 Append Data Logic ----
async def append_data_to_sheets():
    sheet1, history_sheet = await get_sheets()
    if not sheet1 or not history_sheet:
        return

    data = get_option_data_live(kite, user_symbol)
    if not data:
        return

    try:
        await sheet1.append_row(data)
        snapshot = [datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")] + data
        await history_sheet.append_row(snapshot)
        st.success("✅ Data successfully logged to Google Sheets and archived.")
    except Exception as e:
        st.error(f"❌ Error logging to sheets: {e}")

# ---- 🚀 Run on Button Press ----
if st.session_state.access_token:
    if st.button("📥 Fetch Option Data"):
        asyncio.run(append_data_to_sheets())
