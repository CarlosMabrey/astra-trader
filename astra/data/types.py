from dataclasses import dataclass


@dataclass(frozen=True)
class WalletTrade:
    wallet: str
    token: str
    side: str
    timestamp: int
    price_usd: float
    quantity: float
    notional_usd: float
    tx_signature: str


@dataclass(frozen=True)
class MarketSnapshot:
    token: str
    timestamp: int
    price_usd: float
    liquidity_usd: float
    market_cap_usd: float
    volume_1m_usd: float = 0.0
    buys_1m: int = 0
    sells_1m: int = 0
