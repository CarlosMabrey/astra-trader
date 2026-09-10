import csv
from dataclasses import asdict
from pathlib import Path

from astra.data.birdeye import BirdeyeClient
from astra.data.types import WalletTrade


def load_wallets(path: str | Path) -> list[str]:
    wallets: list[str] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            wallet = line.strip()
            if wallet and not wallet.startswith("#"):
                wallets.append(wallet)
    return wallets


def collect_wallet_trades(
    wallets: list[str],
    after_time: int,
    before_time: int,
    client: BirdeyeClient,
) -> list[WalletTrade]:
    trades: list[WalletTrade] = []
    for wallet in wallets:
        trades.extend(client.trader_trades(wallet, after_time, before_time))
    trades.sort(key=lambda t: (t.timestamp, t.wallet, t.tx_signature))
    return trades


def write_trades_csv(path: str | Path, trades: list[WalletTrade]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    rows = [asdict(t) for t in trades]
    if not rows:
        target.write_text("", encoding="utf-8")
        return
    with open(target, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
