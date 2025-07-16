# ShapeShift Affiliate Fee Listener

This directory contains the affiliate fee tracking system for ShapeShift's affiliate program. It monitors affiliate fee payments across multiple DEX protocols including CowSwap, 0x Protocol, and Portals.

## Files

- `run_affiliate_listener_corrected.py` - Main script to fetch and store affiliate fee events
- `verify_affiliate_tracking.py` - Verification script to check tracking against CRM data
- `verify_affiliate_tracking_simple.py` - Simplified verification script
- `README_affiliate_fees.md` - Detailed documentation of affiliate fee tracking
- `abis/` - Directory containing contract ABIs for event parsing

## Supported Protocols

### CowSwap (GPv2Settlement)
- **Contract**: `0x9008D19f58AAbD9eD0D60971565AA8510560ab41`
- **Event**: `Trade(bytes orderUid, address sellToken, address buyToken, uint256 sellAmount, uint256 buyAmount, uint256 feeAmount, address owner, bytes orderUid)`
- **Chains**: Ethereum Mainnet

### 0x Protocol (TransformERC20)
- **Contract**: `0x4f3a120E72B76cF7C4B5B7C4B5B7C4B5B7C4B5B7C`
- **Event**: `TransformERC20(address inputToken, address outputToken, uint256 inputTokenAmount, uint256 outputTokenAmount, address taker, bytes signature)`
- **Chains**: Ethereum Mainnet, Polygon, BSC, Arbitrum

### Portals Router
- **Contract**: `0x0000000000000000000000000000000000000000` (placeholder)
- **Event**: `AffiliateFeePaid(address affiliate, uint256 amount, address token)`
- **Chains**: Ethereum Mainnet

## Database Schema

The system stores affiliate fee events in SQLite with the following schema:

```sql
CREATE TABLE affiliate_fee_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chain_id INTEGER NOT NULL,
    block_number INTEGER NOT NULL,
    transaction_hash TEXT NOT NULL,
    log_index INTEGER NOT NULL,
    contract_address TEXT NOT NULL,
    protocol TEXT NOT NULL,
    affiliate_address TEXT,
    fee_amount TEXT,
    fee_token TEXT,
    order_uid TEXT,
    sell_token TEXT,
    buy_token TEXT,
    sell_amount TEXT,
    buy_amount TEXT,
    owner_address TEXT,
    timestamp INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Usage

1. **Run the listener**:
   ```bash
   python run_affiliate_listener_corrected.py
   ```

2. **Verify tracking**:
   ```bash
   python verify_affiliate_tracking.py
   ```

3. **Check against CRM data**:
   ```bash
   python verify_affiliate_tracking_simple.py
   ```

## Configuration

The scripts support multiple RPC endpoints and can be configured for different time ranges. Default settings fetch the last week of events across all supported chains.

## Dependencies

- `web3` - Ethereum interaction
- `sqlite3` - Database storage
- `requests` - HTTP requests
- `json` - JSON parsing

## Notes

- Events are fetched in chunks to avoid RPC rate limits
- Database includes deduplication to prevent duplicate entries
- Verification scripts compare against ShapeShift's CRM data
- All affiliate fee amounts are stored as strings to preserve precision 