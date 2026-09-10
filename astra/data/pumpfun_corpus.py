from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import duckdb


@dataclass(frozen=True)
class CorpusSchema:
    wallet: str
    mint: str
    timestamp: str
    price: str
    side: str
    side_is_bool: bool


def _pick(columns: set[str], *names: str) -> str:
    for name in names:
        if name.lower() in columns:
            return name.lower()
    raise ValueError(f"Could not resolve any of {names}; available={sorted(columns)}")


def _sql_path(path: str | Path) -> str:
    """Safely quote a filesystem path for DuckDB table-function SQL."""
    return "'" + str(path).replace("'", "''") + "'"


def detect_schema(con: duckdb.DuckDBPyConnection, trades_path: str | Path) -> CorpusSchema:
    rows = con.execute(f"DESCRIBE SELECT * FROM read_parquet({_sql_path(trades_path)})").fetchall()
    types = {str(r[0]).lower(): str(r[1]).upper() for r in rows}
    cols = set(types)
    wallet = _pick(cols, "wallet", "user", "trader", "signer")
    mint = _pick(cols, "mint", "token", "token_address", "address")
    timestamp = _pick(cols, "timestamp", "block_time", "blocktime", "unix_time", "time")
    price = _pick(cols, "price_usd", "price", "token_price", "price_sol")
    side = _pick(cols, "is_buy", "side", "trade_type", "type")
    return CorpusSchema(wallet, mint, timestamp, price, side, "BOOL" in types[side])


def prepare_trades_view(con: duckdb.DuckDBPyConnection, trades_path: str | Path) -> CorpusSchema:
    schema = detect_schema(con, trades_path)
    side_expr = (
        f"CASE WHEN {schema.side} THEN 'buy' ELSE 'sell' END"
        if schema.side_is_bool
        else f"lower(CAST({schema.side} AS VARCHAR))"
    )
    con.execute(
        f"""
        CREATE OR REPLACE TEMP VIEW trades_norm AS
        SELECT
            CAST({schema.wallet} AS VARCHAR) AS wallet,
            CAST({schema.mint} AS VARCHAR) AS mint,
            CAST({schema.timestamp} AS DOUBLE) AS ts,
            CAST({schema.price} AS DOUBLE) AS price,
            {side_expr} AS side
        FROM read_parquet({_sql_path(trades_path)})
        WHERE {schema.wallet} IS NOT NULL
          AND {schema.mint} IS NOT NULL
          AND {schema.timestamp} IS NOT NULL
          AND {schema.price} IS NOT NULL
        """
    )
    return schema


def rank_candidate_wallets(
    con: duckdb.DuckDBPyConnection,
    train_end_ts: float,
    min_buys: int = 20,
    max_wallets: int = 5000,
) -> list[tuple[str, int]]:
    """Rank wallets using training-period information only."""
    return con.execute(
        """
        SELECT wallet, count(*) AS buys
        FROM trades_norm
        WHERE side IN ('buy', 'b', 'true', '1') AND ts < ?
        GROUP BY wallet
        HAVING count(*) >= ?
        ORDER BY buys DESC
        LIMIT ?
        """,
        [train_end_ts, min_buys, max_wallets],
    ).fetchall()


def build_copyability_table(
    con: duckdb.DuckDBPyConnection,
    delay_seconds: int,
    train_end_ts: float,
    test_end_ts: float | None = None,
    hold_seconds: int = 300,
    wallet_limit: int = 1000,
    min_training_buys: int = 20,
) -> None:
    """Build an out-of-sample copyability table.

    Wallets are selected strictly from trades before ``train_end_ts``. Signals are
    evaluated only at/after ``train_end_ts`` (and before ``test_end_ts`` when set),
    preventing future wallet performance from leaking into candidate selection.
    """
    test_bound = "AND t.ts < ?" if test_end_ts is not None else ""
    con.execute(
        """
        CREATE OR REPLACE TEMP TABLE candidate_wallets AS
        SELECT wallet
        FROM trades_norm
        WHERE side IN ('buy', 'b', 'true', '1') AND ts < ?
        GROUP BY wallet
        HAVING count(*) >= ?
        ORDER BY count(*) DESC
        LIMIT ?
        """,
        [train_end_ts, min_training_buys, wallet_limit],
    )
    params: list[float] = [train_end_ts]
    if test_end_ts is not None:
        params.append(test_end_ts)
    con.execute(
        f"""
        CREATE OR REPLACE TEMP TABLE leader_buys AS
        SELECT t.wallet, t.mint, t.ts AS signal_ts, t.price AS leader_price
        FROM trades_norm t
        JOIN candidate_wallets w USING(wallet)
        WHERE t.side IN ('buy', 'b', 'true', '1')
          AND t.ts >= ?
          {test_bound}
        """,
        params,
    )
    con.execute(
        f"""
        CREATE OR REPLACE TEMP TABLE copyability_{int(delay_seconds)}s AS
        SELECT
            b.wallet,
            b.mint,
            b.signal_ts,
            b.leader_price,
            (
                SELECT arg_min(p.price, p.ts)
                FROM trades_norm p
                WHERE p.mint = b.mint AND p.ts >= b.signal_ts + {int(delay_seconds)}
            ) AS entry_price,
            (
                SELECT arg_min(p.price, p.ts)
                FROM trades_norm p
                WHERE p.mint = b.mint AND p.ts >= b.signal_ts + {int(delay_seconds + hold_seconds)}
            ) AS exit_price
        FROM leader_buys b
        """
    )


def summarize_delay(
    con: duckdb.DuckDBPyConnection,
    delay_seconds: int,
    round_trip_cost_fraction: float = 0.015,
) -> dict[str, float]:
    row = con.execute(
        f"""
        WITH r AS (
            SELECT (exit_price / entry_price - 1.0 - ?) AS net_return
            FROM copyability_{int(delay_seconds)}s
            WHERE entry_price > 0 AND exit_price > 0
        )
        SELECT
            count(*) AS n,
            avg(net_return) AS mean_return,
            median(net_return) AS median_return,
            avg(CASE WHEN net_return > 0 THEN 1.0 ELSE 0.0 END) AS win_rate
        FROM r
        """,
        [round_trip_cost_fraction],
    ).fetchone()
    return {
        "delay_seconds": delay_seconds,
        "observations": int(row[0] or 0),
        "mean_net_return": float(row[1] or 0.0),
        "median_net_return": float(row[2] or 0.0),
        "win_rate": float(row[3] or 0.0),
    }
