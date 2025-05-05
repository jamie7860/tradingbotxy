import os
import time
import requests
import pandas as pd
from smartapi import SmartConnect
from flask import Flask
from datetime import datetime
from threading import Thread

app = Flask(__name__)

@app.route('/')
def home():
    return "Spike Bot is running!"

def run_flask():
    app.run(host='0.0.0.0', port=10000)

# ENVIRONMENT VARIABLES
API_KEY = os.getenv("API_KEY")
CLIENT_ID = os.getenv("CLIENT_ID")
PASSWORD = os.getenv("PASSWORD")
TOTP = os.getenv("TOTP")
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

smartapi = SmartConnect(api_key=API_KEY)

def telegram_alert(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print("Telegram error:", e)

def login():
    try:
        session = smartapi.generateSession(CLIENT_ID, PASSWORD, TOTP)
        return session["data"]["refreshToken"]
    except Exception as e:
        print("Login failed:", e)

def get_instruments():
    try:
        df = pd.read_csv("https://margincalc.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.csv")
        return df[df['Exchange'] == 'NFO']
    except:
        return pd.DataFrame()

def get_ltp(symbol_token):
    try:
        data = smartapi.ltpData("NFO", "NIFTY", symbol_token)
        return float(data['data']['ltp'])
    except:
        return 0.0

def place_order(symbol_token):
    try:
        smartapi.placeOrder({
            "variety": "NORMAL",
            "tradingsymbol": symbol_token,
            "symboltoken": symbol_token,
            "transactiontype": "BUY",
            "exchange": "NFO",
            "ordertype": "MARKET",
            "producttype": "INTRADAY",
            "duration": "DAY",
            "quantity": 1
        })
        telegram_alert(f"Order Placed for {symbol_token}")
    except Exception as e:
        print("Order Failed:", e)
        telegram_alert(f"Order Failed: {e}")

def monitor_spikes():
    login()
    instrument_df = get_instruments()
    options = instrument_df[instrument_df['Name'].str.contains("NIFTY|BANKNIFTY") & instrument_df['Symbol'].str.endswith("CE")]

    tracked = {}

    while True:
        for _, row in options.iterrows():
            symbol = row['Symbol']
            token = row['Token']
            ltp = get_ltp(token)

            if ltp == 0:
                continue

            now = datetime.now().strftime("%H:%M:%S")
            if token not in tracked:
                tracked[token] = {"price": ltp, "volume": row.get('Lotsize', 1), "time": now}
                continue

            old = tracked[token]
            price_change = ltp - old["price"]

            if price_change >= 0.30:
                message = f"Spike Detected: {symbol}\nPrice: {old['price']} -> {ltp}\nTime: {now}"
                telegram_alert(message)
                place_order(token)
                tracked[token] = {"price": ltp, "volume": row.get('Lotsize', 1), "time": now}

        time.sleep(15)

if __name__ == "__main__":
    Thread(target=run_flask).start()
    Thread(target=monitor_spikes).start()
