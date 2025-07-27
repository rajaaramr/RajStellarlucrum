import streamlit as st
import datetime
from kiteconnect import KiteConnect
import gspread_asyncio
from google.oauth2.service_account import Credentials
import pandas as pd
import nest_asyncio
import os

nest_asyncio.apply()

# === CONFIG ===
API_KEY = st.secrets["zerodha"]["api_key"]
API_SECRET = st.secrets["zerodha"]["api_secret"]
REDIRECT_URL = st.secrets["zerodha"]["redirect_url"]
TOKEN_PATH = "access_token.txt"

# === Zerodha Kite Setup ===
kite = KiteConnect(api_key=API_KEY)

def save_access_token(token):
    with open(TOKEN_PATH, "w") as f:
        f.write(token)

def load_access_token():
    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, "r") as f:
            return f.read().strip()
    return None

# === Google Sheets Auth ===
def get_creds():
    return Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=["https://www.googleapis.com/auth/spreadsheets"])

agcm = gspread_asyncio.AsyncioGspreadClientManager(get_creds)

async def get_sheets():
    agc = await agcm.authorize()
    sh = await agc.open("OptionAnalytics")
    return await sh.worksheet("Sheet1"), await sh.worksheet("TrendHistory")

# === Data Fetching ===
def get_option_data_live(kite, user_symbol):
    try:
        quote_data = kite.quote([f"NSE:{user_symbol}", f"NFO:{user_symbol}24JULFUT"])
        spot_price = quote_data[f"NSE:{user_symbol}"]["last_price"]
        fut_price = quote_data[f"NFO:{user_symbol}24JULFUT"]["last_price"]
        fut_oi = quote_data[f"NFO:{user_symbol}24JULFUT"]["oi"]
        fut_oi_chg = quote_data[f"NFO:{user_symbol}24JULFUT"]["oi_day_high"] - quote_data[f"NFO:{user_symbol}24JULFUT"]["oi_day_low"]

        # Fetch Option Chain
        instruments = kite.instruments("NFO")
        ce_option = next(i for i in instruments if i["name"] == user_symbol and i["instrument_type"] == "CE" and abs(i["strike"] - spot_price) <= 100)
        pe_option = next(i for i in instruments if i["name"] == user_symbol and i["instrument_type"] == "PE" and i["strike"] == ce_option["strike"])

        ce_data = kite.quote(ce_option["tradingsymbol"])[ce_option["tradingsymbol"]]
        pe_data = kite.quote(pe_option["tradingsymbol"])[pe_option["tradingsymbol"]]

        ce_price = ce_data["last_price"]
        ce_oi = ce_data["oi"]
        ce_oi_chg = ce_data["oi_day_high"] - ce_data["oi_day_low"]

        pe_price = pe_data["last_price"]
        pe_oi = pe_data["oi"]
        pe_oi_chg = pe_data["oi_day_high"] - pe_data["oi_day_low"]

        iv = round((ce_price + pe_price) / spot_price * 100, 2)

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
        st.error(f"❌ Error fetching option data: {e}")
        return None

# === Data Append Logic ===
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
        await history_sheet.append_row([snapshot_time] + data[1:])
        st.success("✅ Logged to Google Sheets.")
    except Exception as e:
        st.error(f"❌ Logging failed: {e}")

# === Streamlit UI ===
st.title("📊 RajTask 7 – Option Analytics Logger")
st.markdown("Click below to fetch Option Data and log it into **Sheet1** and **TrendHistory**.")

user_symbol = st.text_input("Enter Stock Symbol or Index (e.g., NIFTY, RELIANCE, SBIN)", "NIFTY").strip().upper()

if st.button("📉 Fetch Option Data"):
    access_token = load_access_token()
    if not access_token:
        login_url = kite.login_url()
        st.error("🔐 You are not authenticated. Please login via: [Login Link](%s)" % login_url)
    else:
        kite.set_access_token(access_token)
        st.write(f"Fetching live data for: `{user_symbol}`")
        st.toast("📡 Fetching & Logging Option Data...", icon="📈")
        st.experimental_rerun()
