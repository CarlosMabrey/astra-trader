from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import yaml

from astra.backtest.copyability import CopyResult, ExecutionAssumptions, evaluate_results, simulate_copy
from astra.data.types import WalletTrade
from astra.research.wallet_score import score_wallets
from astra.validation.gates import evaluate_gates


@dataclass(frozen=True)
class CampaignReport:
    total_signals: int
    total_simulations: int
    best_delay_seconds: int | None
    best_mean_net_return: float
    promoted: bool
    failures: list[str]
    top_wallets: list[dict]


def load_campaign(path: str | Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def run_copyability_campaign(
    config: dict,
    trades: list[WalletTrade],
    price_at: Callable[[str, int], float],
) -> CampaignReport:
    delays = [int(x) for x in config["entry_delays_seconds"]]
    sizes = [float(x) for x in config["position_sizes_usd"]]
    # First pass deliberately fixes hold time so delay/size effects remain identifiable.
    hold_seconds = 300
    assumptions = ExecutionAssumptions()
    all_results: list[CopyResult] = []
    by_delay: dict[int, list[CopyResult]] = {d: [] for d in delays}

    for trade in trades:
        if trade.side not in {"buy", "swap", ""}:
            continue
        for delay in delays:
            for size in sizes:
                result = simulate_copy(trade, delay, hold_seconds, size, price_at, assumptions)
                all_results.append(result)
                by_delay[delay].append(result)

    delay_evals = {d: evaluate_results(rows) for d, rows in by_delay.items() if rows}
    if delay_evals:
        best_delay = max(delay_evals, key=lambda d: delay_evals[d].mean_net_return)
        best_eval = delay_evals[best_delay]
        stage, failures = evaluate_gates(best_eval)
        best_return = best_eval.mean_net_return
    else:
        best_delay, failures, best_return = None, ["no simulations produced"], 0.0
        stage = None

    top_wallets = [
        {
            "wallet": w.wallet,
            "observations": w.observations,
            "mean_net_return": w.mean_net_return,
            "median_net_return": w.median_net_return,
            "win_rate": w.win_rate,
            "copyability_score": w.copyability_score,
        }
        for w in score_wallets(all_results)[:20]
    ]

    return CampaignReport(
        total_signals=len(trades),
        total_simulations=len(all_results),
        best_delay_seconds=best_delay,
        best_mean_net_return=best_return,
        promoted=bool(stage and stage.value == "walk_forward"),
        failures=failures,
        top_wallets=top_wallets,
    )
