"""
Chainflip affiliate fee listener.
"""

from typing import Any, List
import aiohttp

from ..core.base import BaseListener
from ..core.config import Config


class ChainflipListener(BaseListener):
    """Listener for Chainflip affiliate fee events."""

    def __init__(self, config: Config):
        """Initialize the Chainflip listener."""
        super().__init__(config)
        # Chainflip uses native address format
        self.affiliate_address = "cFMeDPtPHccVYdBSJKTtCYuy7rewFNpro3xZBKaCGbSS2xhRi"
        self.chainflip_api_url = "https://api.chainflip.io"  # Example API endpoint

    async def get_latest_block(self) -> int:
        """Get the latest block number from Chainflip."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.chainflip_api_url}/status") as response:
                    if response.status == 200:
                        data = await response.json()
                        return int(data.get("result", {}).get("block", 0))
                    else:
                        self.logger.error(f"Failed to get Chainflip status: {response.status}")
                        return 0
        except Exception as e:
            self.logger.error(f"Error getting Chainflip latest block: {e}")
            return 0

    async def process_block(self, block_number: int) -> List[dict[str, Any]]:
        """Process a single block for Chainflip affiliate events."""
        try:
            # Chainflip processes transactions differently than EVM chains
            # We need to query the Chainflip API for transactions
            events = []
            
            # Query recent transactions from Chainflip API
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.chainflip_api_url}/transactions") as response:
                    if response.status == 200:
                        data = await response.json()
                        transactions = data.get("transactions", [])
                        
                        for tx in transactions:
                            if self._is_affiliate_transaction(tx):
                                event = self._parse_affiliate_event(tx, block_number)
                                if event:
                                    events.append(event)
            
            return events

        except Exception as e:
            self.logger.error(
                f"Error processing Chainflip block {block_number}: {e}", exc_info=True
            )
            return []

    def _is_affiliate_transaction(self, tx: dict) -> bool:
        """Check if Chainflip transaction involves affiliate address."""
        # Check for affiliate address in transaction data
        return self.affiliate_address.lower() in str(tx).lower()

    def _parse_affiliate_event(self, tx: dict, block_number: int) -> dict[str, Any]:
        """Parse affiliate fee event from Chainflip transaction."""
        try:
            return {
                "protocol": "chainflip",
                "chain": "chainflip",  # Chainflip native chain
                "block_number": block_number,
                "transaction_hash": tx.get("id", ""),
                "from_address": tx.get("from", ""),
                "to_address": tx.get("to", ""),
                "value": tx.get("amount", "0"),
                "gas_price": None,  # Not applicable for Chainflip
                "gas_used": None,   # Not applicable for Chainflip
                "timestamp": tx.get("timestamp", None),
                "affiliate_address": self.affiliate_address,
                "fee_amount": tx.get("fee", "0"),
                "fee_token": tx.get("fee_asset", ""),
            }
        except Exception as e:
            self.logger.error(f"Error parsing Chainflip affiliate event: {e}", exc_info=True)
            return None

    async def initialize(self, chain: str) -> None:
        """Initialize the Chainflip listener."""
        try:
            # Chainflip doesn't use traditional RPC, it uses REST API
            self.logger.info(f"Initialized Chainflip listener")
        except Exception as e:
            self.logger.error(
                f"Failed to initialize Chainflip listener: {e}",
                exc_info=True,
            )
            raise
