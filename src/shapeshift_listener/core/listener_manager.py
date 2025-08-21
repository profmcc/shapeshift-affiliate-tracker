"""
Listener manager for coordinating multiple affiliate fee listeners.
"""

import asyncio
import logging

from .base import BaseListener
from .config import Config


class ListenerManager:
    """Manages multiple affiliate fee listeners."""

    def __init__(self, config: Config):
        """Initialize the listener manager."""
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.listeners: dict[str, BaseListener] = {}
        self.running_tasks: list[asyncio.Task] = []

    def register_listener(self, chain: str, listener: BaseListener) -> None:
        """Register a listener for a specific chain."""
        self.listeners[chain.lower()] = listener
        self.logger.info(f"Registered listener for chain: {chain}")

    async def run_chain(self, chain: str, from_block: int | None = None, sink: str = "stdout") -> None:
        """Run a listener for a specific chain."""
        chain_lower = chain.lower()

        if chain_lower not in self.listeners:
            raise ValueError(f"No listener registered for chain: {chain}")

        listener = self.listeners[chain_lower]

        # Set up sink
        if sink == "stdout":
            self.logger.info(f"Running {chain} listener with stdout sink")
        elif sink == "csv":
            self.logger.info(f"Running {chain} listener with CSV sink")
        elif sink == "database":
            self.logger.info(f"Running {chain} listener with database sink")
        else:
            raise ValueError(f"Unsupported sink: {sink}")

        # Run the listener
        try:
            await listener.run(from_block=from_block)
        except Exception as e:
            self.logger.error(f"Failed to run {chain} listener: {e}", exc_info=True)
            raise

    async def run_all(self) -> None:
        """Run all registered listeners."""
        if not self.listeners:
            self.logger.warning("No listeners registered")
            return

        self.logger.info(f"Starting {len(self.listeners)} listeners")

        # Create tasks for all listeners
        tasks = []
        for _chain, listener in self.listeners.items():
            task = asyncio.create_task(listener.run())
            tasks.append(task)
            self.running_tasks.append(task)

        # Wait for all tasks to complete
        try:
            await asyncio.gather(*tasks, return_exceptions=True)
        except Exception as e:
            self.logger.error(f"Error running listeners: {e}", exc_info=True)
            raise
        finally:
            self.running_tasks.clear()

    def stop_all(self) -> None:
        """Stop all running listeners."""
        self.logger.info("Stopping all listeners")

        for listener in self.listeners.values():
            listener.stop()

        # Cancel running tasks
        for task in self.running_tasks:
            if not task.done():
                task.cancel()

        self.running_tasks.clear()

    async def health_check(self) -> dict[str, any]:
        """Perform health check on all listeners."""
        health_status = {
            "manager_status": "healthy",
            "listeners": {},
            "total_listeners": len(self.listeners),
            "running_tasks": len(self.running_tasks)
        }

        try:
            for chain, listener in self.listeners.items():
                listener_health = await listener.health_check()
                health_status["listeners"][chain] = listener_health

                if listener_health.get("status") == "unhealthy":
                    health_status["manager_status"] = "degraded"

        except Exception as e:
            health_status["manager_status"] = "unhealthy"
            health_status["error"] = str(e)

        return health_status

    def get_supported_chains(self) -> list[str]:
        """Get list of supported chains."""
        return list(self.listeners.keys())

    def get_listener(self, chain: str) -> BaseListener | None:
        """Get a specific listener by chain."""
        return self.listeners.get(chain.lower())
