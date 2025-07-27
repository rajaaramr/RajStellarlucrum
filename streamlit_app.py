import streamlit as st
import datetime
import asyncio
import nest_asyncio
import gspread_asyncio
from google.oauth2.service_account import Credentials
from kiteconnect import KiteConnect
from dateutil import parser
import os

# Required to enable nested loops
nest_asyncio.apply()

# --- Google Sheets Credentials ---
def get_creds():
    return Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
    )

agcm = gspread_asyncio.AsyncioGspreadClientManager(get_creds)

# --- Zerodha API Secrets ---
Z_API_KEY = st.secrets["zerodha"]["api_key"]
Z_API_SECRET = st.secrets["zerodha"]["api_secret"]
Z_REDIRECT_URL = st.secrets["zerodha"]["redirect_url"]

# --- Session Init ---
if "access_token" not in st.session_state:
    st.session_state.access_token = None

kite = KiteConnect(api_key=Z_API_KEY)

# --- Streamlit UI ---
st.set_page_config(page_title="RajTask 7 – Option Analytics Logger")
st.title("📊 RajTask 7 – Option Analytics Logger")
st.write("Click below to fetch Option Data and log it into **Sheet1** and **TrendHistory**.")

user_symbol = st.text_input("Enter Stock Symbol or Index (e.g., NIFTY, RELIANCE, SBIN)", value="NIFTY").upper()

# --- Zerodha Login ---
if not st.session_state.access_token:
    login_url = kite.login_url()
    st.markdown(f"[🔐 Login to Zerodha]({login_url})", unsafe_allow_html=True)
    request_token = st.text_input("Paste the Request Token from URL after login:")
    if request_token:
        try:
            session_data = kite.generate_session(request_token, api_secret=Z_API_SECRET)
            kite.set_access_token(session_data["access_token"])
            st.session_state.access_token = session_data["access_token"]
            st.success("✅ Zerodha login successful.")
        except Exception as e:
            st.error(f"❌ Login failed: {e}")
else:
    kite.set_access_token(st.session_state.access_token)

# --- Symbol Mapper ---
def get_zerodha_symbol(user_symbol: str) -> str:
    index_map = {
        "NIFTY": "NSE:NIFTY 50",
        "BANKNIFTY": "NSE:NIFTY BANK",
        "FINNIFTY": "NSE:NIFTY FIN SERVICE",
        "MIDCPNIFTY": "NSE:NIFTY MIDCAP SELECT"
    }
    return index_map.get(user_symbol, f"NSE:{user_symbol}")

# --- Real Option & Futures Data Fetch ---
def get_option_data_live(kite, user_symbol):
    try:
        symbol = get_zerodha_symbol(user_symbol)
        ltp_data = kite.ltp(symbol)
        spot_price = ltp_data[symbol]['last_price']
        

	instruments = kite.instruments("NFO")
	expiries = sorted(list(set([i["expiry"] for i in instruments if i["name"] == user_symbol and i["segment"] == "NFO-OPT"])))
	expiry_str = expiries[0]
	expiry_date = parser.parse(expiry_str) if isinstance(expiry_str, str) else expiry_str


        # Get CE/PE near ATM data (rounded ATM strike)
        atm_strike = round(spot_price / 100) * 100
        ce_symbol = f"NFO:{user_symbol}{expiry_date.strftime('%y%b').upper()}{atm_strike}CE"
	pe_symbol = f"NFO:{user_symbol}{expiry_date.strftime('%y%b').upper()}{atm_strike}PE"
	fut_symbol = f"NFO:{user_symbol}{expiry_date.strftime('%y%b').upper()}FUT"


        quote = kite.quote([ce_symbol, pe_symbol, fut_symbol])

        ce_price = quote[ce_symbol]['last_price']
        pe_price = quote[pe_symbol]['last_price']
        ce_oi = quote[ce_symbol]['oi']
        pe_oi = quote[pe_symbol]['oi']
        ce_oi_chg = quote[ce_symbol]['oi_day_high'] - quote[ce_symbol]['oi_day_low']
        pe_oi_chg = quote[pe_symbol]['oi_day_high'] - quote[pe_symbol]['oi_day_low']
        fut_price = quote[fut_symbol]['last_price']
        fut_oi = quote[fut_symbol]['oi']
        fut_oi_chg = quote[fut_symbol]['oi_day_high'] - quote[fut_symbol]['oi_day_low']
        iv = quote[ce_symbol].get("implied_volatility", 0)

        return [
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            user_symbol,
            spot_price,
            fut_price,
            fut_oi,
            fut_oi_chg,
            ce_price,
            ce_oi,
            ce_oi_chg,
            pe_price,
            pe_oi,
            pe_oi_chg,
            ce_price + pe_price,     # Straddle Price
            iv,
            "Put Writing" if pe_oi_chg > ce_oi_chg else "Call Writing",
            "Only PE Change" if pe_oi_chg > 1.5 * ce_oi_chg else "Mixed",
            "Bullish Confirmation" if pe_oi_chg > ce_oi_chg else "Neutral"
        ]
    except Exception as e:
        st.error(f"❌ Error: {e}")
        return None

# --- Google Sheet Access ---
async def get_sheets():
    try:
        client = await agcm.authorize()
        gsheet = await client.open("RajTask7_OptionData")
        sheet1 = await gsheet.worksheet("Sheet1")
        history_sheet = await gsheet.worksheet("TrendHistory")
        return sheet1, history_sheet
    except Exception as e:
        st.error(f"❌ Sheet access failed: {e}")
        return None, None

# --- Data Append Logic ---
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

# --- Button Action ---
if st.session_state.access_token:
    if st.button("📥 Fetch Option Data"):
        asyncio.run(append_data_to_sheets())
