# Astra Trader

Astra is an autonomous quantitative research system for discovering, falsifying, validating, and paper-trading market strategies before any live capital is allowed.

## Core loop

Observe -> Hypothesize -> Backtest -> Red-team -> Walk-forward validate -> Paper trade -> Evaluate -> Reweight -> Repeat

## Initial campaign: Copyable Alpha #001

Question: when a historically strong Solana/Pump.fun wallet buys a token, can Astra enter 1/5/10/30/60 seconds later and still earn positive net returns after fees and slippage?

The first milestone is not live trading. It is 1,000+ out-of-sample signals with positive realistic net expectancy and controlled drawdown.

## Safety architecture

- Live trading is disabled by default.
- Research agents cannot override risk policy.
- Strategy promotion is deterministic and gate-based.
- Every result is stored with dataset/version provenance.
- Red-team checks target leakage, survivorship bias, overfitting, unrealistic fills, outlier dependence, and regime fragility.

## Repo layout

- `astra/core` — shared experiment and strategy types
- `astra/research` — hypothesis generation and campaign orchestration
- `astra/backtest` — latency/slippage-aware simulation
- `astra/validation` — promotion gates and red-team tests
- `campaigns` — reproducible experiment specifications
- `tests` — unit tests

## Run

```bash
python -m astra.research.loop campaigns/copyable_alpha_001.yaml
```

The current scaffold uses synthetic data until Solana/Pump.fun historical connectors are wired in.
