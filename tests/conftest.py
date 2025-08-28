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
      # Main Safe addresses for general affiliate tracking (chain-specific)
      mainnet: "0x90A48D5CF7343B08dA12E067680B4C6dbfE551Be"      # Ethereum Mainnet Safe
      base: "0x9c9aA90363630d4ab1D9dbF416cc3BBC8d3Ed502"         # Base Safe
      optimism: "0x6268d07327f4fb7380732dc6d63d95F88c0E083b"      # Optimism Safe
      avalanche: "0x74d63F31C2335b5b3BA7ad2812357672b2624cEd"     # Avalanche Safe
      polygon: "0xB5F944600785724e31Edb90F9DFa16dBF01Af000"       # Polygon Safe
      gnosis: "0xb0E3175341794D1dc8E5F02a02F9D26989EbedB3"        # Gnosis Chain Safe
      bsc: "0x8b92b1698b57bEDF2142297e9397875ADBb2297E"           # Binance Smart Chain Safe
      arbitrum: "0x38276553F8fbf2A027D901F8be45f00373d8Dd48"      # Arbitrum Safe
      
      # Protocol-specific addresses
      butterswap: "0x35339070f178dC4119732982C23F5a8d88D3f8a3"   # ButterSwap affiliate (d3f8a3) - ONLY for ButterSwap
      portals: "0x9c9aA90363630d4ab1D9dbF416cc3BBC8d3Ed502"       # Portals affiliate
      thorchain: "thor122h9hlrugzdny9ct95z6g7afvpzu34s73uklju"    # THORChain affiliate
      chainflip: "cFMeDPtPHccVYdBSJKTtCYuy7rewFNpro3xZBKaCGbSS2xhRi"  # Chainflip affiliate
    
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
