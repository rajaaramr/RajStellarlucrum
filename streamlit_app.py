import streamlit as st
from datetime import datetime
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# === CONFIGURATION ===
SHEET_NAME = "RajTask7_OptionData"
SYMBOL = "NIFTY"  # Change this if you're processing multiple symbols dynamically

# === GOOGLE SHEET SETUP ===
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("gdrive_secret.json", scope)
client = gspread.authorize(creds)
sheet = client.open(SHEET_NAME).sheet1

# === STREAMLIT SETUP ===
st.title("RajTask 7 – Option Analytics HUD")
st.markdown("Click the button below to fetch CE/PE and IV, and log it to Google Sheets.")
btn = st.button("📥 Fetch Option Data")

# === MOCK FETCH FUNCTIONS (Replace with real API calls) ===
def fetch_option_data():
    return {
        "futures_price": 22475,
        "futures_oi": 167000,
        "futures_oi_delta": -3000,
        "ce_price": 120,
        "ce_oi": 110000,
        "ce_oi_delta": -2500,
        "pe_price": 130,
        "pe_oi": 140000,
        "pe_oi_delta": 3000,
        "iv": 13.5
    }

def compute_inference(ce_price, pe_price):
    if ce_price > 140 and pe_price > 140:
        return "Straddle High", "Volatile", "Writers Cautious"
    elif ce_price < 80 and pe_price < 80:
        return "Price Flat", "Only PE Change Mixed", "No Clear Bias"
    elif ce_price < 80 and pe_price > 120:
        return "PE Rising", "Bearish Bias", "Put Writers Aggressive"
    else:
        return "Price Flat", "Only PE Change Mixed", "No Clear Bias"

# === MAIN ACTION ===
if btn:
    data = fetch_option_data()

    # === Derived Metrics ===
    straddle_price = data["ce_price"] + data["pe_price"]
    inference, bias, sentiment = compute_inference(data["ce_price"], data["pe_price"])
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    row = [
        SYMBOL,
        timestamp,
        data["futures_price"],
        data["futures_oi"],
        data["futures_oi_delta"],
        data["ce_price"],
        data["ce_oi"],
        data["ce_oi_delta"],
        data["pe_price"],
        data["pe_oi"],
        data["pe_oi_delta"],
        straddle_price,
        data["iv"],
        inference,
        bias,
        sentiment
    ]

    sheet.append_row(row)
    st.success("✅ Data successfully logged to Google Sheets.")
