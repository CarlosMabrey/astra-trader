import json
import os
import urllib.parse
import urllib.request
from typing import Iterable

from astra.data.types import WalletTrade


class BirdeyeClient:
    BASE = "https://public-api.birdeye.so"

    def __init__(self, api_key: str | None = None, chain: str = "solana") -> None:
        self.api_key = api_key or os.getenv("BIRDEYE_API_KEY")
        if not self.api_key:
            raise RuntimeError("BIRDEYE_API_KEY is required")
        self.chain = chain

    def _get(self, path: str, params: dict[str, object]) -> dict:
        url = f"{self.BASE}{path}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers={"X-API-KEY": self.api_key, "x-chain": self.chain})
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def trader_trades(self, wallet: str, after_time: int, before_time: int) -> Iterable[WalletTrade]:
        offset = 0
        while True:
            payload = self._get(
                "/trader/txs/seek_by_time",
                {"address": wallet, "after_time": after_time, "before_time": before_time,
                 "tx_type": "swap", "limit": 100, "offset": offset, "ui_amount_mode": "scaled"},
            )
            items = (payload.get("data") or {}).get("items") or []
            for item in items:
                yield self._normalize_trade(wallet, item)
            if len(items) < 100:
                break
            offset += len(items)
            if offset >= 10_000:
                break

    def historical_price(self, token: str, timestamp: int) -> float:
        payload = self._get("/defi/historical_price_unix", {"address": token, "unixtime": timestamp})
        data = payload.get("data") or {}
        value = data.get("value")
        if value is None:
            raise ValueError(f"No historical price for {token} at {timestamp}: {payload}")
        return float(value)

    def price_series(self, token: str, start: int, end: int, interval: str = "1m") -> list[tuple[int, float]]:
        payload = self._get(
            "/defi/history_price",
            {"address": token, "address_type": "token", "type": interval, "time_from": start, "time_to": end},
        )
        items = (payload.get("data") or {}).get("items") or []
        result: list[tuple[int, float]] = []
        for item in items:
            unix_time = item.get("unixTime") or item.get("unix_time")
            value = item.get("value")
            if unix_time is not None and value is not None:
                result.append((int(unix_time), float(value)))
        return result

    @staticmethod
    def _normalize_trade(wallet: str, item: dict) -> WalletTrade:
        side = str(item.get("side") or item.get("tradeType") or "").lower()
        token = item.get("tokenAddress") or item.get("base", {}).get("address") or item.get("quote", {}).get("address")
        timestamp = item.get("blockUnixTime") or item.get("unixTime") or item.get("timestamp")
        price = item.get("price") or item.get("nearestPrice")
        signature = item.get("txHash") or item.get("tx_hash") or item.get("signature") or ""
        amount = item.get("amount") or item.get("uiAmount") or 0.0
        if token is None or timestamp is None or price is None:
            raise ValueError(f"Unrecognized Birdeye trade payload: {item}")
        price_f = float(price)
        quantity = abs(float(amount or 0.0))
        return WalletTrade(wallet=wallet, token=str(token), side=side, timestamp=int(timestamp),
                           price_usd=price_f, quantity=quantity, notional_usd=quantity * price_f,
                           tx_signature=str(signature))
