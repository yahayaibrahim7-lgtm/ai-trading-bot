import requests
import time
import os
from PIL import Image, ImageDraw, ImageFont

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

API_URL = "https://ai-trading-backend-nx50.onrender.com/signal"

# 🔥 Get LIVE price
def get_live_price(pair):
    try:
        base = pair[:3]
        quote = pair[3:]
        url = f"https://api.exchangerate.host/latest?base={base}&symbols={quote}"
        res = requests.get(url).json()
        return res["rates"][quote]
    except:
        return None


# 🖼️ CREATE SIGNAL IMAGE
def create_signal_image(pair, direction, entry, tp, sl, confidence):
    width, height = 800, 500
    img = Image.new("RGB", (width, height), color=(10, 20, 40))
    draw = ImageDraw.Draw(img)

    # Optional font (fallback if not found)
    try:
        font_title = ImageFont.truetype("arial.ttf", 50)
        font_text = ImageFont.truetype("arial.ttf", 30)
    except:
        font_title = None
        font_text = None

    # Title
    draw.text((50, 40), f"{pair}", fill="white", font=font_title)

    # Signal
    color = "green" if direction == "BUY" else "red"
    draw.text((50, 120), f"{direction}", fill=color, font=font_title)

    # Details
    draw.text((50, 220), f"Entry: {entry}", fill="white", font=font_text)
    draw.text((50, 270), f"TP: {tp}", fill="white", font=font_text)
    draw.text((50, 320), f"SL: {sl}", fill="white", font=font_text)
    draw.text((50, 370), f"Confidence: {confidence}%", fill="white", font=font_text)

    file_path = "signal.png"
    img.save(file_path)

    return file_path


def send_signal():
    try:
        res = requests.get(API_URL)
        data = res.json()

        for signal in data:
            pair = signal.get("pair", "EURUSD")
            direction = signal.get("signal", "BUY")
            confidence = signal.get("confidence", 0)

            price = get_live_price(pair)
            if price is None:
                continue

            # 🔥 SL/TP logic
            if direction == "BUY":
                tp = round(price + 0.0020, 5)
                sl = round(price - 0.0010, 5)
            else:
                tp = round(price - 0.0020, 5)
                sl = round(price + 0.0010, 5)

            # 🖼️ Generate image
            image_path = create_signal_image(pair, direction, price, tp, sl, confidence)

            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

            with open(image_path, "rb") as photo:
                requests.post(url, files={"photo": photo}, data={
                    "chat_id": CHAT_ID,
                    "caption": f"{pair} {direction} Signal 🚀"
                })

        print("Signal images sent!")

    except Exception as e:
        print("Error:", e)


while True:
    send_signal()
    time.sleep(60)
