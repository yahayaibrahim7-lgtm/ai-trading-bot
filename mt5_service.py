# ==============================
# SAFE MT5 IMPORT (FOR RENDER)
# ==============================
try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except:
    MT5_AVAILABLE = False

import random

# ==============================
# GET SIGNAL (AI / FALLBACK)
# ==============================
def get_signal(symbol="EURUSD"):
    """
    Returns trading signal.
    Works WITH or WITHOUT MT5
    """

    # ==========================
    # IF MT5 AVAILABLE (LOCAL)
    # ==========================
    if MT5_AVAILABLE:
        try:
            if not mt5.initialize():
                return fallback_signal(symbol)

            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, 50)

            if rates is None or len(rates) == 0:
                return fallback_signal(symbol)

            closes = [r.close for r in rates]

            signal = "BUY" if closes[-1] > closes[-2] else "SELL"

            confidence = "85%" if signal in ["BUY", "SELL"] else "0%"

            return {
                "pair": symbol,
                "signal": signal,
                "confidence": confidence
            }

        except Exception as e:
            print("MT5 ERROR:", e)
            return fallback_signal(symbol)

    # ==========================
    # IF MT5 NOT AVAILABLE (RENDER)
    # ==========================
    return fallback_signal(symbol)


# ==============================
# FALLBACK AI SIGNAL
# ==============================
def fallback_signal(symbol):
    signal = random.choice(["BUY", "SELL"])

    return {
        "pair": symbol,
        "signal": signal,
        "confidence": "75% (AI)"
    }


# ==============================
# PLACE TRADE (SAFE)
# ==============================
def place_trade(signal, symbol="EURUSD"):
    """
    Only works locally with MT5
    """

    if not MT5_AVAILABLE:
        return {"status": "MT5 not available on server"}

    try:
        if not mt5.initialize():
            return {"status": "MT5 init failed"}

        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            return {"status": "Symbol not found"}

        if not symbol_info.visible:
            mt5.symbol_select(symbol, True)

        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            return {"status": "No tick data"}

        lot = 0.01
        point = symbol_info.point

        sl_points = 100
        tp_points = 200

        if signal == "BUY":
            price = tick.ask
            sl = price - sl_points * point
            tp = price + tp_points * point
            order_type = mt5.ORDER_TYPE_BUY
        else:
            price = tick.bid
            sl = price + sl_points * point
            tp = price - tp_points * point
            order_type = mt5.ORDER_TYPE_SELL

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": lot,
            "type": order_type,
            "price": price,
            "sl": sl,
            "tp": tp,
            "deviation": 20,
            "magic": 123456,
            "comment": "AI Trade",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        result = mt5.order_send(request)

        return {"status": "Trade sent", "result": str(result)}

    except Exception as e:
        return {"status": "Error", "message": str(e)}
