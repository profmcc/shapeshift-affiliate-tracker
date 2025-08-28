"""
Base listener class for affiliate fee monitoring.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any

from .config import Config


class BaseListener(ABC):
    """Base class for all affiliate fee listeners."""

    def __init__(self, config: Config):
        """Initialize the base listener."""
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.is_running = False

    @abstractmethod
    async def process_block(self, block_number: int) -> list[dict[str, Any]]:
        """Process a single block and return affiliate events."""
        pass

    @abstractmethod
    async def get_latest_block(self) -> int:
        """Get the latest block number for the chain."""
        pass

    async def run(
        self, from_block: int | None = None, to_block: int | None = None
    ) -> None:
        """Run the listener from a starting block."""
        try:
            self.is_running = True
            self.logger.info(
                "Starting listener",
                extra={"from_block": from_block, "to_block": to_block},
            )

            # Determine starting block
            if from_block is None:
                from_block = await self.get_latest_block()
                self.logger.info(f"Starting from latest block: {from_block}")

            # Process blocks
            current_block = from_block
            while self.is_running:
                try:
                    events = await self.process_block(current_block)

                    if events:
                        self.logger.info(
                            f"Found {len(events)} events in block {current_block}",
                            extra={"block": current_block, "event_count": len(events)},
                        )

                    current_block += 1

                    # Check if we've reached the target block
                    if to_block and current_block > to_block:
                        self.logger.info(f"Reached target block {to_block}, stopping")
                        break

                    # Rate limiting
                    await asyncio.sleep(1 / self.config.rpc_rate_limit_per_second)

                except Exception as e:
                    self.logger.error(
                        f"Error processing block {current_block}: {e}", exc_info=True
                    )
                    await asyncio.sleep(self.config.retry_delay_seconds)

        except Exception as e:
            self.logger.error(f"Listener failed: {e}", exc_info=True)
            raise
        finally:
            self.is_running = False
            self.logger.info("Listener stopped")

    def stop(self) -> None:
        """Stop the listener."""
        self.is_running = False
        self.logger.info("Stopping listener")

    async def health_check(self) -> dict[str, Any]:
        """Perform a health check of the listener."""
        try:
            latest_block = await self.get_latest_block()
            return {
                "status": "healthy",
                "latest_block": latest_block,
                "is_running": self.is_running,
                "config": self.config.to_dict(),
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "is_running": self.is_running,
            }
