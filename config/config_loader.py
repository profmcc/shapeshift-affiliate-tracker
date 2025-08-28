#!/usr/bin/env python3
"""
Configuration Loader for Relay Affiliate Fee Listener
====================================================

A simplified, standalone configuration management system that loads
settings from YAML files and environment variables.
"""

import os
import yaml
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv


class ConfigLoader:
    """
    Configuration loader for the Relay listener
    
    Loads configuration from YAML files and environment variables
    with graceful fallbacks and error handling.
    """

    def __init__(self, config_path: str = None):
        """
        Initialize config loader with path to config file
        
        Args:
            config_path: Path to configuration file. If None, uses default.
        """
        if config_path is None:
            # Get the directory where this script is located
            script_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(script_dir, "config.yaml")

        self.config_path = config_path
        self.config = None

        # Load configuration
        self._load_config()

    def _load_config(self):
        """Load configuration from YAML file and resolve environment variables"""
        try:
            # Load environment variables first
            load_dotenv()

            # Read config file
            with open(self.config_path, "r") as file:
                config_content = file.read()

            # Replace environment variables
            config_content = os.path.expandvars(config_content)

            # Parse YAML
            self.config = yaml.safe_load(config_content)

            if not self.config:
                raise ValueError("Configuration file is empty or invalid")

        except FileNotFoundError:
            print(f"Warning: Configuration file not found: {self.config_path}")
            self.config = self._get_default_config()
        except Exception as e:
            print(f"Warning: Error loading configuration: {e}")
            self.config = self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration if file loading fails"""
        return {
            "api": {
                "alchemy_api_key": os.getenv("ALCHEMY_API_KEY", ""),
                "infura_api_key": os.getenv("INFURA_API_KEY", ""),
            },
            "shapeshift_affiliates": {
                "base": "0x9c9aA90363630d4ab1D9dbF416cc3BBC8d3Ed502",
                "legacy_relay": "0x2905d7e4d048d29954f81b02171dd313f457a4a4",
            },
            "chains": {
                "base": {
                    "name": "Base",
                    "rpc_url": f"https://base-mainnet.g.alchemy.com/v2/{os.getenv('ALCHEMY_API_KEY', '')}",
                    "start_block": 32900000,
                    "chunk_size": 100,
                    "delay": 0.5,
                }
            },
            "protocols": {
                "relay": {
                    "contracts": {
                        "base": "0xF5042e6ffaC5a625D4E7848e0b01373D8eB9e222"
                    },
                    "events": {
                        "affiliate_fee": "AffiliateFee(address,address,uint256,address,uint256)",
                        "transfer": "Transfer(address,address,uint256)"
                    },
                    "listener": {
                        "chunk_size": 100,
                        "delay": 0.5,
                        "max_blocks": 1000,
                        "min_volume_usd": 0
                    }
                }
            },
            "storage": {
                "csv_directory": "data",
                "file_patterns": {
                    "relay": "relay_transactions.csv",
                    "block_tracker": "{protocol}_block_tracker.csv"
                }
            },
            "thresholds": {
                "minimum_volume_usd": 0,
                "minimum_fee_usd": 0
            }
        }

    def get_config(self) -> 'Config':
        """Get the configuration object"""
        return Config(self.config)

    def reload(self):
        """Reload configuration from file"""
        self._load_config()


class Config:
    """Configuration wrapper with helper methods"""

    def __init__(self, config_data: Dict[str, Any]):
        self.config = config_data

    def get_alchemy_api_key(self) -> str:
        """Get Alchemy API key"""
        return self.config.get("api", {}).get("alchemy_api_key", "")

    def get_infura_api_key(self) -> str:
        """Get Infura API key"""
        return self.config.get("api", {}).get("infura_api_key", "")

    def get_all_shapeshift_addresses(self) -> List[str]:
        """Get all ShapeShift affiliate addresses"""
        affiliates = self.config.get("shapeshift_affiliates", {})
        addresses = []
        
        # Add chain-specific addresses
        for chain, address in affiliates.items():
            if isinstance(address, str) and address.startswith("0x"):
                addresses.append(address)
        
        # Add variations if they exist
        variations = affiliates.get("variations", [])
        if isinstance(variations, list):
            addresses.extend([addr for addr in variations if isinstance(addr, str) and addr.startswith("0x")])
        
        return list(set(addresses))  # Remove duplicates

    def get_chain_config(self, chain_name: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific chain"""
        chains = self.config.get("chains", {})
        return chains.get(chain_name)

    def get_contract_address(self, protocol: str, chain: str) -> str:
        """Get contract address for a protocol on a specific chain"""
        protocols = self.config.get("protocols", {})
        protocol_config = protocols.get(protocol, {})
        contracts = protocol_config.get("contracts", {})
        return contracts.get(chain, "0x0000000000000000000000000000000000000000")

    def get_event_signature(self, protocol: str, event_name: str) -> str:
        """Get event signature for a protocol"""
        protocols = self.config.get("protocols", {})
        protocol_config = protocols.get(protocol, {})
        events = protocol_config.get("events", {})
        return events.get(event_name, "")

    def get_storage_path(self, path_type: str, protocol: str = None) -> str:
        """Get storage path for files"""
        storage = self.config.get("storage", {})
        
        if path_type == "csv_directory":
            return storage.get("csv_directory", "data")
        elif path_type == "file_pattern":
            patterns = storage.get("file_patterns", {})
            if protocol:
                return patterns.get(protocol, f"{protocol}_data.csv")
            return patterns.get("relay", "relay_transactions.csv")
        
        return "data"

    def get_listener_config(self, protocol: str) -> Dict[str, Any]:
        """Get listener configuration for a protocol"""
        protocols = self.config.get("protocols", {})
        protocol_config = protocols.get(protocol, {})
        return protocol_config.get("listener", {})

    def get_threshold(self, threshold_name: str) -> float:
        """Get threshold value"""
        thresholds = self.config.get("thresholds", {})
        return thresholds.get(threshold_name, 0.0)

    def get_supported_chains(self) -> List[str]:
        """Get list of supported chains"""
        return list(self.config.get("chains", {}).keys())

    def get_protocol_contracts(self, protocol: str) -> Dict[str, str]:
        """Get all contract addresses for a protocol"""
        protocols = self.config.get("protocols", {})
        protocol_config = protocols.get(protocol, {})
        return protocol_config.get("contracts", {})


