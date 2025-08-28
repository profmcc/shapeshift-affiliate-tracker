#!/usr/bin/env python3
"""
Example Usage of OnchainDen Clone

This script demonstrates various ways to use the OnchainDen clone system
for transaction analysis and revenue tracking.
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "shared"))

from enhanced_onchainden import (
    EnhancedOnchainDenAnalyzer,
    EnhancedTransactionCategorizer,
    ERC20Parser,
)


async def example_basic_analysis():
    """Example 1: Basic address analysis."""
    print("=== Example 1: Basic Address Analysis ===")

    # Create a simple configuration
    config = {
        "rpc_urls": {
            1: "https://eth-mainnet.g.alchemy.com/v2/YOUR_KEY",
            137: "https://polygon-mainnet.g.alchemy.com/v2/YOUR_KEY",
        },
        "api_keys": {},
        "addresses": ["0x90a48d5cf7343b08da12e067680b4c6dbfe551be"],
        "revenue_addresses": ["0x90a48d5cf7343b08da12e067680b4c6dbfe551be"],
        "expense_addresses": [],
        "ignored_addresses": [],
        "custom_rules": [],
    }

    # Save config
    os.makedirs("config", exist_ok=True)
    with open("config/example_config.json", "w") as f:
        json.dump(config, f, indent=2)

    print("Configuration saved to config/example_config.json")
    print("Please edit with your actual API keys before running analysis.")

    # Note: This would require actual API keys to run
    # analyzer = EnhancedOnchainDenAnalyzer("config/example_config.json")
    # results = await analyzer.analyze_addresses(config["addresses"])
    # print(f"Analysis complete for {len(config['addresses'])} addresses")


def example_custom_categorization():
    """Example 2: Custom transaction categorization."""
    print("\n=== Example 2: Custom Transaction Categorization ===")

    # Create custom categorization rules
    config = {
        "revenue_addresses": ["0x90a48d5cf7343b08da12e067680b4c6dbfe551be"],
        "expense_addresses": ["0x74d63f31c2335b5b3ba7ad2812357672b2624ced"],
        "ignored_addresses": ["0xb5f944600785724e31edb90f9dfa16dbf01af000"],
        "custom_rules": [
            {
                "type": "address_pattern",
                "pattern": "0x1234",
                "category": "Custom",
                "subcategory": "Special",
            },
            {
                "type": "value_threshold",
                "threshold": "1000000000000000000000",  # 1 ETH
                "category": "Large Transfer",
                "subcategory": "High Value",
            },
            {
                "type": "method_signature",
                "signature": "0xa9059cbb",  # transfer(address,uint256)
                "category": "Token Transfer",
                "subcategory": "ERC-20",
            },
        ],
    }

    # Initialize categorizer
    categorizer = EnhancedTransactionCategorizer(config)

    print("Custom categorization rules configured:")
    print(f"- Revenue addresses: {len(config['revenue_addresses'])}")
    print(f"- Expense addresses: {len(config['expense_addresses'])}")
    print(f"- Ignored addresses: {len(config['ignored_addresses'])}")
    print(f"- Custom rules: {len(config['custom_rules'])}")

    # Example rule types
    print("\nRule types supported:")
    for rule in config["custom_rules"]:
        print(f"- {rule['type']}: {rule['category']} -> {rule['subcategory']}")


def example_erc20_parsing():
    """Example 3: ERC-20 event parsing."""
    print("\n=== Example 3: ERC-20 Event Parsing ===")

    # Initialize ERC-20 parser
    parser = ERC20Parser()

    # Example transfer event log
    example_log = {
        "topics": [
            "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef",
            "0x000000000000000000000000a0b86a33e6441b8c4a8f7c13b45b1d3c9f5954e0",
            "0x000000000000000000000000b0c86a33e6441b8c4a8f7c13b45b1d3c9f5954e0",
        ],
        "data": "0x000000000000000000000000000000000000000000000000000000000000000064",
        "address": "0x6b175474e89094c44da98b954eedeac495271d0f",
    }

    # Parse the transfer event
    transfer_event = parser.parse_transfer_event(example_log)

    if transfer_event:
        print("ERC-20 Transfer Event Detected:")
        print(f"- From: {transfer_event['from']}")
        print(f"- To: {transfer_event['to']}")
        print(f"- Value: {transfer_event['value']}")
        print(f"- Token: {transfer_event['token_address']}")
    else:
        print("No transfer event detected")


def example_database_queries():
    """Example 4: Database query examples."""
    print("\n=== Example 4: Database Query Examples ===")

    # These queries would be run against the actual database
    queries = {
        "total_transactions": """
            SELECT COUNT(*) as total 
            FROM enhanced_transactions 
            WHERE from_address = ? OR to_address = ?
        """,
        "revenue_transactions": """
            SELECT COUNT(*) as count, SUM(usd_value) as total_value
            FROM enhanced_transactions 
            WHERE category = 'Revenue' AND (from_address = ? OR to_address = ?)
        """,
        "gas_costs_by_chain": """
            SELECT chain_name, SUM(gas_cost_eth) as total_gas
            FROM enhanced_transactions 
            WHERE from_address = ? OR to_address = ?
            GROUP BY chain_name
        """,
        "token_summary": """
            SELECT token_symbol, COUNT(*) as count, SUM(CAST(token_amount AS REAL)) as total
            FROM enhanced_transactions 
            WHERE (from_address = ? OR to_address = ?) AND token_symbol IS NOT NULL
            GROUP BY token_symbol
        """,
    }

    print("Example database queries:")
    for name, query in queries.items():
        print(f"\n{name}:")
        print(query.strip())


def example_report_generation():
    """Example 5: Report generation."""
    print("\n=== Example 5: Report Generation ===")

    # Example report structure
    report_structure = {
        "generated_at": "2024-01-15T10:30:00",
        "addresses_analyzed": ["0x90a48d5cf7343b08da12e067680b4c6dbfe551be"],
        "total_transactions": 150,
        "summary_by_address": {
            "0x90a48d5cf7343b08da12e067680b4c6dbfe551be": {
                "total_transactions": 150,
                "total_revenue": 5000.0,
                "total_expenses": 1200.0,
                "total_gas_costs": 0.045,
                "categories": {
                    "Revenue": 45,
                    "Expense": 30,
                    "Token Transfer": 50,
                    "Contract": 25,
                },
                "token_summary": {
                    "ETH": {"count": 80, "total_amount": 2.5},
                    "USDC": {"count": 40, "total_amount": 50000},
                    "FOX": {"count": 30, "total_amount": 10000},
                },
            }
        },
        "chain_summary": {"Ethereum": 100, "Polygon": 50},
        "category_summary": {
            "Revenue": 45,
            "Expense": 30,
            "Token Transfer": 50,
            "Contract": 25,
        },
    }

    print("Report structure includes:")
    print(f"- {len(report_structure['addresses_analyzed'])} addresses analyzed")
    print(f"- {report_structure['total_transactions']} total transactions")
    print(f"- {len(report_structure['chain_summary'])} chains")
    print(f"- {len(report_structure['category_summary'])} categories")

    # Save example report
    os.makedirs("reports", exist_ok=True)
    with open("reports/example_report.json", "w") as f:
        json.dump(report_structure, f, indent=2)

    print("Example report saved to reports/example_report.json")


async def main():
    """Run all examples."""
    print("OnchainDen Clone - Example Usage")
    print("=" * 50)

    # Run examples
    await example_basic_analysis()
    example_custom_categorization()
    example_erc20_parsing()
    example_database_queries()
    example_report_generation()

    print("\n" + "=" * 50)
    print("Examples completed!")
    print("\nTo run actual analysis:")
    print("1. Edit config files with your API keys")
    print("2. Use the CLI: python onchainden_cli.py --analyze config/your_config.json")
    print("3. Or import and use the classes in your own scripts")


if __name__ == "__main__":
    asyncio.run(main())
