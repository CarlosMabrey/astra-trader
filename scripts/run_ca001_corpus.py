import argparse
import json
from pathlib import Path

import duckdb

from astra.data.pumpfun_corpus import build_copyability_table, prepare_trades_view, summarize_delay


def main() -> None:
    p = argparse.ArgumentParser(description="Run leakage-safe CA-001 against Pump.fun parquet trades")
    p.add_argument("--trades", required=True, help="Path to trades.parquet")
    p.add_argument("--train-end", type=float, required=True, help="Unix timestamp: wallet selection uses only earlier trades")
    p.add_argument("--test-end", type=float, default=None, help="Optional Unix timestamp ending the OOS evaluation window")
    p.add_argument("--wallet-limit", type=int, default=1000)
    p.add_argument("--min-training-buys", type=int, default=20)
    p.add_argument("--hold", type=int, default=300)
    p.add_argument("--cost", type=float, default=0.015, help="Round-trip cost fraction; 0.015 = 1.5%")
    p.add_argument("--out", default="results/ca001_copyability.json")
    args = p.parse_args()

    con = duckdb.connect()
    schema = prepare_trades_view(con, args.trades)
    results = []
    for delay in (1, 5, 10, 30, 60):
        build_copyability_table(
            con,
            delay,
            train_end_ts=args.train_end,
            test_end_ts=args.test_end,
            hold_seconds=args.hold,
            wallet_limit=args.wallet_limit,
            min_training_buys=args.min_training_buys,
        )
        results.append(summarize_delay(con, delay, round_trip_cost_fraction=args.cost))

    payload = {
        "campaign": "copyable_alpha_001",
        "source": "Slinky21/Pumpfun_Memecoin_Corpus",
        "schema": schema.__dict__,
        "train_end_ts": args.train_end,
        "test_end_ts": args.test_end,
        "hold_seconds": args.hold,
        "round_trip_cost_fraction": args.cost,
        "delays": results,
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
