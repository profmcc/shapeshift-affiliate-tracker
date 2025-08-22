ShapeShift Affiliate Listener

A comprehensive system for monitoring and tracking ShapeShift affiliate fee events across multiple blockchain protocols and chains.

Overview

The ShapeShift Affiliate Listener indexes blockchain transactions in real-time to capture affiliate fee events from various DEX protocols including CoW Swap, THORChain, ButterSwap, Portals, Relay, and Chainflip. It provides a unified data structure for cross-protocol analysis, reporting, and DAO revenue tracking.

Quick Start

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys

# Run a specific listener
python -m shapeshift_listener run --protocol butterswap --chain base

# List supported chains
python -m shapeshift_listener list-chains

# Check configuration
python -m shapeshift_listener config

How It Works

Transaction Indexing Strategy

The system uses block-by-block scanning with the following approach:
	•	Sequential Block Processing: Each listener processes blocks sequentially starting from a specified block number
	•	Event Filtering: Scans transaction logs for specific events (e.g., Trade events from CoW Swap, Swap events from THORChain)
	•	Address-Based Detection: Filters transactions by checking if ShapeShift affiliate addresses are involved
	•	Rate Limiting: Configurable RPC rate limiting (default: 10 requests/second) to avoid hitting API limits
	•	Reorg Safety: Waits for confirmation blocks before processing to handle blockchain reorganizations
	•	Cross-Chain Parsing: Integrates native APIs (e.g., THORChain Midgard, Chainflip indexers) for non-EVM detection

RPC Endpoints and APIs

Primary RPC Providers:
	•	Alchemy (preferred) - https://{chain}-mainnet.g.alchemy.com/v2/{API_KEY}
	•	Infura (fallback) - https://{chain}-mainnet.infura.io/v3/{API_KEY}

Supported Chains:
	•	Base, Ethereum, Polygon, Optimism, Arbitrum, Avalanche, BSC, Gnosis Chain

External APIs:
	•	THORChain Midgard API for cross-chain swap data
	•	Chainflip Indexer for native cross-chain affiliate data
	•	Token price APIs for USD value calculations

Filtering Implementation

Per Address Filtering:
	•	Hardcoded affiliate addresses per chain in centralized config
	•	Protocol-specific overrides for special cases (ButterSwap, Chainflip)
	•	Memo and text detection for THORChain affiliates

Per Chain Filtering:
	•	Chain-specific RPC URLs configured in .env
	•	Chain-specific block ranges and starting blocks
	•	Gas handling optimizations for L1 vs L2 chains

Data Structure

Complete Unified Event Structure

All protocols output data in a standardized format for cross-protocol analysis:

{
    "protocol": "butterswap",           # Protocol name
    "chain": "base",                    # Chain identifier
    "block_number": 15000000,           # Block number
    "tx_hash": "0x...",                # Transaction hash
    "block_timestamp": 1640995200,      # Unix timestamp
    "block_date": "2024-01-01",        # Human readable date
    
    # Address Tracking
    "from_address": "0x...",
    "to_address": "0x...",
    "user_address": "0x...",
    "affiliate_address": "0x...",
    
    # Fee Information
    "expected_fee_bps": 55,
    "actual_fee_bps": 55,
    "affiliate_fee_amount": "0.133",
    "affiliate_fee_token": "WETH",
    "affiliate_fee_usd": 454.00,
    
    # Trade Details
    "input_token": "UNI-V2",
    "input_amount": "3000.0",
    "input_amount_usd": 69948.00,
    "output_token": "USDC",
    "output_amount": "56980.0",
    "output_amount_usd": 56980.00,
    "volume_usd": 69948.00,
    
    # Gas & Performance
    "gas_used": 150000,
    "gas_price": 20000000000,
    "gas_cost_usd": 12.50,
    
    # Metadata
    "swap_path": "UNI-V2>USDC",
    "is_streaming_swap": False,
    "liquidity_fee": 0.005,
    "swap_slip": 0.02,
    
    # Reorg & Confirmation Safety
    "reorg_depth": 0,
    "confirmations": 15,
    "is_final": True,
    "reorg_window_blocks": 25,
    
    # Protocol-Specific Identifiers
    "order_uid": "",
    "app_code": "butterswap",
    "app_data": "",
    
    # Error Handling
    "error_code": None,
    "error_message": None,
    "status": "success",
    
    # Timestamps
    "created_at": "2024-01-01 00:00:00",
    "created_date": "2024-01-01"
}

Data Persistence Strategy
	•	CSV Exports: Protocol-specific and consolidated files
	•	SQLite Database: Unified structured storage with indexing
	•	Stdout Streaming: For real-time monitoring and logs
	•	JSON Export: For API/webhook integrations

Affiliate Address Configuration

Centralized config (shapeshift_config.yaml) with:
	•	Chain-specific Safe addresses
	•	Protocol-specific affiliate addresses (ButterSwap, THORChain, Chainflip)
	•	Legacy/alternative address support
	•	Pattern matching for variations

See detailed mapping tables in the configuration section of this README.

Testing
	•	Pytest for unit and integration tests
	•	Mock RPC & API calls for deterministic runs
	•	Coverage reports with pytest --cov
	•	Regression tests using saved sample transaction data

Architecture

shapeshift_listener/
├── __main__.py
├── cli.py
├── core/
│   ├── base.py
│   ├── config.py
│   └── listener_manager.py
└── listeners/
    ├── butterswap.py
    ├── cowswap.py
    ├── portals.py
    ├── relay.py
    ├── thorchain.py
    └── chainflip.py

Design Patterns
	•	Strategy Pattern for listener implementations
	•	Factory Pattern for listener creation
	•	Observer Pattern for event handling
	•	Template Method for shared listener logic

Supported Protocols
	•	ButterSwap (Base)
	•	CoW Swap (EVM)
	•	Portals (Cross-chain bridge)
	•	Relay (DEX aggregator)
	•	THORChain (native cross-chain)
	•	Chainflip (cross-chain swaps)

Performance Considerations
	•	Batch processing for throughput
	•	Async RPC calls
	•	Caching for token metadata and prices
	•	Configurable rate limiting with exponential backoff

Development

# Clone repository
git clone https://github.com/profmcc/shapeshift-listener.git
cd shapeshift-listener

# Create venv
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -e .

# Install pre-commit
pre-commit install

	•	Black for formatting
	•	isort for imports
	•	flake8 for linting
	•	mypy for type checks

Status

Current Implementation
	•	✅ Core framework implemented
	•	✅ All major protocol listeners live
	•	✅ Centralized affiliate config complete
	•	✅ Data persistence with CSV + SQLite
	•	✅ Testing framework running

Roadmap
	•	🔄 Add more DEX and bridge protocols
	•	🔄 Real-time dashboard web UI
	•	🔄 REST API endpoints
	•	🔄 Notification/alerting system
	•	🔄 Performance optimization (batch + caching)

Contributing

See CONTRIBUTING.md

License

MIT License - see LICENSE

Security

See SECURITY.md for vulnerability reporting.