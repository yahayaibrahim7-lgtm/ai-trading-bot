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

        message = "📊 *AI SIGNALS*\n\n"

        for signal in data:
            pair = signal.get("pair", "N/A")
            direction = signal.get("signal", "N/A")
            confidence = signal.get("confidence", "N/A")

            # 👉 AUTO SL/TP LOGIC (simple example)
            price = signal.get("price", 1.1000)

            if direction == "BUY":
                tp = round(price + 0.0020, 5)
                sl = round(price - 0.0010, 5)
            else:
                tp = round(price - 0.0020, 5)
                sl = round(price + 0.0010, 5)

            message += f"📌 *{pair}*\n"
            message += f"➡️ Signal: *{direction}*\n"
            message += f"🎯 TP: `{tp}`\n"
            message += f"🛑 SL: `{sl}`\n"
            message += f"📊 Confidence: `{confidence}`\n\n"

        message += "🚀 *VIP AI Trading Bot*"

        # 🖼️ IMAGE (use any hosted image)
        image_url = "https://i.imgur.com/8RKXAIV.jpeg"

        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

        requests.post(url, data={
            "chat_id": CHAT_ID,
            "caption": message,
            "photo": image_url,
            "parse_mode": "Markdown"
        })

        print("Signals with SL/TP + Image sent!")

    except Exception as e:
        print("Error:", e)

while True:
    send_signal()
    time.sleep(180)
