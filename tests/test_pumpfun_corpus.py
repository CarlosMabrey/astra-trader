from pathlib import Path

import duckdb

from astra.data.pumpfun_corpus import build_copyability_table, prepare_trades_view, summarize_delay


def test_public_corpus_pipeline_on_synthetic_parquet(tmp_path: Path):
    parquet = tmp_path / "trades.parquet"
    con = duckdb.connect()
    con.execute("CREATE TABLE src(wallet VARCHAR, mint VARCHAR, timestamp BIGINT, price DOUBLE, is_buy BOOLEAN)")
    rows = []
    # 20 leader buys plus later market prints so wallet passes candidate threshold.
    for i in range(20):
        t = 1000 + i * 1000
        rows.extend([
            ("leader", f"mint{i}", t, 1.00, True),
            ("other", f"mint{i}", t + 5, 1.02, True),
            ("other", f"mint{i}", t + 305, 1.08, False),
        ])
    con.executemany("INSERT INTO src VALUES (?, ?, ?, ?, ?)", rows)
    con.execute("COPY src TO ? (FORMAT PARQUET)", [str(parquet)])

    prepare_trades_view(con, parquet)
    build_copyability_table(con, delay_seconds=5, hold_seconds=300, wallet_limit=10)
    summary = summarize_delay(con, 5, round_trip_cost_fraction=0.01)

    assert summary["observations"] >= 20
    assert summary["mean_net_return"] > 0
    assert summary["win_rate"] > 0.5
