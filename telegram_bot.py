import MetaTrader5 as mt5
import requests
import time
import os
import matplotlib.pyplot as plt

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

API_URL = "https://ai-trading-backend-nx50.onrender.com/signal"

# 🔥 CONNECT TO MT5
if not mt5.initialize():
    print("MT5 initialization failed")
    quit()

print("MT5 connected ✅")


# 🔥 GET REAL FOREX PRICE
def get_price(symbol="EURUSD"):
    tick = mt5.symbol_info_tick(symbol)
    return tick.bid


# 🎯 Generate REAL chart
def generate_chart(symbol, price, tp, sl):
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 50)

    closes = [r.close for r in rates]

    plt.figure()
    plt.plot(closes)

    plt.axhline(tp, linestyle='--')
    plt.axhline(sl, linestyle='--')
    plt.axhline(price)

    plt.title(f"{symbol} MT5 LIVE")

    file_path = f"{symbol}.png"
    plt.savefig(file_path)
    plt.close()

    return file_path


def send_signal():
    try:
        res = requests.get(API_URL)
        data = res.json()

        for signal in data:
            pair = signal.get("pair", "EURUSD")
            direction = signal.get("signal", "BUY")
            confidence = signal.get("confidence", 0)

            price = get_price(pair)

            if direction == "BUY":
                tp = round(price + 0.0020, 5)
                sl = round(price - 0.0010, 5)
            else:
                tp = round(price - 0.0020, 5)
                sl = round(price + 0.0010, 5)

            chart = generate_chart(pair, price, tp, sl)

            caption = f"""
📊 MT5 LIVE SIGNAL

📌 {pair}
💰 Entry: {price}
➡️ {direction}

🎯 TP: {tp}
🛑 SL: {sl}
📊 Confidence: {confidence}%
"""

            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

            with open(chart, "rb") as photo:
                requests.post(url, data={
                    "chat_id": CHAT_ID,
                    "caption": caption
                }, files={"photo": photo})

            print("MT5 signal sent!")

    except Exception as e:
        print("Error:", e)


while True:
    send_signal()
    time.sleep(180)
