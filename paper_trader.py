import csv
import json
import os
import time
from datetime import datetime, timezone
import pandas as pd
import config
from data_fetcher import _make_exchange
from strategy import atr, bollinger_bands, rsi


def load_state():
    if os.path.exists(config.STATE_FILE):
        with open(config.STATE_FILE) as f:
            return json.load(f)
    return {
        "cash": config.STARTING_EQUITY,
        "position": 0.0,       # positive = long size, negative = short size
        "entry_price": None,
        "sl": None,
        "tp": None,
    }

def save_state(state):
    with open(config.STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def log_trade(row: dict):
    os.makedirs(os.path.dirname(config.TRADE_LOG_FILE), exist_ok=True)
    write_header = not os.path.exists(config.TRADE_LOG_FILE)
    with open(config.TRADE_LOG_FILE, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())
        if write_header:
            writer.writeheader()
        writer.writerow(row)

def fetch_recent(exchange, symbol, timeframe, limit=200) -> pd.DataFrame:
    candles = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    df = pd.DataFrame(candles, columns=["timestamp", "Open", "High", "Low", "Close", "Volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
    return df.set_index("timestamp")

def step(exchange, state):
    df = fetch_recent(exchange, config.SYMBOL, config.TIMEFRAME)
    close, high, low = df["Close"], df["High"], df["Low"]

    upper, mid, lower = bollinger_bands(close, config.BB_PERIOD, config.BB_STD)
    rsi_series = rsi(close, config.RSI_PERIOD)
    atr_series = atr(high, low, close, config.ATR_PERIOD)

    price = close.iloc[-1]
    atr_val = atr_series.iloc[-1]
    rsi_val = rsi_series.iloc[-1]

    if pd.isna(atr_val) or pd.isna(rsi_val) or pd.isna(lower.iloc[-1]):
        print("Not enough history yet, skipping.")
        return state

    stop_distance = config.ATR_STOP_MULT * atr_val
    risk_amount = state["cash"] * config.RISK_PER_TRADE
    size = max(risk_amount / stop_distance, 0)

    # --- manage an open position: check stop / target / exit first ---
    if state["position"] != 0:
        hit_sl = (state["position"] > 0 and price <= state["sl"]) or (
            state["position"] < 0 and price >= state["sl"]
        )
        hit_tp = (state["position"] > 0 and price >= state["tp"]) or (
            state["position"] < 0 and price <= state["tp"]
        )
        reverted = (state["position"] > 0 and rsi_val >= config.EXIT_RSI_MID) or (
            state["position"] < 0 and rsi_val <= config.EXIT_RSI_MID
        )
        if hit_sl or hit_tp or reverted:
            pnl = (price - state["entry_price"]) * state["position"]
            state["cash"] += pnl
            log_trade({
                "time": datetime.now(timezone.utc).isoformat(),
                "action": "CLOSE",
                "price": price,
                "size": state["position"],
                "pnl": pnl,
                "reason": "sl" if hit_sl else "tp" if hit_tp else "rsi_revert",
            })
            state.update(position=0.0, entry_price=None, sl=None, tp=None)

    # --- look for new entries only if flat ---
    if state["position"] == 0:
        if price < lower.iloc[-1] and rsi_val < config.RSI_OVERSOLD:
            state.update(position=size, entry_price=price, sl=price - stop_distance,
                          tp=price + config.ATR_TARGET_MULT * atr_val)
            log_trade({"time": datetime.now(timezone.utc).isoformat(), "action": "OPEN_LONG",
                       "price": price, "size": size, "pnl": 0, "reason": "bb_rsi_oversold"})
        elif price > upper.iloc[-1] and rsi_val > config.RSI_OVERBOUGHT:
            state.update(position=-size, entry_price=price, sl=price + stop_distance,
                          tp=price - config.ATR_TARGET_MULT * atr_val)
            log_trade({"time": datetime.now(timezone.utc).isoformat(), "action": "OPEN_SHORT",
                       "price": price, "size": size, "pnl": 0, "reason": "bb_rsi_overbought"})

    print(f"[{datetime.now(timezone.utc):%H:%M:%S}] price={price:.2f} rsi={rsi_val:.1f} "
          f"position={state['position']:.4f} cash={state['cash']:.2f}")
    return state

def run():
    exchange = _make_exchange(config.EXCHANGE_ID)
    state = load_state()
    print(f"Paper trading {config.SYMBOL} on {config.EXCHANGE_ID}, starting cash={state['cash']:.2f}")
    try:
        while True:
            state = step(exchange, state)
            save_state(state)
            time.sleep(config.POLL_SECONDS)
    except KeyboardInterrupt:
        print("\nStopped. Final state:", state)


if __name__ == "__main__":
    run()
