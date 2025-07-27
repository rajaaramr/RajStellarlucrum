import streamlit as st
import datetime
import asyncio
import nest_asyncio
import gspread_asyncio
from google.oauth2.service_account import Credentials
from kiteconnect import KiteConnect
import os

# ✅ Allow nested loops (needed for Streamlit + asyncio)
nest_asyncio.apply()

# ✅ Google Sheets authentication
def get_creds():
    return Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
    )

agcm = gspread_asyncio.AsyncioGspreadClientManager(get_creds)

# ✅ Zerodha credentials from secrets
Z_API_KEY = st.secrets["zerodha"]["api_key"]
Z_API_SECRET = st.secrets["zerodha"]["api_secret"]
Z_REDIRECT_URL = st.secrets["zerodha"]["redirect_url"]

# ✅ Session state for access token
if "access_token" not in st.session_state:
    st.session_state.access_token = None

kite = KiteConnect(api_key=Z_API_KEY)

# ✅ Streamlit UI setup
st.set_page_config(page_title="RajTask 7 – Option Analytics Logger")
st.title("📊 RajTask 7 – Option Analytics Logger")
st.write("Click below to fetch Option Data and log it into **Sheet1** and **TrendHistory**.")

# ✅ Symbol input
user_symbol = st.text_input("Enter Stock Symbol or Index (e.g., NIFTY, RELIANCE, SBIN)", value="NIFTY").upper()

# ✅ Zerodha login
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

# ✅ Symbol mapping
def get_zerodha_symbol(user_symbol: str) -> str:
    index_map = {
        "NIFTY": "NSE:NIFTY 50",
        "BANKNIFTY": "NSE:NIFTY BANK",
        "FINNIFTY": "NSE:NIFTY FIN SERVICE",
        "MIDCPNIFTY": "NSE:NIFTY MIDCAP SELECT"
    }
    return index_map.get(user_symbol, f"NSE:{user_symbol}")

# ✅ Fetch live option data from Zerodha
def get_option_data_live(kite, user_symbol):
    try:
        instrument = get_zerodha_symbol(user_symbol)
        quote = kite.ltp(instrument)
        if instrument not in quote:
            st.error(f"⚠️ Symbol not found: {instrument}")
            return None

        spot_price = quote[instrument]["last_price"]
        instruments = kite.instruments("NFO")

        # Filter CE and PE
        ce, pe = None, None
        for inst in instruments:
            if inst["name"] == user_symbol and inst["instrument_type"] == "CE" and inst["strike"] >= spot_price:
                ce = inst
            if inst["name"] == user_symbol and inst["instrument_type"] == "PE" and inst["strike"] <= spot_price:
                pe = inst
            if ce and pe:
                break

        if not ce or not pe:
            st.error("⚠️ No matching CE/PE option found.")
            return None

        ce_ltp = kite.ltp(f"NFO:{ce['tradingsymbol']}")[f"NFO:{ce['tradingsymbol']}"]
        pe_ltp = kite.ltp(f"NFO:{pe['tradingsymbol']}")[f"NFO:{pe['tradingsymbol']}"]

        fut_inst = next((i for i in instruments if i["name"] == user_symbol and i["instrument_type"] == "FUT"), None)
        fut_quote = kite.ltp(f"NFO:{fut_inst['tradingsymbol']}")[f"NFO:{fut_inst['tradingsymbol']}"] if fut_inst else {}

        return [
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            user_symbol,
            spot_price,
            fut_quote.get("last_price", 0),
            fut_quote.get("oi", 0),
            fut_quote.get("oi_day_high", 0),
            ce_ltp["last_price"],
            ce_ltp["oi"],
            ce_ltp["oi_day_high"],
            pe_ltp["last_price"],
            pe_ltp["oi"],
            pe_ltp["oi_day_high"],
            ce_ltp["last_price"] + pe_ltp["last_price"],
            13.8,  # Replace with actual IV logic if available
            "Put Writing" if pe_ltp["oi_day_high"] > ce_ltp["oi_day_high"] else "Call Writing",
            "Only PE Change" if pe_ltp["oi_day_high"] > 1.5 * ce_ltp["oi_day_high"] else "Mixed",
            "Bullish Confirmation" if pe_ltp["oi_day_high"] > ce_ltp["oi_day_high"] else "Neutral"
        ]
    except Exception as e:
        st.error(f"❌ Error fetching option data: {e}")
        return None

# ✅ Get Google Sheets references
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

# ✅ Append to Sheets
async def append_data_to_sheets():
    sheet1, history_sheet = await get_sheets()
    if not sheet1 or not history_sheet:
        return

    data = get_option_data_live(kite, user_symbol)
    if not data:
        return

    try:
        await sheet1.append_row(data)
        snapshot_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        await history_sheet.append_row([snapshot_time] + data[1:])  # Avoid duplicating timestamp
        st.success("✅ Logged to Google Sheets.")
    except Exception as e:
        st.error(f"❌ Logging failed: {e}")

# ✅ Run on button click
if st.session_state.access_token:
    if st.button("📥 Fetch Option Data"):
        asyncio.run(append_data_to_sheets())
