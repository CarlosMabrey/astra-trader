"""Astra research-loop skeleton.

The orchestrator deliberately has no live-broker capability. Its job is to
produce evidence and promote candidates toward paper trading.
"""
from dataclasses import dataclass
from astra.validation.gates import evaluate_gates
from astra.validation.red_team import red_team


@dataclass
class ResearchCycle:
    campaign_id: str

    def run(self) -> dict:
        # Connectors/backtester are intentionally the next implementation step.
        return {
            "campaign": self.campaign_id,
            "steps": [
                "observe",
                "generate_hypotheses",
                "historical_backtest",
                "red_team",
                "walk_forward",
                "paper_trade",
                "evaluate",
                "update_strategy_library",
            ],
            "live_execution": False,
        }


def main() -> None:
    import sys
    campaign = sys.argv[1] if len(sys.argv) > 1 else "campaigns/copyable_alpha_001.yaml"
    cycle = ResearchCycle(campaign)
    print(cycle.run())


if __name__ == "__main__":
    main()
