"""
Configuration management for ShapeShift Affiliate Listener.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from dotenv import load_dotenv


class Config:
    """Configuration manager for the affiliate listener."""
    
    def __init__(self, config_data: Optional[Dict[str, Any]] = None):
        """Initialize configuration."""
        self.config_data = config_data or {}
        self._load_env_vars()
    
    @classmethod
    def from_env(cls) -> "Config":
        """Create configuration from environment variables."""
        load_dotenv()
        return cls()
    
    @classmethod
    def from_file(cls, config_path: Path) -> "Config":
        """Create configuration from YAML file."""
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)
        
        return cls(config_data)
    
    def _load_env_vars(self) -> None:
        """Load configuration from environment variables."""
        # RPC Configuration
        self.alchemy_api_key = os.getenv("ALCHEMY_API_KEY")
        self.infura_api_key = os.getenv("INFURA_API_KEY")
        
        # Rate Limiting & Performance
        self.rpc_rate_limit_per_second = int(os.getenv("RPC_RATE_LIMIT_PER_SECOND", "10"))
        self.batch_size = int(os.getenv("BATCH_SIZE", "100"))
        self.max_retries = int(os.getenv("MAX_RETRIES", "3"))
        self.retry_delay_seconds = float(os.getenv("RETRY_DELAY_SECONDS", "1"))
        
        # Logging & Monitoring
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.log_format = os.getenv("LOG_FORMAT", "json")
        self.metrics_enabled = os.getenv("METRICS_ENABLED", "true").lower() == "true"
        self.prometheus_port = int(os.getenv("PROMETHEUS_PORT", "9090"))
        
        # Data Storage
        self.data_dir = Path(os.getenv("DATA_DIR", "./data"))
        self.csv_output_dir = Path(os.getenv("CSV_OUTPUT_DIR", "./data/csv"))
        self.database_url = os.getenv("DATABASE_URL", "sqlite:///./data/affiliate_fees.db")
        
        # Security & Validation
        self.reorg_window_blocks = int(os.getenv("REORG_WINDOW_BLOCKS", "25"))
        self.confirmation_blocks = int(os.getenv("CONFIRMATION_BLOCKS", "12"))
        self.min_volume_usd = float(os.getenv("MIN_VOLUME_USD", "0.0"))
        
        # Development & Testing
        self.debug_mode = os.getenv("DEBUG_MODE", "false").lower() == "true"
        self.testnet_mode = os.getenv("TESTNET_MODE", "false").lower() == "true"
        self.mock_rpc = os.getenv("MOCK_RPC", "false").lower() == "true"
    
    def validate(self) -> None:
        """Validate configuration values."""
        errors = []
        
        # Check required API keys
        if not self.alchemy_api_key and not self.infura_api_key:
            errors.append("At least one RPC provider API key is required (ALCHEMY_API_KEY or INFURA_API_KEY)")
        
        # Check numeric values
        if self.rpc_rate_limit_per_second <= 0:
            errors.append("RPC_RATE_LIMIT_PER_SECOND must be positive")
        
        if self.batch_size <= 0:
            errors.append("BATCH_SIZE must be positive")
        
        if self.max_retries < 0:
            errors.append("MAX_RETRIES must be non-negative")
        
        if self.retry_delay_seconds < 0:
            errors.append("RETRY_DELAY_SECONDS must be non-negative")
        
        if errors:
            raise ValueError(f"Configuration validation failed:\n" + "\n".join(f"- {error}" for error in errors))
    
    def get_rpc_url(self, chain: str) -> str:
        """Get RPC URL for a specific chain."""
        if chain.lower() == "base":
            if self.alchemy_api_key:
                return f"https://base-mainnet.g.alchemy.com/v2/{self.alchemy_api_key}"
            elif self.infura_api_key:
                return f"https://base-mainnet.infura.io/v3/{self.infura_api_key}"
        elif chain.lower() == "ethereum":
            if self.alchemy_api_key:
                return f"https://eth-mainnet.g.alchemy.com/v2/{self.alchemy_api_key}"
            elif self.infura_api_key:
                return f"https://mainnet.infura.io/v3/{self.infura_api_key}"
        elif chain.lower() == "polygon":
            if self.alchemy_api_key:
                return f"https://polygon-mainnet.g.alchemy.com/v2/{self.alchemy_api_key}"
            elif self.infura_api_key:
                return f"https://polygon-mainnet.infura.io/v3/{self.infura_api_key}"
        
        raise ValueError(f"No RPC URL configured for chain: {chain}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "rpc_rate_limit_per_second": self.rpc_rate_limit_per_second,
            "batch_size": self.batch_size,
            "max_retries": self.max_retries,
            "retry_delay_seconds": self.retry_delay_seconds,
            "log_level": self.log_level,
            "log_format": self.log_format,
            "metrics_enabled": self.metrics_enabled,
            "data_dir": str(self.data_dir),
            "csv_output_dir": str(self.csv_output_dir),
            "reorg_window_blocks": self.reorg_window_blocks,
            "confirmation_blocks": self.confirmation_blocks,
            "min_volume_usd": self.min_volume_usd,
        }

