#!/usr/bin/env python3
"""
ShapeShift Affiliate Listener CLI

Command-line interface for running affiliate fee listeners.
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional

from .core.config import Config
from .core.listener_manager import ListenerManager


def setup_logging(level: str = "INFO", format_type: str = "json") -> None:
    """Set up logging configuration."""
    if format_type == "json":
        logging.basicConfig(
            level=getattr(logging, level.upper()),
            format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "name": "%(name)s", "message": "%(message)s"}'
        )
    else:
        logging.basicConfig(
            level=getattr(logging, level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="ShapeShift Affiliate Fee Listener",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run listener for Arbitrum from specific block
  ss-listener run --chain arbitrum --from-block 22222222 --sink stdout
  
  # Run with debug logging
  ss-listener run --chain base --from-block 32900000 --sink csv --log-level DEBUG
  
  # List available chains
  ss-listener list-chains
  
  # Check configuration
  ss-listener config --validate
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Run command
    run_parser = subparsers.add_parser("run", help="Run a listener")
    run_parser.add_argument("--chain", required=True, help="Chain to monitor (e.g., arbitrum, base, ethereum)")
    run_parser.add_argument("--from-block", type=int, help="Starting block number")
    run_parser.add_argument("--sink", default="stdout", choices=["stdout", "csv", "database"], help="Output destination")
    run_parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"], help="Log level")
    run_parser.add_argument("--config", type=Path, help="Path to configuration file")
    
    # List chains command
    list_parser = subparsers.add_parser("list-chains", help="List available chains")
    
    # Config command
    config_parser = subparsers.add_parser("config", help="Configuration management")
    config_parser.add_argument("--validate", action="store_true", help="Validate configuration")
    config_parser.add_argument("--show", action="store_true", help="Show current configuration")
    
    # Version command
    version_parser = subparsers.add_parser("version", help="Show version information")
    
    return parser.parse_args()


async def run_listener(args: argparse.Namespace) -> None:
    """Run a listener with the specified configuration."""
    try:
        # Load configuration
        config = Config.from_file(args.config) if args.config else Config.from_env()
        
        # Set up logging
        setup_logging(args.log_level)
        logger = logging.getLogger(__name__)
        
        logger.info("Starting ShapeShift Affiliate Listener", extra={
            "chain": args.chain,
            "from_block": args.from_block,
            "sink": args.sink
        })
        
        # Initialize and run listener manager
        manager = ListenerManager(config)
        await manager.run_chain(args.chain, args.from_block, args.sink)
        
    except Exception as e:
        logger.error(f"Failed to run listener: {e}", exc_info=True)
        sys.exit(1)


def list_chains() -> None:
    """List available chains."""
    chains = [
        {"name": "ethereum", "chain_id": 1, "description": "Ethereum Mainnet"},
        {"name": "polygon", "chain_id": 137, "description": "Polygon Mainnet"},
        {"name": "base", "chain_id": 8453, "description": "Base Mainnet"},
        {"name": "arbitrum", "chain_id": 42161, "description": "Arbitrum One"},
        {"name": "optimism", "chain_id": 10, "description": "Optimism Mainnet"},
        {"name": "avalanche", "chain_id": 43114, "description": "Avalanche C-Chain"},
        {"name": "bsc", "chain_id": 56, "description": "BNB Smart Chain"},
    ]
    
    print("Available Chains:")
    print("================")
    for chain in chains:
        print(f"{chain['name']:<12} (ID: {chain['chain_id']:<6}) - {chain['description']}")


def show_config(args: argparse.Namespace) -> None:
    """Show or validate configuration."""
    try:
        config = Config.from_env()
        
        if args.validate:
            config.validate()
            print("✅ Configuration is valid")
        
        if args.show:
            print("Current Configuration:")
            print("=====================")
            print(f"RPC Rate Limit: {config.rpc_rate_limit_per_second}/s")
            print(f"Batch Size: {config.batch_size}")
            print(f"Max Retries: {config.max_retries}")
            print(f"Log Level: {config.log_level}")
            print(f"Data Directory: {config.data_dir}")
            
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        sys.exit(1)


def show_version() -> None:
    """Show version information."""
    from . import __version__, __author__, __license__
    print(f"ShapeShift Affiliate Listener v{__version__}")
    print(f"Author: {__author__}")
    print(f"License: {__license__}")


async def main() -> None:
    """Main entry point."""
    args = parse_args()
    
    if args.command == "run":
        await run_listener(args)
    elif args.command == "list-chains":
        list_chains()
    elif args.command == "config":
        show_config(args)
    elif args.command == "version":
        show_version()
    else:
        print("Please specify a command. Use --help for more information.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

