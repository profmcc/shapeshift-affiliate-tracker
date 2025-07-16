# ShapeShift FOX LP Listener

This directory contains the liquidity pool tracking system for ShapeShift's FOX token liquidity events. It monitors Uniswap V3 liquidity events for FOX token pairs across multiple chains.

## Files

- `run_lp_listener_week.py` - Main script to fetch and store LP events
- `abis/` - Directory containing contract ABIs for event parsing

## Supported Protocols

### Uniswap V3 Pool
- **Contract**: Various pool addresses for FOX token pairs
- **Events**: 
  - `Swap(address indexed sender, address indexed recipient, int256 amount0, int256 amount1, uint160 sqrtPriceX96, uint128 liquidity, int24 tick)`
  - `Mint(address indexed owner, address indexed tickLower, address indexed tickUpper, uint128 amount, uint256 amount0, uint256 amount1)`
  - `Burn(address indexed owner, address indexed tickLower, address indexed tickUpper, uint128 amount, uint256 amount0, uint256 amount1)`
- **Chains**: Ethereum Mainnet, Polygon, Arbitrum, BSC

## Database Schema

The system stores LP events in SQLite with the following schema:

```sql
CREATE TABLE lp_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chain_id INTEGER NOT NULL,
    block_number INTEGER NOT NULL,
    transaction_hash TEXT NOT NULL,
    log_index INTEGER NOT NULL,
    contract_address TEXT NOT NULL,
    event_type TEXT NOT NULL,
    sender TEXT,
    recipient TEXT,
    owner TEXT,
    amount0 TEXT,
    amount1 TEXT,
    sqrtPriceX96 TEXT,
    liquidity TEXT,
    tick INTEGER,
    tickLower INTEGER,
    tickUpper INTEGER,
    amount TEXT,
    timestamp INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Supported FOX Pairs

The listener tracks FOX token pairs including:
- FOX/WETH
- FOX/USDC
- FOX/USDT
- Other major FOX trading pairs

## Usage

1. **Run the LP listener**:
   ```bash
   python run_lp_listener_week.py
   ```

2. **Analyze LP data**:
   ```bash
   # Query the database for specific events
   sqlite3 lp_events.db "SELECT * FROM lp_events WHERE event_type = 'Swap' LIMIT 10;"
   ```

## Configuration

The script supports multiple RPC endpoints and can be configured for different time ranges. Default settings fetch the last week of events across all supported chains.

## Dependencies

- `web3` - Ethereum interaction
- `sqlite3` - Database storage
- `requests` - HTTP requests
- `json` - JSON parsing

## Event Types

### Swap Events
Track actual token swaps in FOX pools, including:
- Swap direction (FOX in/out)
- Swap amounts
- Price impact
- Liquidity changes

### Mint Events
Track new liquidity provision:
- Liquidity provider address
- Position range (tickLower/tickUpper)
- Liquidity amount added

### Burn Events
Track liquidity removal:
- Liquidity provider address
- Position range
- Liquidity amount removed

## Notes

- Events are fetched in chunks to avoid RPC rate limits
- Database includes deduplication to prevent duplicate entries
- All amounts are stored as strings to preserve precision
- Focuses specifically on FOX token liquidity events
- Can be extended to track other ShapeShift token pairs 