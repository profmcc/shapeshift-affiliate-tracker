"""
ButterSwap affiliate fee listener.
"""

from typing import Any

from web3 import Web3

from ..core.base import BaseListener
from ..core.config import Config


class ButterSwapListener(BaseListener):
    """Listener for ButterSwap affiliate fee events."""

    def __init__(self, config: Config):
        """Initialize the ButterSwap listener."""
        super().__init__(config)
        self.web3 = None
        self.affiliate_addresses = {
            "base": "0x35339070f178dC4119732982C23F5a8d88D3f8a3",
            "ethereum": "0x90A48D5CF7343B08dA12E067680B4C6dbfE551Be",
            "polygon": "0xB5F944600785724e31Edb90F9DFa16dBF01Af000",
            "optimism": "0x6268d07327f4fb7380732dc6d63d95F88c0E083b",
            "arbitrum": "0x38276553F8fbf2A027D901F8be45f00373d8Dd48",
            "avalanche": "0x74d63F31C2335b5b3BA7ad2812357672b2624cEd",
            "bsc": "0x8b92b1698b57bEDF2142297e9397875ADBb2297E",
        }

    async def get_latest_block(self) -> int:
        """Get the latest block number."""
        if not self.web3:
            raise RuntimeError("Web3 connection not initialized")

        return self.web3.eth.block_number

    async def process_block(self, block_number: int) -> list[dict[str, Any]]:
        """Process a single block for ButterSwap affiliate events."""
        if not self.web3:
            raise RuntimeError("Web3 connection not initialized")

        try:
            # Get block information
            block = self.web3.eth.get_block(block_number, full_transactions=True)

            events = []
            for tx in block.transactions:
                # Check if transaction involves affiliate address
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
        """Check if transaction involves affiliate address."""
        # Check if any affiliate address is involved
        for address in self.affiliate_addresses.values():
            if address.lower() in tx.to.lower() or address.lower() in tx.from_.lower():
                return True
        return False

    def _parse_affiliate_event(self, tx: Any, block_number: int) -> dict[str, Any]:
        """Parse affiliate fee event from transaction."""
        try:
            return {
                "protocol": "butterswap",
                "chain": "base",  # TODO: Make this configurable
                "block_number": block_number,
                "transaction_hash": tx.hash.hex(),
                "from_address": tx.from_,
                "to_address": tx.to,
                "value": tx.value,
                "gas_price": tx.gasPrice,
                "gas_used": tx.gas,
                "timestamp": None,  # TODO: Get from block
                "affiliate_address": self._get_affiliate_address(tx),
                "fee_amount": None,  # TODO: Parse from transaction data
                "fee_token": None,  # TODO: Parse from transaction data
            }
        except Exception as e:
            self.logger.error(f"Error parsing affiliate event: {e}", exc_info=True)
            return None

    def _get_affiliate_address(self, tx: Any) -> str:
        """Get the affiliate address involved in the transaction."""
        for address in self.affiliate_addresses.values():
            if address.lower() in tx.to.lower() or address.lower() in tx.from_.lower():
                return address
        return None

    async def initialize(self, chain: str) -> None:
        """Initialize the listener for a specific chain."""
        try:
            rpc_url = self.config.get_rpc_url(chain)
            self.web3 = Web3(Web3.HTTPProvider(rpc_url))

            if not self.web3.is_connected():
                raise ConnectionError(f"Failed to connect to {chain} RPC")

            self.logger.info(f"Initialized ButterSwap listener for {chain}")

        except Exception as e:
            self.logger.error(
                f"Failed to initialize ButterSwap listener for {chain}: {e}",
                exc_info=True,
            )
            raise
