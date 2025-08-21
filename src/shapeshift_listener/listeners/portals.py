"""
Portals protocol affiliate fee listener.
"""

from ..core.base import BaseListener
from ..core.config import Config


class PortalsListener(BaseListener):
    """Listener for Portals protocol affiliate fee events."""
    
    def __init__(self, config: Config):
        """Initialize the Portals listener."""
        super().__init__(config)
    
    async def get_latest_block(self) -> int:
        """Get the latest block number."""
        # TODO: Implement
        return 0
    
    async def process_block(self, block_number: int):
        """Process a single block for Portals affiliate events."""
        # TODO: Implement
        return []
