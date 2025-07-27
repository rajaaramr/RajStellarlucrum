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

# ✅ Fetch live option data from Zerodha using kite.quote()
def get_option_data_live(kite, user_symbol):
    try:
        instrument = get_zerodha_symbol(user_symbol)
        quote = kite.quote([instrument])
        if instrument not in quote:
            st.error(f"⚠️ Symbol not found: {instrument}")
            return None

        spot_price = quote[instrument]["last_price"]

        # Get instrument list for NFO
        instruments = kite.instruments("NFO")
        # Closest strike logic (find ATM options)
        strikes = sorted(set(i["strike"] for i in instruments if i["name"] == user_symbol and i["instrument_type"] in ["CE", "PE"]))
        atm_strike = min(strikes, key=lambda s: abs(s - spot_price))

        # Get CE and PE instrument details
        ce_inst = next((i for i in instruments if i["name"] == user_symbol and i["instrument_type"] == "CE" and i["strike"] == atm_strike), None)
        pe_inst = next((i for i in instruments if i["name"] == user_symbol and i["instrument_type"] == "PE" and i["strike"] == atm_strike), None)

        if not ce_inst or not pe_inst:
            st.error("⚠️ No matching CE/PE option found.")
            return None

        ce_symbol = f"NFO:{ce_inst['tradingsymbol']}"
        pe_symbol = f"NFO:{pe_inst['tradingsymbol']}"
        fut_inst = next((i for i in instruments if i["name"] == user_symbol and i["instrument_type"] == "FUT"), None)
        fut_symbol = f"NFO:{fut_inst['tradingsymbol']}" if fut_inst else None

        # Get full quote data for CE, PE, and FUT
        quote_all = kite.quote([ce_symbol, pe_symbol] + ([fut_symbol] if fut_symbol else []))

        ce_data = quote_all.get(ce_symbol, {})
        pe_data = quote_all.get(pe_symbol, {})
        fut_data = quote_all.get(fut_symbol, {}) if fut_symbol else {}

        # Prepare return row
        return [
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            user_symbol,
            spot_price,
            fut_data.get("last_price", 0),
            fut_data.get("oi", 0),
            fut_data.get("oi_day_high", 0),
            ce_data.get("last_price", 0),
            ce_data.get("oi", 0),
            ce_data.get("oi_day_high", 0),
            pe_data.get("last_price", 0),
            pe_data.get("oi", 0),
            pe_data.get("oi_day_high", 0),
            ce_data.get("last_price", 0) + pe_data.get("last_price", 0),
            13.8,  # Replace with real IV calc later
            "Put Writing" if pe_data.get("oi_day_high", 0) > ce_data.get("oi_day_high", 0) else "Call Writing",
            "Only PE Change" if pe_data.get("oi_day_high", 0) > 1.5 * ce_data.get("oi_day_high", 0) else "Mixed",
            "Bullish Confirmation" if pe_data.get("oi_day_high", 0) > ce_data.get("oi_day_high", 0) else "Neutral"
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
