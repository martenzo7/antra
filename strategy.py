import numpy as np
import pandas as pd
from backtesting import Strategy
from backtesting.lib import crossover
import config


def rsi(series: pd.Series, period: int) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))

def bollinger_bands(series: pd.Series, period: int, num_std: float):
    mid = series.rolling(period).mean()
    std = series.rolling(period).std()
    upper = mid + num_std * std
    lower = mid - num_std * std
    return upper, mid, lower

def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int) -> pd.Series:
    prev_close = close.shift(1)
    tr = pd.concat(
        [high - low, (high - prev_close).abs(), (low - prev_close).abs()], axis=1
    ).max(axis=1)
    return tr.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()

class RSIBollingerMeanReversion(Strategy):
    bb_period = config.BB_PERIOD
    bb_std = config.BB_STD
    rsi_period = config.RSI_PERIOD
    rsi_oversold = config.RSI_OVERSOLD
    rsi_overbought = config.RSI_OVERBOUGHT
    exit_rsi_mid = config.EXIT_RSI_MID
    atr_period = config.ATR_PERIOD
    atr_stop_mult = config.ATR_STOP_MULT
    atr_target_mult = config.ATR_TARGET_MULT
    risk_per_trade = config.RISK_PER_TRADE

    def init(self):
        close = pd.Series(self.data.Close)
        high = pd.Series(self.data.High)
        low = pd.Series(self.data.Low)
        upper, mid, lower = bollinger_bands(close, self.bb_period, self.bb_std)
        self.bb_upper = self.I(lambda: upper, name="BB_upper")
        self.bb_mid = self.I(lambda: mid, name="BB_mid")
        self.bb_lower = self.I(lambda: lower, name="BB_lower")
        self.rsi = self.I(lambda: rsi(close, self.rsi_period), name="RSI")
        self.atr = self.I(lambda: atr(high, low, close, self.atr_period), name="ATR")

    def next(self):
        price = self.data.Close[-1]
        atr_val = self.atr[-1]
        if np.isnan(atr_val) or np.isnan(self.rsi[-1]) or np.isnan(self.bb_lower[-1]):
            return  # not enough history yet

        stop_distance = self.atr_stop_mult * atr_val
        if stop_distance <= 0:
            return
        risk_amount = self.equity * self.risk_per_trade
        size_units = risk_amount / stop_distance
        notional = size_units * price
        fraction = notional / self.equity
        fraction = min(fraction, 0.99)
        if fraction < 0.001:
            return
        if not self.position:
            if price < self.bb_lower[-1] and self.rsi[-1] < self.rsi_oversold:
                sl = price - stop_distance
                tp = price + self.atr_target_mult * atr_val
                self.buy(size=fraction, sl=sl, tp=tp)

            elif price > self.bb_upper[-1] and self.rsi[-1] > self.rsi_overbought:
                sl = price + stop_distance
                tp = price - self.atr_target_mult * atr_val
                self.sell(size=fraction, sl=sl, tp=tp)

        else:
            if self.position.is_long and crossover(self.rsi, self.exit_rsi_mid):
                self.position.close()
            elif self.position.is_short and crossover(self.exit_rsi_mid, self.rsi):
                self.position.close()
