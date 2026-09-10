import json
import os
import urllib.parse
import urllib.request


class HeliusClient:
    """Secondary Solana history source used to reconcile Birdeye backfills.

    Uses Helius getTransactionsForAddress rather than the deprecated Enhanced
    Transactions history endpoint.
    """

    BASE = "https://mainnet.helius-rpc.com/"

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.getenv("HELIUS_API_KEY")
        if not self.api_key:
            raise RuntimeError("HELIUS_API_KEY is required")

    def transactions_for_address(
        self,
        address: str,
        start_time: int,
        end_time: int,
        limit: int = 100,
        pagination_token: str | None = None,
    ) -> dict:
        url = f"{self.BASE}?{urllib.parse.urlencode({'api-key': self.api_key})}"
        config = {
            "transactionDetails": "full",
            "encoding": "jsonParsed",
            "maxSupportedTransactionVersion": 0,
            "sortOrder": "asc",
            "limit": limit,
            "filters": {
                "status": "succeeded",
                "tokenAccounts": "balanceChanged",
                "blockTime": {"gte": start_time, "lte": end_time},
            },
        }
        if pagination_token:
            config["paginationToken"] = pagination_token

        body = json.dumps({
            "jsonrpc": "2.0",
            "id": "astra-ca001",
            "method": "getTransactionsForAddress",
            "params": [address, config],
        }).encode("utf-8")
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        if payload.get("error"):
            raise RuntimeError(f"Helius RPC error: {payload['error']}")
        return payload.get("result") or {"data": [], "paginationToken": None}
