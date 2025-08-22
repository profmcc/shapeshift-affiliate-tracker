# ShapeShift Affiliate Listener

A comprehensive system for monitoring and tracking ShapeShift affiliate fee events across multiple blockchain protocols and chains.

## Overview

The ShapeShift Affiliate Listener indexes blockchain transactions in real-time to capture affiliate fee events from various DEX protocols including CoW Swap, THORChain, ButterSwap, Portals, and Relay. It provides a unified data structure for cross-protocol analysis and revenue tracking.

## How It Works

### Transaction Indexing Strategy

The system uses **block-by-block scanning** with the following approach:

- **Sequential Block Processing**: Each listener processes blocks sequentially starting from a specified block number
- **Event Filtering**: Scans transaction logs for specific events (e.g., `Trade` events from CoW Swap, `Swap` events from THORChain)
- **Address-Based Detection**: Filters transactions by checking if ShapeShift affiliate addresses are involved
- **Rate Limiting**: Configurable RPC rate limiting (default: 10 requests/second) to avoid hitting API limits
- **Reorg Safety**: Waits for confirmation blocks before processing to handle blockchain reorganizations

### RPC Endpoints and APIs

**Primary RPC Providers:**
- **Alchemy** (preferred) - `https://{chain}-mainnet.g.alchemy.com/v2/{API_KEY}`
- **Infura** (fallback) - `https://{chain}-mainnet.infura.io/v3/{API_KEY}`

**Supported Chains:**
- Base, Ethereum, Polygon, Optimism, Arbitrum, Avalanche, BSC

**External APIs:**
- **THORChain Midgard API** for cross-chain swap data
- **Token price APIs** for USD value calculations

### Filtering Implementation

**Per Address Filtering:**
```python
# Hardcoded affiliate addresses per chain
affiliate_addresses = {
    "base": "0x35339070f178dC4119732982C23F5a8d88D3f8a3",
    "ethereum": "0x90A48D5CF7343B08dA12E067680B4C6dbfE551Be",
    "polygon": "0xB5F944600785724e31Edb90F9DFa16dBF01Af000",
    "optimism": "0x6268d07327f4fb7380732dc6d63d95F88c0E083b",
    "arbitrum": "0x38276553F8fbf2A027D901F8be45f00373d8Dd48",
    "avalanche": "0x74d63F31C2335b5b3BA7ad2812357672b2624cEd",
    "bsc": "0x8b92b1698b57bEDF2142297e9397875ADBb2297E",
}
```

**Per Chain Filtering:**
- **Chain-specific RPC URLs** configured in environment variables
- **Protocol-specific listeners** (ButterSwap, CoW Swap, THORChain, etc.)
- **Chain-specific block ranges** and scanning parameters
- **Chain-specific gas handling** for L1 vs L2 optimizations

## Data Structure

### Unified Event Structure

All protocols output data in a standardized format for cross-protocol analysis:

