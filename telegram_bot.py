import requests
import time
import os

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

API_URL = "https://ai-trading-backend-nx50.onrender.com/signal"

def send_signal():
    try:
        res = requests.get(API_URL)
        data = res.json()

        message = "📊 AI SIGNALS\n\n"

        for signal in data:
            message += f"""
Pair: {signal['pair']}
Signal: {signal['signal']}
Confidence: {signal['confidence']}

"""

        message += "🔥 Powered by AI Bot"

        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": message})

        print("Signals sent!")

    except Exception as e:
        print("Error:", e)

while True:
    send_signal()
    time.sleep(60)
