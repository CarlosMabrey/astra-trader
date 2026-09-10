from dataclasses import dataclass


@dataclass(frozen=True)
class RedTeamReport:
    passed: bool
    warnings: list[str]


def red_team(*, train_return: float, test_return: float, top_3_trade_share: float, timestamp_leakage: bool, survivorship_bias: bool) -> RedTeamReport:
    warnings: list[str] = []
    if timestamp_leakage:
        warnings.append("timestamp/look-ahead leakage detected")
    if survivorship_bias:
        warnings.append("survivorship bias detected")
    if train_return > 0 and test_return < train_return * 0.35:
        warnings.append("severe out-of-sample degradation")
    if top_3_trade_share > 0.50:
        warnings.append("more than half of profit depends on top three trades")
    return RedTeamReport(passed=not warnings, warnings=warnings)