```python
{
    # Core Transaction Info
    "protocol": "butterswap",           # Protocol name
    "chain": "base",                    # Chain identifier
    "block_number": 15000000,           # Block number
    "tx_hash": "0x...",                # Transaction hash
    "block_timestamp": 1640995200,      # Unix timestamp
    "block_date": "2024-01-01",        # Human readable date
    
    # Address Tracking
    "from_address": "0x...",           # Transaction sender
    "to_address": "0x...",             # Transaction recipient
    "user_address": "0x...",           # End user making swap
    "affiliate_address": "0x...",       # ShapeShift affiliate address
    
    # Fee Information
    "expected_fee_bps": 55,            # Expected fee basis points
    "actual_fee_bps": 55,              # Actual fee basis points
    "affiliate_fee_amount": "0.133",    # Fee amount in token
    "affiliate_fee_token": "WETH",      # Token used for fee
    "affiliate_fee_usd": 454.00,       # Fee in USD
    
    # Trade Details
    "input_token": "UNI-V2",           # Input token
    "input_amount": "3000.0",          # Input amount
    "input_amount_usd": 69948.00,      # Input value in USD
    "output_token": "USDC",            # Output token
    "output_amount": "56980.0",        # Output amount
    "output_amount_usd": 56980.00,     # Output value in USD
    "volume_usd": 69948.00,            # Total trade volume in USD
    
    # Gas & Performance
    "gas_used": 150000,                # Gas consumed
    "gas_price": 20000000000,          # Gas price in wei
    "gas_cost_usd": 12.50,             # Gas cost in USD
    
    # Metadata
    "swap_path": "UNI-V2>USDC",        # Token swap path
    "is_streaming_swap": False,        # For THORChain
    "liquidity_fee": 0.005,            # Protocol liquidity fee
    "swap_slip": 0.02,                 # Price impact
    
    # Reorg & Confirmation Safety
    "reorg_depth": 0,                  # Number of orphaned blocks
    "confirmations": 15,                # Blocks since this block
    "is_final": True,                  # True if confirmations > reorg_window
    "reorg_window_blocks": 25,         # Configured reorg safety margin
    
    # Protocol-Specific Identifiers
    "order_uid": "",                   # For protocols using order IDs (CoW Swap)
    "app_code": "butterswap",          # Application identifier
    "app_data": "",                    # Additional protocol data
    
    # Error Handling
    "error_code": None,                # Error code if transaction failed
    "error_message": None,             # Human readable error description
    "status": "success",               # Transaction status
    
    # Timestamps
    "created_at": "2024-01-01 00:00:00",
    "created_date": "2024-01-01"
}
```

### CSV Column Descriptions

**Core Transaction Info:**
- `protocol`: Name of the DEX protocol (e.g., "butterswap", "cowswap", "thorchain")
- `chain`: Blockchain network (e.g., "base", "ethereum", "arbitrum")
- `block_number`: Block number where transaction occurred
- `tx_hash`: Unique transaction hash identifier
- `block_timestamp`: Unix timestamp of block creation
- `block_date`: Human-readable date in YYYY-MM-DD format

**Address Tracking:**
- `from_address`: Address that initiated the transaction
- `to_address`: Address that received the transaction
- `user_address`: End user making the swap (may differ from from_address in aggregators)
- `affiliate_address`: ShapeShift affiliate address receiving fees

**Fee Information:**
- `expected_fee_bps`: Expected fee in basis points (typically 55)
- `actual_fee_bps`: Actual fee charged in basis points
- `affiliate_fee_amount`: Fee amount in the token's native units
- `affiliate_fee_token`: Token symbol used for fee payment
- `affiliate_fee_usd`: Fee value converted to USD

**Trade Details:**
- `input_token`: Token being swapped from
- `input_amount`: Amount of input token
- `input_amount_usd`: USD value of input amount
- `output_token`: Token being swapped to
- `output_amount`: Amount of output token
- `output_amount_usd`: USD value of output amount
- `volume_usd`: Total trade volume in USD

**Gas & Performance:**
- `gas_used`: Amount of gas consumed by transaction
- `gas_price`: Gas price in wei
- `gas_cost_usd`: Total gas cost converted to USD

**Metadata:**
- `swap_path`: Token swap route (e.g., "UNI-V2>USDC")
- `is_streaming_swap`: Boolean for THORChain streaming swaps
- `liquidity_fee`: Protocol liquidity fee percentage
- `swap_slip`: Price impact percentage

**Reorg & Confirmation Safety:**
- `reorg_depth`: Number of orphaned blocks (0 = confirmed)
- `confirmations`: Blocks since this transaction
- `is_final`: True if transaction is beyond reorg window
- `reorg_window_blocks`: Configured safety margin for reorgs

**Protocol-Specific Identifiers:**
- `order_uid`: Unique order identifier (CoW Swap)
- `app_code`: Application identifier
- `app_data`: Additional protocol-specific data

**Error Handling:**
- `error_code`: Error code if transaction failed
- `error_message`: Human-readable error description
- `status`: Transaction status ("success", "failed", "pending")

**Timestamps:**
- `created_at`: Full timestamp when record was created
- `created_date`: Date when record was created

## Data Persistence Strategy

