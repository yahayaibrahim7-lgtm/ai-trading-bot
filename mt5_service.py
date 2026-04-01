import MetaTrader5 as mt5
import pandas as pd

# ==============================
# CONNECT MT5
# ==============================
def connect_mt5():
    if not mt5.initialize():
        print("❌ MT5 initialization failed")
        return False
    return True


# ==============================
# GET DATA
# ==============================
def get_data(symbol="USDJPY"):
    if not connect_mt5():
        return None

    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 100)

    if rates is None:
        return None

    df = pd.DataFrame(rates)
    return df


# ==============================
# SIMPLE AI SIGNAL (PLACEHOLDER)
# ==============================
def generate_signal(df):
    last_close = df["close"].iloc[-1]
    last_open = df["open"].iloc[-1]

    if last_close > last_open:
        return "BUY"
    elif last_close < last_open:
        return "SELL"
    else:
        return "WAIT"


# ==============================
# PLACE TRADE (WITH SL/TP)
# ==============================
def place_trade(signal, symbol="USDJPY"):
    symbol_info = mt5.symbol_info(symbol)

    if symbol_info is None:
        print("❌ Symbol not found")
        return

    if not symbol_info.visible:
        mt5.symbol_select(symbol, True)

    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        print("❌ No tick data")
        return

    # ==============================
    # RISK SETTINGS
    # ==============================
    lot = 0.01
    point = symbol_info.point

    sl_points = 100
    tp_points = 200

    # ==============================
    # BUY / SELL LOGIC
    # ==============================
    if signal == "BUY":
        price = tick.ask
        sl = price - sl_points * point
        tp = price + tp_points * point
        order_type = mt5.ORDER_TYPE_BUY

    elif signal == "SELL":
        price = tick.bid
        sl = price + sl_points * point
        tp = price - tp_points * point
        order_type = mt5.ORDER_TYPE_SELL

    else:
        return

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot,
        "type": order_type,
        "price": price,
        "sl": sl,
        "tp": tp,
        "deviation": 10,
        "magic": 123456,
        "comment": "AI Trade",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    result = mt5.order_send(request)

    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print("❌ Trade failed:", result)
    else:
        print("✅ Trade placed:", result)


# ==============================
# FINAL SIGNAL FUNCTION (API USES THIS)
# ==============================
def get_signal(symbol="USDJPY"):
    try:
        df = get_data(symbol)

        if df is None or df.empty:
            return {
                "pair": symbol,
                "signal": "WAIT",
                "confidence": "0%"
            }

        signal = generate_signal(df)

        confidence = "85%" if signal in ["BUY", "SELL"] else "0%"

        # AUTO TRADE
        if signal in ["BUY", "SELL"]:
            place_trade(signal, symbol)

        return {
            "pair": symbol,
            "signal": signal,
            "confidence": confidence
        }

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return {
            "pair": symbol,
            "signal": "WAIT",
            "confidence": "0%"
        }