from pathlib import Path

import duckdb

from astra.data.pumpfun_corpus import build_copyability_table, prepare_trades_view, summarize_delay


def test_public_corpus_pipeline_on_synthetic_parquet(tmp_path: Path):
    parquet = tmp_path / "trades.parquet"
    con = duckdb.connect()
    con.execute("CREATE TABLE src(wallet VARCHAR, mint VARCHAR, timestamp BIGINT, price DOUBLE, is_buy BOOLEAN)")
    rows = []

    # Training-period activity qualifies the leader using past information only.
    for i in range(20):
        rows.append(("leader", f"train{i}", 100 + i, 1.00, True))

    # OOS signals + delayed market prints.
    for i in range(20):
        t = 10_000 + i * 1000
        rows.extend([
            ("leader", f"test{i}", t, 1.00, True),
            ("other", f"test{i}", t + 5, 1.02, True),
            ("other", f"test{i}", t + 305, 1.08, False),
        ])

    con.executemany("INSERT INTO src VALUES (?, ?, ?, ?, ?)", rows)
    con.execute("COPY src TO ? (FORMAT PARQUET)", [str(parquet)])

    prepare_trades_view(con, parquet)
    build_copyability_table(
        con,
        delay_seconds=5,
        train_end_ts=1000,
        test_end_ts=40_000,
        hold_seconds=300,
        wallet_limit=10,
    )
    summary = summarize_delay(con, 5, round_trip_cost_fraction=0.01)

    assert summary["observations"] == 20
    assert summary["mean_net_return"] > 0
    assert summary["win_rate"] > 0.5


def test_wallet_selection_does_not_use_future_activity(tmp_path: Path):
    parquet = tmp_path / "leakage.parquet"
    con = duckdb.connect()
    con.execute("CREATE TABLE src(wallet VARCHAR, mint VARCHAR, timestamp BIGINT, price DOUBLE, is_buy BOOLEAN)")
    rows = [("future_star", f"m{i}", 10_000 + i, 1.0, True) for i in range(30)]
    con.executemany("INSERT INTO src VALUES (?, ?, ?, ?, ?)", rows)
    con.execute("COPY src TO ? (FORMAT PARQUET)", [str(parquet)])

    prepare_trades_view(con, parquet)
    build_copyability_table(con, delay_seconds=5, train_end_ts=1000, wallet_limit=10)
    n = con.execute("SELECT count(*) FROM candidate_wallets").fetchone()[0]
    assert n == 0
