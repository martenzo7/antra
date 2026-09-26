import os
import time
from datetime import datetime, timedelta, timezone
import ccxt
import pandas as pd
import config


def _make_exchange(exchange_id: str):
    exchange_class = getattr(ccxt, exchange_id)
    return exchange_class({"enableRateLimit": True})

def fetch_ohlcv(
    exchange_id: str = config.EXCHANGE_ID,
    symbol: str = config.SYMBOL,
    timeframe: str = config.TIMEFRAME,
    days: int = config.HISTORY_DAYS,
) -> pd.DataFrame:
    exchange = _make_exchange(exchange_id)
    since = exchange.parse8601(
        (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    )
    all_candles = []
    limit = 1000

    while True:
        candles = exchange.fetch_ohlcv(symbol, timeframe=timeframe, since=since, limit=limit)
        if not candles:
            break
        all_candles.extend(candles)
        last_ts = candles[-1][0]
        if last_ts == since:
            break
        since = last_ts + 1
        if len(candles) < limit:
            break
        time.sleep(exchange.rateLimit / 1000)

    df = pd.DataFrame(
        all_candles, columns=["timestamp", "Open", "High", "Low", "Close", "Volume"]
    )
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
    df = df.drop_duplicates(subset="timestamp").set_index("timestamp").sort_index()
    return df

def load_or_fetch(cache_name: str = None, **kwargs) -> pd.DataFrame:
    os.makedirs(config.DATA_DIR, exist_ok=True)
    symbol = kwargs.get("symbol", config.SYMBOL)
    timeframe = kwargs.get("timeframe", config.TIMEFRAME)
    cache_name = cache_name or f"{symbol.replace('/', '_').replace(':', '_')}_{timeframe}.csv"
    path = os.path.join(config.DATA_DIR, cache_name)

    if os.path.exists(path):
        return pd.read_csv(path, index_col=0, parse_dates=True)

    df = fetch_ohlcv(**kwargs)
    df.to_csv(path)
    return df


if __name__ == "__main__":
    data = load_or_fetch()
    print(data.tail())
    print(f"\nFetched {len(data)} candles for {config.SYMBOL} @ {config.TIMEFRAME}")
