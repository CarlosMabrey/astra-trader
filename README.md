# Astra Trader

Astra is an autonomous quantitative research system for discovering, falsifying, validating, and paper-trading market strategies before any live capital is allowed.

## Core loop

Observe -> Hypothesize -> Backtest -> Red-team -> Walk-forward validate -> Paper trade -> Evaluate -> Reweight -> Repeat

## Initial campaign: Copyable Alpha #001

Question: when a historically strong Solana/Pump.fun wallet buys a token, can Astra enter 1/5/10/30/60 seconds later and still earn positive net returns after fees and slippage?

The first milestone is not live trading. It is 1,000+ out-of-sample signals with positive realistic net expectancy and controlled drawdown.

## Data sources

### Free historical corpus (preferred first run)

`Slinky21/Pumpfun_Memecoin_Corpus` contains ~33.6M trade rows, ~26.9M bonding-curve snapshots, ~798k launches, and wallet-level identifiers over June 5–July 14, 2026. Astra's DuckDB miner can run CA-001 directly against its `trades.parquet` file.

```bash
pip install -e '.[dev]'
hf download Slinky21/Pumpfun_Memecoin_Corpus --repo-type dataset --local-dir data/pumpfun_corpus
python scripts/run_ca001_corpus.py \
  --trades data/pumpfun_corpus/trades.parquet \
  --wallet-limit 1000 \
  --hold 300 \
  --cost 0.015
```

Read the corpus `KNOWN_ISSUES.md` before interpreting results. We intentionally recompute wallet behavior from trade rows instead of trusting stale aggregate wallet statistics.

### API backfill / reconciliation

- Birdeye: exact trader executions plus historical token prices (`BIRDEYE_API_KEY`)
- Helius: independent Solana archival transaction history (`HELIUS_API_KEY`)

These are validation/reconciliation sources; the public corpus lets research begin without API spend.

## Safety architecture

- Live trading is disabled by default.
- Research agents cannot override risk policy.
- Strategy promotion is deterministic and gate-based.
- Every result is stored with dataset/version provenance.
- Red-team checks target leakage, survivorship bias, overfitting, unrealistic fills, outlier dependence, and regime fragility.

## Repo layout

- `astra/core` — shared experiment and strategy types
- `astra/data` — public-corpus and API adapters
- `astra/research` — hypothesis generation, wallet scoring, campaign orchestration
- `astra/backtest` — latency/slippage-aware simulation
- `astra/validation` — promotion gates and red-team tests
- `campaigns` — reproducible experiment specifications
- `scripts` — collection and campaign runners
- `tests` — unit/integration tests

## Run

```bash
python -m astra.research.loop campaigns/copyable_alpha_001.yaml
```

The research loop is operational; live execution remains disabled.
