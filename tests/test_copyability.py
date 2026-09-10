from astra.backtest.copyability import ExecutionAssumptions, evaluate_results, simulate_copy
from astra.data.types import WalletTrade


def test_copy_result_accounts_for_delay_and_costs():
    trade = WalletTrade("w1", "token", "buy", 100, 1.0, 100.0, 100.0, "sig")
    prices = {105: 1.10, 405: 1.21}
    result = simulate_copy(
        trade,
        delay_seconds=5,
        hold_seconds=300,
        position_usd=100,
        price_at=lambda _token, ts: prices[ts],
        assumptions=ExecutionAssumptions(fee_bps_round_trip=10, base_slippage_bps=10, impact_bps_per_100_usd=0),
    )
    assert round(result.gross_return, 4) == 0.10
    assert round(result.net_return, 4) == 0.098


def test_evaluation_removes_top_three_outliers():
    trade = WalletTrade("w1", "t", "buy", 0, 1, 1, 1, "")
    returns = []
    for i, exit_price in enumerate([1.01, 1.02, 1.03, 2.0, 2.1, 2.2]):
        returns.append(
            simulate_copy(
                trade,
                delay_seconds=i,
                hold_seconds=1,
                position_usd=0,
                price_at=lambda _token, ts, ep=exit_price, i=i: 1.0 if ts == i else ep,
                assumptions=ExecutionAssumptions(0, 0, 0),
            )
        )
    evaluation = evaluate_results(returns)
    assert evaluation.observations == 6
    assert evaluation.outlier_removed_return < evaluation.mean_net_return
