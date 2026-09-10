from dataclasses import dataclass
from statistics import mean, median
from typing import Callable, Iterable

from astra.core.models import Evaluation
from astra.data.types import WalletTrade


PriceFn = Callable[[str, int], float]


@dataclass(frozen=True)
class ExecutionAssumptions:
    fee_bps_round_trip: float = 100.0
    base_slippage_bps: float = 35.0
    impact_bps_per_100_usd: float = 8.0

    def cost_fraction(self, position_usd: float) -> float:
        bps = self.fee_bps_round_trip + self.base_slippage_bps + self.impact_bps_per_100_usd * (position_usd / 100.0)
        return bps / 10_000.0


@dataclass(frozen=True)
class CopyResult:
    wallet: str
    token: str
    signal_time: int
    delay_seconds: int
    entry_price: float
    exit_price: float
    gross_return: float
    net_return: float


def simulate_copy(
    trade: WalletTrade,
    delay_seconds: int,
    hold_seconds: int,
    position_usd: float,
    price_at: PriceFn,
    assumptions: ExecutionAssumptions = ExecutionAssumptions(),
) -> CopyResult:
    entry_time = trade.timestamp + delay_seconds
    exit_time = entry_time + hold_seconds
    entry = price_at(trade.token, entry_time)
    exit_ = price_at(trade.token, exit_time)
    gross = (exit_ / entry) - 1.0
    net = gross - assumptions.cost_fraction(position_usd)
    return CopyResult(trade.wallet, trade.token, trade.timestamp, delay_seconds, entry, exit_, gross, net)


def evaluate_results(results: Iterable[CopyResult]) -> Evaluation:
    rows = list(results)
    if not rows:
        return Evaluation(0, 0.0, 0.0, 0.0, 0.0, 0.0)

    returns = [r.net_return for r in rows]
    equity = peak = 1.0
    max_drawdown = 0.0
    for r in returns:
        equity *= 1.0 + r
        peak = max(peak, equity)
        max_drawdown = min(max_drawdown, (equity / peak) - 1.0)

    trimmed = sorted(returns)[:-3] if len(returns) > 3 else []
    return Evaluation(
        observations=len(rows),
        mean_net_return=mean(returns),
        median_net_return=median(returns),
        win_rate=sum(r > 0 for r in returns) / len(returns),
        max_drawdown=max_drawdown,
        outlier_removed_return=mean(trimmed) if trimmed else 0.0,
    )
