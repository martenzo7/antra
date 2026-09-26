# --- Exchange / market ---
EXCHANGE_ID = "binanceusdm"      # ccxt id for Binance USDT-M perpetual futures
                                  # (use "bybit" for Bybit perpetuals instead)
SYMBOL = "BTC/USDT:USDT"         # ccxt unified symbol for the perpetual contract
TIMEFRAME = "1h"                 # candle size: 1m, 5m, 15m, 1h, 4h, 1d ...
HISTORY_DAYS = 730                # how much history to pull for backtests

# --- Strategy parameters (RSI + Bollinger Band mean reversion) ---
BB_PERIOD = 20
BB_STD = 2.0
RSI_PERIOD = 14
RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 70
EXIT_RSI_MID = 50                # exit when RSI reverts back through this level

# --- Risk management ---
RISK_PER_TRADE = 0.01            # fraction of equity risked per trade (1%)
ATR_PERIOD = 14
ATR_STOP_MULT = 2.5              # stop loss  = ATR_STOP_MULT   * ATR from entry
ATR_TARGET_MULT = 4.0            # take profit = ATR_TARGET_MULT * ATR from entry
MAX_LEVERAGE = 3                 # caps notional exposure relative to equity
STARTING_EQUITY = 10000

# --- Paper trading ---
POLL_SECONDS = 60                # how often to poll for a new candle
STATE_FILE = "paper_state.json"
TRADE_LOG_FILE = "logs/paper_trades.csv"

# --- Files ---
DATA_DIR = "data"
