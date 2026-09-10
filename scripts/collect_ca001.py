import argparse

from astra.data.birdeye import BirdeyeClient
from astra.data.dataset import collect_wallet_trades, load_wallets, write_trades_csv


def main() -> None:
    p = argparse.ArgumentParser(description="Collect CA-001 historical wallet trades from Birdeye")
    p.add_argument("--wallets", default="campaigns/wallets_ca001.txt")
    p.add_argument("--after", type=int, required=True, help="Unix timestamp, inclusive lower bound")
    p.add_argument("--before", type=int, required=True, help="Unix timestamp, upper bound")
    p.add_argument("--out", default="data/ca001_wallet_trades.csv")
    args = p.parse_args()

    wallets = load_wallets(args.wallets)
    if not wallets:
        raise SystemExit("No wallets configured")
    client = BirdeyeClient()
    trades = collect_wallet_trades(wallets, args.after, args.before, client)
    write_trades_csv(args.out, trades)
    print(f"wrote {len(trades)} trades to {args.out}")


if __name__ == "__main__":
    main()
