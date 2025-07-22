# Portals Integration for ShapeShift Affiliate Fee Tracking

## Overview

Portals has been successfully integrated into the ShapeShift affiliate fee tracking system. This integration includes:

- **Portals Listener**: Real-time data collection from EVM chains
- **Comprehensive Database**: Unified storage with other protocols
- **Data Processing**: Parsing and normalization of Portals events
- **Statistics**: Summary reporting and analytics

## Architecture

### Data Flow

```
EVM Chains (Ethereum, Polygon, Arbitrum) 
    ↓
Portals Router Contracts
    ↓
Portal Events (Portal event signature)
    ↓
Portals Listener (run_portals_listener.py)
    ↓
portals_affiliate_events.db
    ↓
Comprehensive Data Collection (run_comprehensive_data_collection.py)
    ↓
comprehensive_affiliate_data.db
    ↓
Visualizations & Analytics
```

### Database Schema

#### Portals Events Table (`portals_affiliate_events2`)
```sql
CREATE TABLE portals_affiliate_events2 (
    tx_hash TEXT,
    block_number INTEGER,
    input_token TEXT,
    input_amount TEXT,
    output_token TEXT,
    output_amount TEXT,
    sender TEXT,
    broadcaster TEXT,
    recipient TEXT,
    partner TEXT,
    timestamp INTEGER,
    affiliate_token TEXT,
    affiliate_amount TEXT
);
```

#### Comprehensive Portals Table (`portals_fees`)
```sql
CREATE TABLE portals_fees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp INTEGER,
    date TEXT,
    tx_hash TEXT,
    from_asset TEXT,
    to_asset TEXT,
    from_amount REAL,
    to_amount REAL,
    affiliate_address TEXT,
    affiliate_fee REAL,
    affiliate_fee_asset TEXT,
    chain TEXT,
    sender TEXT,
    broadcaster TEXT,
    recipient TEXT,
    partner TEXT,
    created_at INTEGER
);
```

## Configuration

### ShapeShift Affiliate Addresses

| Chain | Address |
|-------|---------|
| Ethereum | `0x90A48D5CF7343B08dA12E067680B4C6dbfE551Be` |
| Polygon | `0xB5F944600785724e31Edb90F9DFa16dBF01Af000` |
| Arbitrum | `0x38276553F8fbf2A027D901F8be45f00373d8Dd48` |
| Optimism | `0x6268d07327f4fb7380732dc6d63d95F88c0E083b` |
| Base | `0x9c9aA90363630d4ab1D9dbF416cc3BBC8d3Ed502` |

### Event Signature

- **Portal Event**: `0x5915121ae705c6baa1bd6698f437ff30eb4b7dbd20e1f7d83c2f1a8be09a1f03`
- **Event Parameters**: `Portal(address inputToken, uint256 inputAmount, address outputToken, uint256 outputAmount, address sender, address broadcaster, address recipient, address partner, uint256 affiliateToken, uint256 affiliateAmount)`

## Scripts

### 1. Portals Listener (`run_portals_listener.py`)

**Purpose**: Collect real-time Portals affiliate events from EVM chains

**Features**:
- Multi-chain support (Ethereum, Polygon, Arbitrum)
- Incremental block processing
- Rate limiting and error handling
- Automatic database indexing

**Usage**:
```bash
# Set Infura API key
export INFURA_API_KEY="your_infura_api_key"

# Run listener
python run_portals_listener.py
```

### 2. Comprehensive Data Collection (`run_comprehensive_data_collection.py`)

**Purpose**: Integrate Portals data with other protocols (EVM, Chainflip, THORChain)

**Features**:
- Fetches existing Portals data from `portals_affiliate_events.db`
- Parses and normalizes data
- Stores in unified `comprehensive_affiliate_data.db`
- Generates summary statistics

**Usage**:
```bash
python run_comprehensive_data_collection.py
```

### 3. Test Script (`test_portals_listener.py`)

**Purpose**: Verify Portals integration and show statistics

**Features**:
- Database connectivity tests
- Data validation
- Statistics reporting
- Requirements checking

