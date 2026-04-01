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
            message += f"📌 {signal['pair']}\n"
            message += f"➡️ Signal: {signal['signal']}\n"
            message += f"📊 Confidence: {signal['confidence']}\n\n"

        message += "🚀 Powered by AI Trading Bot"

        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, data={
            "chat_id": CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        })
