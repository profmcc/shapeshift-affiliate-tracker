"""
ShapeShift Affiliate Listener

A comprehensive blockchain monitoring system that tracks ShapeShift's affiliate fee revenue
across multiple DeFi protocols and chains.
"""

__version__ = "0.1.0"
__author__ = "ShapeShift Affiliate Listener Contributors"
__license__ = "MIT"

from .core.base import BaseListener
from .core.config import Config

__all__ = ["BaseListener", "Config"]

