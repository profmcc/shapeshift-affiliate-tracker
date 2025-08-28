"""
Basic tests for ShapeShift Affiliate Listener.
"""

import pytest
from shapeshift_listener import __version__, __author__, __license__


def test_version():
    """Test that version information is available."""
    assert __version__ == "0.1.0"
    assert __author__ == "ShapeShift Affiliate Listener Contributors"
    assert __license__ == "MIT"


def test_imports():
    """Test that core modules can be imported."""
    from shapeshift_listener.core.config import Config
    from shapeshift_listener.core.base import BaseListener
    from shapeshift_listener.core.listener_manager import ListenerManager

    assert Config is not None
    assert BaseListener is not None
    assert ListenerManager is not None


def test_config_creation():
    """Test that Config can be created."""
    from shapeshift_listener.core.config import Config

    config = Config()
    assert config.rpc_rate_limit_per_second == 10
    assert config.batch_size == 100
    assert config.log_level == "INFO"
