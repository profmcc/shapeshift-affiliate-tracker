#!/usr/bin/env python3
"""
OnchainDen CLI - Command Line Interface for Transaction Analysis

Simple CLI tool for running OnchainDen analysis and generating reports.
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from pathlib import Path

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "shared"))

from enhanced_onchainden import EnhancedOnchainDenAnalyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def create_sample_config():
    """Create a sample configuration file."""
    sample_config = {
        "rpc_urls": {
            "1": "https://eth-mainnet.g.alchemy.com/v2/YOUR_ALCHEMY_KEY",
            "137": "https://polygon-mainnet.g.alchemy.com/v2/YOUR_ALCHEMY_KEY",
            "8453": "https://mainnet.base.org",
            "42161": "https://arb-mainnet.g.alchemy.com/v2/YOUR_ALCHEMY_KEY",
        },
        "api_keys": {
            "etherscan": "YOUR_ETHERSCAN_KEY",
            "polygonscan": "YOUR_POLYGONSCAN_KEY",
            "basescan": "YOUR_BASESCAN_KEY",
            "arbiscan": "YOUR_ARBISCAN_KEY",
        },
        "addresses": [
            "0x90a48d5cf7343b08da12e067680b4c6dbfe551be",
            "0x6268d07327f4fb7380732dc6d63d95f88c0e083b",
        ],
        "revenue_addresses": ["0x90a48d5cf7343b08da12e067680b4c6dbfe551be"],
        "expense_addresses": [],
        "ignored_addresses": [],
        "custom_rules": [
            {
                "type": "method_signature",
                "signature": "0xa9059cbb",
                "category": "Token Transfer",
                "subcategory": "ERC-20",
            }
        ],
    }

    config_dir = Path("config")
    config_dir.mkdir(exist_ok=True)

    config_file = config_dir / "onchainden_config.json"
    with open(config_file, "w") as f:
        json.dump(sample_config, f, indent=2)

    print(f"Sample configuration created at: {config_file}")
    print("Please edit the file with your actual API keys and addresses.")


def validate_config(config_path: str) -> bool:
    """Validate configuration file."""
    try:
        with open(config_path, "r") as f:
            config = json.load(f)

        required_keys = ["rpc_urls", "addresses"]
        for key in required_keys:
            if key not in config:
                print(f"Missing required key: {key}")
                return False

        if not config["addresses"]:
            print("No addresses specified in configuration")
            return False

        print("Configuration validation passed!")
        return True

    except Exception as e:
        print(f"Configuration validation failed: {e}")
        return False


async def run_analysis(config_path: str, output_format: str = "csv"):
    """Run the analysis with the specified configuration."""
    try:
        # Initialize analyzer
        analyzer = EnhancedOnchainDenAnalyzer(config_path)

        # Load configuration
        with open(config_path, "r") as f:
            config = json.load(f)

        addresses = config["addresses"]
        print(f"Starting analysis of {len(addresses)} addresses...")

        # Run analysis
        results = await analyzer.analyze_addresses(addresses)

        # Generate reports
        print("Generating reports...")
        if output_format == "csv":
            report_file = analyzer.generate_enhanced_report(addresses, "csv")
        elif output_format == "json":
            report_file = analyzer.generate_enhanced_report(addresses, "json")
        else:
            report_file = analyzer.generate_enhanced_report(addresses, "csv")

        print(f"Analysis complete! Report saved to: {report_file}")

        # Print summary
        print("\n=== ANALYSIS SUMMARY ===")
        for address, result in results.items():
            print(f"\nAddress: {address}")
            print(f"Total transactions: {result['summary']['total_transactions']}")
            print(f"Total gas costs: {result['summary']['total_gas_costs']:.6f} ETH")
            print(f"Categories: {result['summary']['categories']}")

            if result["summary"]["token_summary"]:
                print("Token summary:")
                for token, info in result["summary"]["token_summary"].items():
                    print(
                        f"  {token}: {info['count']} transactions, {info['total_amount']} total"
                    )

        return True

    except Exception as e:
        print(f"Analysis failed: {e}")
        logger.error(f"Analysis error: {e}")
        return False


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="OnchainDen Clone - Transaction Analysis & Revenue Tracking",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create sample configuration
  python onchainden_cli.py --create-config
  
  # Validate configuration
  python onchainden_cli.py --validate-config config/onchainden_config.json
  
  # Run analysis with CSV output
  python onchainden_cli.py --analyze config/onchainden_config.json --output csv
  
  # Run analysis with JSON output
  python onchainden_cli.py --analyze config/onchainden_config.json --output json
        """,
    )

    parser.add_argument(
        "--create-config",
        action="store_true",
        help="Create a sample configuration file",
    )

    parser.add_argument(
        "--validate-config", metavar="CONFIG_FILE", help="Validate a configuration file"
    )

    parser.add_argument(
        "--analyze",
        metavar="CONFIG_FILE",
        help="Run analysis with the specified configuration file",
    )

    parser.add_argument(
        "--output",
        choices=["csv", "json"],
        default="csv",
        help="Output format for reports (default: csv)",
    )

    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Handle different commands
    if args.create_config:
        create_sample_config()
        return

    elif args.validate_config:
        if validate_config(args.validate_config):
            sys.exit(0)
        else:
            sys.exit(1)

    elif args.analyze:
        if not os.path.exists(args.analyze):
            print(f"Configuration file not found: {args.analyze}")
            sys.exit(1)

        # Validate config first
        if not validate_config(args.analyze):
            print(
                "Configuration validation failed. Please fix the issues and try again."
            )
            sys.exit(1)

        # Run analysis
        success = asyncio.run(run_analysis(args.analyze, args.output))
        if not success:
            sys.exit(1)

    else:
        parser.print_help()
        print("\nNo action specified. Use --help for usage information.")
        sys.exit(1)


if __name__ == "__main__":
    main()
