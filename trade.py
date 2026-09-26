"""
Examples:
  python main.py fetch              # download & cache OHLCV data
  python main.py backtest           # run one backtest with default params
  python main.py backtest --plot    # ...and save an interactive chart
  python main.py optimize           # grid-search strategy parameters
  python main.py paper              # start the paper-trading loop
"""
import argparse
import backtester
import data_fetcher
import paper_trader


def main():
    parser = argparse.ArgumentParser(description="Crypto perpetual futures mean-reversion bot")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("fetch", help="download and cache OHLCV data")
    bt_parser = sub.add_parser("backtest", help="run a single backtest")
    bt_parser.add_argument("--plot", action="store_true")
    sub.add_parser("optimize", help="grid-search strategy parameters")
    sub.add_parser("paper", help="run the live paper-trading loop")
    args = parser.parse_args()
    if args.command == "fetch":
        df = data_fetcher.load_or_fetch()
        print(df.tail())
    elif args.command == "backtest":
        backtester.run_backtest(plot=args.plot)
    elif args.command == "optimize":
        backtester.optimize()
    elif args.command == "paper":
        paper_trader.run()

if __name__ == "__main__":
    main()
