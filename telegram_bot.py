import MetaTrader5 as mt5
import requests
import time
import os
import matplotlib.pyplot as plt

# ================= CONFIG =================
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

API_URL = "https://ai-trading-backend-nx50.onrender.com/signal"


# ================= CONNECT MT5 =================
if not mt5.initialize():
    print("❌ MT5 initialization failed")
    quit()

print("MT5 connected ✅")


# ================= GET PRICE =================
def get_price(symbol):
    if not mt5.symbol_select(symbol, True):
        return None

    tick = mt5.symbol_info_tick(symbol)

    if tick is None:
        return None

    return tick.bid


# ================= AUTO SYMBOL MAPPING (FINAL FIX) =================
def get_valid_symbol(pair):
    possible_symbols = [
        pair,
        pair + "m",
        pair + ".m",     # ✅ YOUR BROKER FORMAT
        pair + ".pro",
        pair + ".a",
        pair + "_i"
    ]

    for sym in possible_symbols:
        price = get_price(sym)
        if price is not None:
            print(f"✅ Using symbol: {sym}")
            return sym, price

    print(f"❌ No valid symbol found for {pair}")
    return None, None


# ================= GENERATE CHART =================
def generate_chart(symbol, price, tp, sl):
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 50)

    if rates is None or len(rates) == 0:
        print("No rate data...")
        return None

    # ✅ FIX HERE
    closes = [r['close'] for r in rates]

    import matplotlib.pyplot as plt

    plt.figure()
    plt.plot(closes)

    # Entry, TP, SL
    plt.axhline(price, linestyle='-')
    plt.axhline(tp, linestyle='--')
    plt.axhline(sl, linestyle='--')

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

            pair = signal.get("pair", "EURUSD")
            direction = signal.get("signal", "BUY")
            confidence = signal.get("confidence", 0)

            # 🔥 AUTO SYMBOL DETECTION
            symbol, price = get_valid_symbol(pair)

            if price is None:
                print("Skipping due to no price...")
                continue

            # TP / SL
            if direction == "BUY":
                tp = round(price + 0.0020, 5)
                sl = round(price - 0.0010, 5)
            else:
                tp = round(price - 0.0020, 5)
                sl = round(price + 0.0010, 5)

            # Chart
            chart = generate_chart(symbol, price, tp, sl)

            if chart is None:
                print("Chart failed...")
                continue

            caption = f"""
📊 MT5 LIVE SIGNAL

📌 {symbol}
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
