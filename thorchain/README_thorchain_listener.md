# THORChain Affiliate Fee Listener

This module provides THORChain affiliate fee tracking for ShapeShift's affiliate program. It fetches swap actions from the THORChain Midgard API and tracks affiliate fees paid to ShapeShift.

## Features

- **Real-time tracking** of THORChain swap actions
- **Affiliate fee detection** for ShapeShift's THORChain address
- **Database storage** of all affiliate fee transactions
- **Comprehensive logging** and error handling
- **Rate limiting** to respect API limits

## Configuration

### Environment Variables

```bash
# THORChain Midgard API URL
export THORCHAIN_MIDGARD_URL=https://midgard.ninerealms.com

# ShapeShift affiliate address on THORChain
export THORCHAIN_AFFILIATE_ADDRESS=thor1z8s0yk6q86nqwsc2gagv4n9yt9c0hk9qtszt0p
```

### Configuration Files

- `thorchain_config.py` - Main configuration settings
- `run_thorchain_listener.py` - Main listener script

## Usage

### Running the Listener

```bash
# Install dependencies
pip install -r requirements_thorchain.txt

# Run the THORChain listener
python run_thorchain_listener.py
```

### Querying Affiliate Fees

```bash
# Query and display affiliate fee summary
python run_thorchain_listener.py query
```

## Database Schema

The listener creates a SQLite database (`shapeshift_thorchain_fees.db`) with the following schema:

```sql
CREATE TABLE thorchain_affiliate_fees (
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
    pool TEXT,
    status TEXT,
    created_at INTEGER
);
```

## API Integration

### Midgard API Endpoints Used

- `GET /v2/actions` - Fetch THORChain actions
- Parameters: `limit`, `offset`

### Data Processing

1. **Action Filtering**: Only processes `swap` type actions
2. **Affiliate Detection**: Checks if ShapeShift is the affiliate
3. **Fee Extraction**: Extracts affiliate fee amounts and assets
4. **Data Normalization**: Converts amounts from base units to standard units

## Supported Assets

The listener tracks affiliate fees for major THORChain assets:

- THOR.RUNE (native RUNE)
- ETH.ETH (Ethereum)
- BTC.BTC (Bitcoin)
- BNB.BNB (Binance Coin)
- BSC.BUSD (Binance USD)
- BSC.USDT (Tether on BSC)
- ETH.USDC (USD Coin on Ethereum)
- ETH.USDT (Tether on Ethereum)
- AVAX.AVAX (Avalanche)
- POLYGON.MATIC (Polygon)

## Error Handling

- **API Rate Limiting**: Automatic delays between requests
- **Network Errors**: Retry logic with exponential backoff
- **Data Parsing**: Graceful handling of malformed responses
- **Database Errors**: Transaction rollback on failures

## Monitoring

### Log Files

- `thorchain_listener.log` - Main application logs
- Database file: `shapeshift_thorchain_fees.db`

### Key Metrics

- Total actions processed
- Affiliate fees found
- Processing rate (actions/second)
- Error rates and types

## Integration with Existing System

This THORChain listener follows the same patterns as other chain listeners in the project:

- Similar database schema structure
- Consistent logging format
- Same configuration management approach
- Compatible with existing affiliate tracking workflows

## Development

### Testing

```bash
# Test the listener with a small batch
python run_thorchain_listener.py --test

# Query recent fees
python run_thorchain_listener.py query
```

### Adding New Features

1. Update `thorchain_config.py` for new settings
2. Modify `run_thorchain_listener.py` for new functionality
3. Update database schema if needed
4. Add tests and documentation

## Troubleshooting

### Common Issues

1. **API Rate Limiting**: Increase `rate_limit_delay` in config
2. **Database Locked**: Check for concurrent access
3. **Network Timeouts**: Increase `timeout` in config
4. **Memory Issues**: Reduce `batch_size` in config

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python run_thorchain_listener.py
``` 