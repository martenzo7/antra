import argparse

from backtesting.lib import FractionalBacktest

import config
from data_fetcher import load_or_fetch
from strategy import RSIBollingerMeanReversion


def run_backtest(plot: bool = False):
    data = load_or_fetch()
    bt = FractionalBacktest(
        data,
        RSIBollingerMeanReversion,
        cash=config.STARTING_EQUITY,
        commission=0.0004,      # ~ Binance futures taker fee
        margin=1 / config.MAX_LEVERAGE,
        exclusive_orders=True,
    )
    stats = bt.run()
    print(stats)
    #print("\n--- Last trades ---")
    #print(stats["_trades"].tail(10))

    if plot:
        bt.plot(filename="backtest_result.html", open_browser=False)
        print("\nSaved interactive chart to backtest_result.html")

    return stats, bt


def optimize():
    data = load_or_fetch()
    bt = FractionalBacktest(
        data,
        RSIBollingerMeanReversion,
        cash=config.STARTING_EQUITY,
        commission=0.0004,
        margin=1 / config.MAX_LEVERAGE,
        exclusive_orders=True,
    )
    stats = bt.optimize(
        bb_period=range(14, 31, 4),
        rsi_oversold=range(20, 36, 5),
        rsi_overbought=range(64, 81, 5),
        atr_stop_mult=[1.5, 2.0, 2.5, 3.0],
        maximize="Sharpe Ratio",
        max_tries=200,
        random_state=42,
    )
    print(stats)
    print("\nBest parameters found:")
    print(stats._strategy)
    return stats


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--optimize", action="store_true",
                         help="run parameter grid-search instead of a single backtest")
    parser.add_argument("--plot", action="store_true",
                         help="save an interactive HTML chart of the backtest")
    args = parser.parse_args()

    if args.optimize:
        optimize()
    else:
        run_backtest(plot=args.plot)
