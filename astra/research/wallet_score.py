from collections import defaultdict
from dataclasses import dataclass
from statistics import mean, median

from astra.backtest.copyability import CopyResult


@dataclass(frozen=True)
class WalletScore:
    wallet: str
    observations: int
    mean_net_return: float
    median_net_return: float
    win_rate: float
    copyability_score: float


def score_wallets(results: list[CopyResult]) -> list[WalletScore]:
    grouped: dict[str, list[float]] = defaultdict(list)
    for r in results:
        grouped[r.wallet].append(r.net_return)

    scores: list[WalletScore] = []
    for wallet, returns in grouped.items():
        n = len(returns)
        avg = mean(returns)
        med = median(returns)
        win_rate = sum(r > 0 for r in returns) / n
        sample_confidence = min(1.0, n / 100.0)
        # Score emphasizes actually copyable returns and consistency; sample size
        # shrinks tiny-wallet histories toward zero rather than rewarding lucky outliers.
        raw = 0.45 * avg + 0.35 * med + 0.20 * (win_rate - 0.5)
        score = 100.0 * sample_confidence * raw
        scores.append(WalletScore(wallet, n, avg, med, win_rate, score))

    return sorted(scores, key=lambda x: x.copyability_score, reverse=True)
