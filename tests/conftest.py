"""
Pytest configuration and fixtures for ShapeShift Affiliate Listener tests.
"""

import pytest
from pathlib import Path

from shapeshift_listener.core.config import Config


@pytest.fixture
def test_config():
    """Create a test configuration."""
    return Config()


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Set up mock environment variables for testing."""
    monkeypatch.setenv("ALCHEMY_API_KEY", "test_key_12345")
    monkeypatch.setenv("BATCH_SIZE", "50")
    monkeypatch.setenv("RPC_RATE_LIMIT_PER_SECOND", "5")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("DATA_DIR", "./test_data")
    monkeypatch.setenv("MIN_VOLUME_USD", "0.0")


@pytest.fixture
def test_data_dir(tmp_path):
    """Create a temporary test data directory."""
    data_dir = tmp_path / "test_data"
    data_dir.mkdir()
    return data_dir


@pytest.fixture
def sample_config_file(tmp_path):
    """Create a sample configuration file for testing."""
    config_file = tmp_path / "test_config.yaml"
    config_content = """
    shapeshift_affiliates:
      primary: "0x35339070f178dC4119732982C23F5a8d88D3f8a3"
      relay: "0x9c9aA90363630d4ab1d9dbF416cc3BBC8d3Ed502"
      cowswap: "0x9c9aA90363630d4ab1d9dbF416cc3BBC8d3Ed502"
      butterswap: "0x35339070f178dC4119732982C23F5a8d88D3f8a3"
    
    rpc_providers:
      alchemy:
        api_key: "${ALCHEMY_API_KEY}"
        base_url: "https://base-mainnet.g.alchemy.com/v2/"
    
    chains:
      base:
        chain_id: 8453
        start_block: 32900000
        rpc_url: "https://base-mainnet.g.alchemy.com/v2/${ALCHEMY_API_KEY}"
    """
    
    config_file.write_text(config_content)
    return config_file
