from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class StrategyStage(str, Enum):
    HYPOTHESIS = "hypothesis"
    BACKTEST = "backtest"
    RED_TEAM = "red_team"
    WALK_FORWARD = "walk_forward"
    PAPER = "paper"
    REJECTED = "rejected"
    LIVE_ELIGIBLE = "live_eligible"  # eligibility only; execution remains disabled


@dataclass(frozen=True)
class Signal:
    timestamp: float
    market: str
    asset: str
    source: str
    features: dict[str, float]


@dataclass(frozen=True)
class StrategySpec:
    strategy_id: str
    thesis: str
    entry_delay_seconds: int
    take_profit_pct: float
    stop_loss_pct: float
    max_hold_seconds: int
    filters: dict[str, Any] = field(default_factory=dict)


@dataclass
class Evaluation:
    observations: int
    mean_net_return: float
    median_net_return: float
    win_rate: float
    max_drawdown: float
    outlier_removed_return: float
    stage: StrategyStage = StrategyStage.BACKTEST
