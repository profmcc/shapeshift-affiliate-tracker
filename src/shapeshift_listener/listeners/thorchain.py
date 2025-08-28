"""
THORChain affiliate fee listener.
"""

from typing import Any, List
import aiohttp

from ..core.base import BaseListener
from ..core.config import Config


class ThorChainListener(BaseListener):
    """Listener for THORChain affiliate fee events."""

    def __init__(self, config: Config):
        """Initialize the THORChain listener."""
        super().__init__(config)
        # THORChain uses native address format and name abbreviation
        self.affiliate_address = "thor122h9hlrugzdny9ct95z6g7afvpzu34s73uklju"
        self.affiliate_name = "ss"  # THORChain affiliate name abbreviation
        self.midgard_api_url = "https://midgard.thorchain.info/v2"

    async def get_latest_block(self) -> int:
        """Get the latest block number from THORChain."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.midgard_api_url}/status") as response:
                    if response.status == 200:
                        data = await response.json()
                        return int(data.get("result", {}).get("block", 0))
                    else:
                        self.logger.error(f"Failed to get THORChain status: {response.status}")
                        return 0
        except Exception as e:
            self.logger.error(f"Error getting THORChain latest block: {e}")
            return 0

    async def process_block(self, block_number: int) -> List[dict[str, Any]]:
        """Process a single block for THORChain affiliate events."""
        try:
            # THORChain processes transactions differently than EVM chains
            # We need to query the Midgard API for transactions
            events = []
            
            # Query recent transactions from Midgard API
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.midgard_api_url}/actions") as response:
                    if response.status == 200:
                        data = await response.json()
                        actions = data.get("actions", [])
                        
                        for action in actions:
                            if self._is_affiliate_transaction(action):
                                event = self._parse_affiliate_event(action, block_number)
                                if event:
                                    events.append(event)
            
            return events

        except Exception as e:
            self.logger.error(
                f"Error processing THORChain block {block_number}: {e}", exc_info=True
            )
            return []

    def _is_affiliate_transaction(self, action: dict) -> bool:
        """Check if THORChain action involves affiliate address or name."""
        # Check for affiliate address in memo or other fields
        memo = action.get("memo", "").lower()
        return (
            self.affiliate_address.lower() in str(action).lower() or
            self.affiliate_name.lower() in memo
        )

    def _parse_affiliate_event(self, action: dict, block_number: int) -> dict[str, Any]:
        """Parse affiliate fee event from THORChain action."""
        try:
            return {
                "protocol": "thorchain",
                "chain": "thorchain",  # THORChain native chain
                "block_number": block_number,
                "transaction_hash": action.get("id", ""),
                "from_address": action.get("in", {}).get("address", ""),
                "to_address": action.get("out", {}).get("address", ""),
                "value": action.get("in", {}).get("amount", "0"),
                "gas_price": None,  # Not applicable for THORChain
                "gas_used": None,   # Not applicable for THORChain
                "timestamp": action.get("date", None),
                "affiliate_address": self.affiliate_address,
                "affiliate_name": self.affiliate_name,
                "fee_amount": action.get("fee", "0"),
                "fee_token": action.get("fee_asset", ""),
                "memo": action.get("memo", ""),
            }
        except Exception as e:
            self.logger.error(f"Error parsing THORChain affiliate event: {e}", exc_info=True)
            return None

    async def initialize(self, chain: str) -> None:
        """Initialize the THORChain listener."""
        try:
            # THORChain doesn't use traditional RPC, it uses REST API
            self.logger.info(f"Initialized THORChain listener")
        except Exception as e:
            self.logger.error(
                f"Failed to initialize THORChain listener: {e}",
                exc_info=True,
            )
            raise
