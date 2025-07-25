import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

st.set_page_config(page_title="RajTask 7 – Option Analytics HUD", layout="centered")

st.title("RajTask 7 – Option Analytics HUD")
st.write("Click the button below to fetch CE/PE and IV, and log it to Google Sheets.")

# === Setup Google Sheets Access ===
def get_gsheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["google"], scope)
    client = gspread.authorize(creds)
    sheet = client.open("RajTask7_OptionData").sheet1  # Make sure your sheet name matches this
    return sheet

# === Simulated data fetch (can later replace with Zerodha API) ===
def fetch_option_data():
    spot = 24100
    atm_strike = 24100
    ce = 145.25
    pe = 160.80
    iv = 12.8
    straddle = ce + pe
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return [timestamp, spot, atm_strike, ce, pe, straddle, iv]

# === Main Button Action ===
if st.button("🔁 Fetch Option Data"):
    row = fetch_option_data()
    sheet = get_gsheet()
    sheet.append_row(row)
    st.success(f"✅ Data written to Google Sheet: {row}")