**Primary: CSV Files**
- **Protocol-specific files**: `cowswap_transactions.csv`, `thorchain_transactions.csv`, etc.
- **Consolidated file**: `consolidated_affiliate_transactions.csv` for cross-protocol analysis
- **Block tracking**: `block_trackers/` directory with progress CSV files

**Secondary Options:**
- **SQLite database**: `affiliate_fees.db` (configurable via `DATABASE_URL`)
- **Stdout streaming**: Real-time output for monitoring
- **JSON export**: For API consumption

**Block Tracking Files:**
```csv
chain,last_processed_block,last_processed_date,total_transactions_processed,last_error,last_error_date
ethereum,15000000,2024-01-01,1250,,,
polygon,25000000,2024-01-01,890,,,
```

## Testing and Validation

**Testing Infrastructure:**
- **Pytest framework** with coverage reporting
- **Mock environment variables** for testing
- **Test database**: `test_relay_processing.db` for integration testing
- **Coverage reports**: HTML coverage reports generated during testing

**Unique Artifacts:**
- **Block tracking CSVs**: Show scanning progress and prevent duplicate work
- **Timestamped data**: `created_at` and `created_date` fields in all records
- **Processing metadata**: Last processed block, error tracking, transaction counts
- **Idempotent operation**: Safe to re-run scripts (only processes new blocks)

**Example Test Run:**
```bash
# Run tests with coverage
pytest --cov=src --cov-report=html

# Run specific listener test
pytest tests/test_butterswap.py -v

# Run integration tests
pytest tests/ -m "integration"
```

## Installation

```bash
# Clone repository
git clone https://github.com/profmcc/shapeshift-affiliate-tracker.git
cd shapeshift-affiliate-tracker

# Install dependencies
pip install -e .

# Set up environment variables
cp env.example .env
# Edit .env with your API keys
```

## Configuration

**Environment Variables:**
```bash
# Required API Keys
ALCHEMY_API_KEY=your_alchemy_key_here
INFURA_API_KEY=your_infura_key_here

# Performance Tuning
RPC_RATE_LIMIT_PER_SECOND=10
BATCH_SIZE=100
MAX_RETRIES=3

# Data Storage
DATA_DIR=./data
CSV_OUTPUT_DIR=./data/csv

# Safety Settings
REORG_WINDOW_BLOCKS=25
CONFIRMATION_BLOCKS=12
```

## Usage

**Command Line Interface:**
```bash
# Run listener for specific chain
ss-listener run --chain base --from-block 32900000 --sink csv

# Run with debug logging
ss-listener run --chain arbitrum --from-block 22222222 --sink stdout --log-level DEBUG

# List available chains
ss-listener list-chains

# Validate configuration
ss-listener config --validate
```

**Python API:**
```python
from shapeshift_listener.core.config import Config
from shapeshift_listener.core.listener_manager import ListenerManager

# Load configuration
config = Config.from_env()

# Create listener manager
manager = ListenerManager(config)

# Run specific chain
await manager.run_chain("base", from_block=32900000, sink="csv")
```

## Supported Protocols

- **CoW Swap**: DEX aggregator with 55 bps affiliate fees
- **THORChain**: Cross-chain swaps with native asset support
- **ButterSwap**: Base-native DEX with affiliate integration
- **Portals**: Cross-chain bridge with affiliate rewards
- **Relay**: MEV protection with affiliate fee sharing

## Data Quality & Validation

**Required Fields:**
- ✅ **Always Present**: tx_hash, block_number, affiliate_fee_usd, volume_usd
- ✅ **Address Tracking**: from_address, to_address, affiliate_address
- ✅ **Fee Validation**: expected_fee_bps vs actual_fee_bps
- ✅ **Timestamp Data**: block_timestamp, created_at, created_date

**Validation Rules:**
- **Fee Accuracy**: Actual fees must match expected 55 bps
- **Address Format**: All addresses must be valid checksummed format
- **Block Consistency**: Block numbers must be sequential within chains
- **USD Conversion**: All USD values must be calculated from reliable price feeds

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

For issues and questions:
- Create an issue on GitHub
- Check the documentation in the `docs/` directory
- Review existing CSV data for examples