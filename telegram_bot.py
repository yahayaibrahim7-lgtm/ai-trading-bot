import MetaTrader5 as mt5
import requests
import time
import os
import matplotlib.pyplot as plt

# ================= CONFIG =================
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

API_URL = "https://ai-trading-backend-nx50.onrender.com/signal"

# 🔥 IMPORTANT: CHANGE THIS TO YOUR BROKER SYMBOL
SYMBOL = "USDJP.m"   # e.g. USDJPY.m, EURUSD.m etc


# ================= CONNECT MT5 =================
if not mt5.initialize():
    print("❌ MT5 initialization failed")
    quit()

print("MT5 connected ✅")


# ================= GET PRICE =================
def get_price(symbol):
    if not mt5.symbol_select(symbol, True):
        print(f"❌ Failed to select {symbol}")
        return None

    tick = mt5.symbol_info_tick(symbol)

    if tick is None:
        print(f"❌ No tick data for {symbol}")
        return None

    return tick.bid


# ================= GENERATE CHART =================
def generate_chart(symbol, price, tp, sl):
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 50)

    if rates is None:
        return None

    closes = [r.close for r in rates]

    plt.figure()
    plt.plot(closes)

    # Draw lines
    plt.axhline(price, linestyle='-')   # Entry
    plt.axhline(tp, linestyle='--')     # TP
    plt.axhline(sl, linestyle='--')     # SL

    plt.title(f"{symbol} MT5 LIVE")

    file_path = f"{symbol}.png"
    plt.savefig(file_path)
    plt.close()

    return file_path


# ================= SEND SIGNAL =================
def send_signal():
    try:
        res = requests.get(API_URL)
        data = res.json()

        for signal in data:

            direction = signal.get("signal", "BUY")
            confidence = signal.get("confidence", 0)

            pair = SYMBOL   # 🔥 FORCE correct symbol

            # GET REAL PRICE
            price = get_price(pair)

            if price is None:
                print("Skipping due to no price...")
                continue

            # CALCULATE TP / SL
            if direction == "BUY":
                tp = round(price + 0.0020, 5)
                sl = round(price - 0.0010, 5)
            else:
                tp = round(price - 0.0020, 5)
                sl = round(price + 0.0010, 5)

            # GENERATE CHART
            chart = generate_chart(pair, price, tp, sl)

            if chart is None:
                print("Chart failed...")
                continue

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

            print("✅ MT5 signal sent!")

    except Exception as e:
        print("Error:", e)


# ================= LOOP =================
while True:
    send_signal()
    time.sleep(180)
