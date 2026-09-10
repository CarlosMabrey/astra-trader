from dataclasses import dataclass
from astra.core.models import Evaluation, StrategyStage


@dataclass(frozen=True)
class PromotionPolicy:
    min_observations: int = 1000
    min_mean_net_return: float = 0.0
    min_median_net_return: float = 0.0
    min_win_rate: float = 0.52
    max_drawdown: float = 0.15
    min_outlier_removed_return: float = 0.0


def evaluate_gates(result: Evaluation, policy: PromotionPolicy = PromotionPolicy()) -> tuple[StrategyStage, list[str]]:
    failures: list[str] = []
    if result.observations < policy.min_observations:
        failures.append("insufficient observations")
    if result.mean_net_return <= policy.min_mean_net_return:
        failures.append("non-positive mean net return")
    if result.median_net_return <= policy.min_median_net_return:
        failures.append("non-positive median net return")
    if result.win_rate < policy.min_win_rate:
        failures.append("win rate below threshold")
    if abs(result.max_drawdown) > policy.max_drawdown:
        failures.append("drawdown exceeds threshold")
    if result.outlier_removed_return <= policy.min_outlier_removed_return:
        failures.append("alpha disappears after removing outliers")

    return (StrategyStage.REJECTED if failures else StrategyStage.WALK_FORWARD, failures)
