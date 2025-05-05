import time
import requests
import pandas as pd
from smartapi import SmartConnect
from flask import Flask
import datetime

app = Flask(__name__)

@app.route('/')
def home():
    return "Algo Bot is running!"

API_KEY = "your_api_key"
CLIENT_CODE = "your_client_code"
PASSWORD = "your_password"
TOTP_SECRET = "your_totp_secret"

obj = SmartConnect(api_key=API_KEY)
data = obj.generateSession(client_code=CLIENT_CODE, password=PASSWORD, totp=None)
profile = obj.getProfile()
print("Login successful. Profile:", profile)

def detect_spike(data):
    print("Checking for spikes...")
    return True

while True:
    print("Running algo check at", datetime.datetime.now())
    time.sleep(10)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