# Convenience functions for backward compatibility
def get_config(config_path: str = None) -> Config:
    """Get configuration object"""
    loader = ConfigLoader(config_path)
    return loader.get_config()

def get_shapeshift_address(chain: str = None) -> str:
    """Get ShapeShift address for a specific chain"""
    config = get_config()
    if chain:
        addresses = config.config.get("shapeshift_affiliates", {})
        return addresses.get(chain, "")
    return ""

def get_contract_address(protocol: str, chain: str) -> str:
    """Get contract address for a protocol on a chain"""
    config = get_config()
    return config.get_contract_address(protocol, chain)

def get_chain_config(chain: str) -> Optional[Dict[str, Any]]:
    """Get chain configuration"""
    config = get_config()
    return config.get_chain_config(chain)

def get_storage_path(path_type: str, protocol: str = None) -> str:
    """Get storage path"""
    config = get_config()
    return config.get_storage_path(path_type, protocol)

def get_listener_config(protocol: str) -> Dict[str, Any]:
    """Get listener configuration"""
    config = get_config()
    return config.get_listener_config(protocol)

def get_event_signature(protocol: str, event_name: str) -> str:
    """Get event signature"""
    config = get_config()
    return config.get_event_signature(protocol, event_name)

def get_threshold(threshold_name: str) -> float:
    """Get threshold value"""
    config = get_config()
    return config.get_threshold(threshold_name)
