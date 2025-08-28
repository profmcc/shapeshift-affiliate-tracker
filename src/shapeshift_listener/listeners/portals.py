"""
Portals protocol affiliate fee listener.
"""

from typing import Any, List
from web3 import Web3

from ..core.base import BaseListener
from ..core.config import Config


class PortalsListener(BaseListener):
    """Listener for Portals protocol affiliate fee events."""

    def __init__(self, config: Config):
        """Initialize the Portals listener."""
        super().__init__(config)
        self.web3 = None
        # Portals uses the Base Safe address for affiliate tracking
        self.affiliate_address = "0x9c9aA90363630d4ab1D9dbF416cc3BBC8d3Ed502"

    async def get_latest_block(self) -> int:
        """Get the latest block number."""
        if not self.web3:
            raise RuntimeError("Web3 connection not initialized")
        return self.web3.eth.block_number

    async def process_block(self, block_number: int) -> List[dict[str, Any]]:
        """Process a single block for Portals affiliate events."""
        if not self.web3:
            raise RuntimeError("Web3 connection not initialized")

        try:
            # Get block information
            block = self.web3.eth.get_block(block_number, full_transactions=True)

            events = []
            for tx in block.transactions:
                # Check if transaction involves Portals affiliate address
                if self._is_affiliate_transaction(tx):
                    event = self._parse_affiliate_event(tx, block_number)
                    if event:
                        events.append(event)

            return events

        except Exception as e:
            self.logger.error(
                f"Error processing block {block_number}: {e}", exc_info=True
            )
            return []

    def _is_affiliate_transaction(self, tx: Any) -> bool:
        """Check if transaction involves Portals affiliate address."""
        # Check if Portals affiliate address is involved
        return (
            self.affiliate_address.lower() in tx.to.lower() 
            or self.affiliate_address.lower() in tx.from_.lower()
        )

    def _parse_affiliate_event(self, tx: Any, block_number: int) -> dict[str, Any]:
        """Parse affiliate fee event from Portals transaction."""
        try:
            return {
                "protocol": "portals",
                "chain": "base",  # TODO: Make this configurable
                "block_number": block_number,
                "transaction_hash": tx.hash.hex(),
                "from_address": tx.from_,
                "to_address": tx.to,
                "value": tx.value,
                "gas_price": tx.gasPrice,
                "gas_used": tx.gas,
                "timestamp": None,  # TODO: Get from block
                "affiliate_address": self.affiliate_address,
                "fee_amount": None,  # TODO: Parse from transaction data
                "fee_token": None,  # TODO: Parse from transaction data
            }
        except Exception as e:
            self.logger.error(f"Error parsing Portals affiliate event: {e}", exc_info=True)
            return None

    async def initialize(self, chain: str) -> None:
        """Initialize the listener for a specific chain."""
        try:
            rpc_url = self.config.get_rpc_url(chain)
            self.web3 = Web3(Web3.HTTPProvider(rpc_url))

            if not self.web3.is_connected():
                raise ConnectionError(f"Failed to connect to {chain} RPC")

            self.logger.info(f"Initialized Portals listener for {chain}")

        except Exception as e:
            self.logger.error(
                f"Failed to initialize Portals listener for {chain}: {e}",
                exc_info=True,
            )
            raise