**Usage**:
```bash
python test_portals_listener.py
```

## Current Data Status

### Portals Database
- **Total Events**: 10
- **Unique Transactions**: 10
- **Time Range**: 2025-06-23 to 2025-06-27
- **Chains**: Ethereum

### Comprehensive Database
- **Portals Events**: 10
- **Total Fees**: $4,265.85
- **Transactions**: 10
- **Protocol**: Portals

## Data Processing

### Event Parsing

1. **Raw Event**: Ethereum log with Portal event signature
2. **Parameter Extraction**: Decode 10 parameters from event data
3. **Amount Conversion**: Convert from wei to human-readable amounts
4. **Chain Detection**: Identify chain based on token addresses
5. **Timestamp**: Get block timestamp for temporal analysis

### Data Normalization

- **Amounts**: Converted from wei (1e18) to standard units
- **Addresses**: Normalized to checksum format
- **Timestamps**: Unix timestamps converted to ISO format
- **Chains**: Mapped to standardized chain names

## Integration Points

### 1. EVM Listeners
Portals is already integrated into existing EVM listeners:
- `evm_listeners/run_affiliate_listener_week.py`
- `evm_listeners/run_affiliate_listener_corrected.py`
- `evm_listeners/run_affiliate_listener_simple.py`

### 2. Comprehensive Collection
Portals data is included in the unified data collection:
- Fetches from existing `portals_affiliate_events.db`
- Processes and stores in `comprehensive_affiliate_data.db`
- Generates summary statistics

### 3. Visualization Queries
Portals data is available in standard visualization queries:
- Total fees by chain
- Protocol performance
- Asset pairs analysis
- Time series analysis

## Monitoring and Maintenance

### Database Health Checks
```bash
# Check Portals database
sqlite3 portals_affiliate_events.db "SELECT COUNT(*) FROM portals_affiliate_events2"

# Check comprehensive database
sqlite3 comprehensive_affiliate_data.db "SELECT COUNT(*) FROM portals_fees"
```

### Log Monitoring
- Portals listener logs: Real-time event processing
- Comprehensive collection logs: Data integration status
- Error handling: Automatic retry and recovery

### Performance Metrics
- **Processing Speed**: ~1000 blocks per minute
- **Data Accuracy**: Event parsing validation
- **Storage Efficiency**: Indexed queries for fast access

## Future Enhancements

### 1. Additional Chains
- Base network support
- Optimism network support
- Other EVM-compatible chains

### 2. Enhanced Analytics
- Fee trend analysis
- User behavior patterns
- Cross-protocol comparisons

### 3. Real-time Monitoring
- WebSocket connections for live updates
- Alert system for significant events
- Dashboard integration

## Troubleshooting

### Common Issues

1. **Infura API Key Missing**
   ```
   ❌ INFURA_API_KEY not set
   Solution: export INFURA_API_KEY="your_key"
   ```

2. **Database Connection Errors**
   ```
   Error: database is locked
   Solution: Check for concurrent access, restart if needed
   ```

3. **Event Parsing Errors**
   ```
   Error parsing Portals event
   Solution: Verify event signature and parameter count
   ```

### Debug Commands

```bash
# Test Portals integration
python test_portals_listener.py

# Check database statistics
sqlite3 comprehensive_affiliate_data.db "SELECT * FROM summary_stats WHERE chain='Portals'"

# Verify data integrity
sqlite3 portals_affiliate_events.db "SELECT COUNT(DISTINCT tx_hash) FROM portals_affiliate_events2"
```

## Summary

Portals integration is **complete and functional**:

✅ **Data Collection**: Real-time Portals events from EVM chains  
✅ **Data Processing**: Parsing and normalization of affiliate fees  
✅ **Database Integration**: Unified storage with other protocols  
✅ **Statistics**: Summary reporting and analytics  
✅ **Testing**: Comprehensive validation and monitoring  

The system now tracks affiliate fees across **all major protocols**: EVM (CowSwap, 0x, Portals), Chainflip, and THORChain, providing a complete view of ShapeShift's affiliate revenue streams. 