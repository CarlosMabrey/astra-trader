import argparse
import json

import duckdb

from astra.data.pumpfun_corpus import build_copyability_table, prepare_trades_view, summarize_delay


def main() -> None:
    p = argparse.ArgumentParser(description="Run CA-001 against the public Pump.fun parquet corpus")
    p.add_argument("--trades", required=True, help="Path to trades.parquet")
    p.add_argument("--wallet-limit", type=int, default=1000)
    p.add_argument("--hold", type=int, default=300)
    p.add_argument("--cost", type=float, default=0.015, help="Round-trip cost fraction; 0.015 = 1.5%")
    p.add_argument("--out", default="results/ca001_copyability.json")
    args = p.parse_args()

    con = duckdb.connect()
    schema = prepare_trades_view(con, args.trades)
    results = []
    for delay in (1, 5, 10, 30, 60):
        build_copyability_table(con, delay, hold_seconds=args.hold, wallet_limit=args.wallet_limit)
        results.append(summarize_delay(con, delay, round_trip_cost_fraction=args.cost))

    payload = {
        "campaign": "copyable_alpha_001",
        "source": "Slinky21/Pumpfun_Memecoin_Corpus",
        "schema": schema.__dict__,
        "hold_seconds": args.hold,
        "round_trip_cost_fraction": args.cost,
        "delays": results,
    }
    from pathlib import Path
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
