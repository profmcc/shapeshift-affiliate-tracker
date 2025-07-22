# ViewBlock THORChain Affiliate Fee Scraper

This scraper extracts comprehensive THORChain affiliate fee data from [ViewBlock](https://viewblock.io/thorchain/txs?affiliate=ss) and stores it in a SQLite database. It specifically captures the full data from hover tooltips that show abbreviated information in the display.

## Features

- **Hover Tooltip Extraction**: Captures full transaction hashes, addresses, and amounts from hover tooltips
- **Comprehensive Data Storage**: Stores all transaction details including amounts, assets, fees, and timestamps
- **Robust Error Handling**: Handles network issues, timeouts, and parsing errors gracefully
- **Database Integration**: SQLite database with proper indexing for efficient queries
- **Logging**: Detailed logging to track scraping progress and debug issues

## Prerequisites

### System Requirements
- Python 3.8+
- Chrome browser installed
- ChromeDriver (will be auto-detected if installed via package manager)

### Dependencies
Install the required Python packages:

```bash
pip install -r requirements_viewblock_scraper.txt
```

### ChromeDriver Setup

**macOS:**
```bash
brew install chromedriver
```

**Ubuntu/Debian:**
```bash
sudo apt-get install chromium-chromedriver
```

**Manual Installation:**
1. Download ChromeDriver from https://chromedriver.chromium.org/
2. Extract and place in your PATH or project directory

## Usage

### Quick Start

Run the scraper with default settings (20 pages):

```bash
python run_viewblock_scraper.py
```

### Advanced Usage

Run the scraper directly with custom parameters:

```bash
python viewblock_thorchain_scraper.py --pages 50
```

### Configuration

Edit `run_viewblock_scraper.py` to modify:
- `max_pages`: Number of pages to scrape (default: 20)
- Database path and logging settings

## Database Schema

The scraper creates a SQLite database (`viewblock_thorchain_fees.db`) with the following schema:

```sql
CREATE TABLE viewblock_thorchain_fees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tx_hash TEXT UNIQUE,
    block_height INTEGER,
    timestamp TEXT,
    from_address TEXT,
    to_address TEXT,
    affiliate_address TEXT,
    from_asset TEXT,
    to_asset TEXT,
    from_amount REAL,
    to_amount REAL,
    from_amount_usd REAL,
    to_amount_usd REAL,
    affiliate_fee_amount REAL,
    affiliate_fee_basis_points INTEGER,
    swap_slip REAL,
    liquidity_fee REAL,
    gas_fee REAL,
    gas_asset TEXT,
    status TEXT,
    memo TEXT,
    raw_data TEXT,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Data Extraction

The scraper extracts the following data from ViewBlock:

### Primary Fields (from table columns)
- **Transaction Hash**: Full hash from hover tooltip
- **Block Height**: Full block number from hover tooltip
- **Timestamp**: Full timestamp from hover tooltip
- **From Address**: Full address from hover tooltip
- **To Address**: Full address from hover tooltip
- **Amount**: Full amount with asset information

### Parsed Fields (from amount column)
- **From Asset**: Extracted from amount field (e.g., "BTC", "ETH")
- **To Asset**: Extracted from amount field
- **From Amount**: Numeric amount before conversion
- **To Amount**: Numeric amount after conversion

### Additional Fields
- **Affiliate Address**: Set to "ss" for ShapeShift affiliate transactions
- **Raw Data**: JSON string with original row data for debugging

## Example Queries

### Get all transactions
```sql
SELECT * FROM viewblock_thorchain_fees ORDER BY timestamp DESC LIMIT 10;
```

### Get transaction statistics
```sql
SELECT 
    COUNT(*) as total_transactions,
    COUNT(DISTINCT from_address) as unique_addresses,
    COUNT(DISTINCT from_asset) as unique_assets,
    MIN(timestamp) as earliest_tx,
    MAX(timestamp) as latest_tx
FROM viewblock_thorchain_fees;
```

### Get transactions by asset
```sql
SELECT 
    from_asset,
    COUNT(*) as transaction_count,
    SUM(from_amount) as total_volume
FROM viewblock_thorchain_fees 
WHERE from_asset IS NOT NULL
GROUP BY from_asset 
ORDER BY total_volume DESC;
```

## Logging

The scraper provides detailed logging:

- **Console Output**: Real-time progress and status
- **Log File**: `viewblock_scraper.log` with detailed information
- **Database Statistics**: Summary of scraped data

## Error Handling

The scraper handles various error conditions:

- **Network Timeouts**: Retries with exponential backoff
- **Missing Elements**: Graceful degradation with fallback data
- **Parsing Errors**: Continues processing other rows
- **Database Errors**: Logs errors and continues

## Performance Considerations

- **Rate Limiting**: 2-second delay between pages to be respectful
- **Memory Usage**: Processes one page at a time to minimize memory usage
- **Database Efficiency**: Uses indexes for fast queries
- **Headless Mode**: Runs Chrome in headless mode for better performance

## Troubleshooting

### Common Issues

1. **ChromeDriver not found**
   ```
   Error: Chrome driver issue: Message: unknown error: cannot find Chrome binary
   ```
   **Solution**: Install Chrome browser and ChromeDriver

2. **Page timeout**
   ```
   Error: Timeout waiting for page 1 to load
   ```
   **Solution**: Check internet connection and try again

3. **No transactions found**
   ```
   No transactions found on page 1. Stopping.
   ```
   **Solution**: The page might be empty or the site structure changed

### Debug Mode

Enable debug logging by modifying the logging level in `viewblock_thorchain_scraper.py`:

```python
logging.basicConfig(level=logging.DEBUG, ...)
```

## Integration with Existing Project

This scraper complements the existing THORChain listener:

- **ViewBlock Scraper**: Captures UI data with hover tooltips
- **THORChain Listener**: Captures API data from Midgard
- **Combined Analysis**: Use both datasets for comprehensive analysis

## License

This project is part of the ShapeShift affiliate tracker and follows the same licensing terms.

## Contributing

When contributing to this scraper:

1. Test with a small number of pages first
2. Verify database schema changes
3. Update documentation for new features
4. Follow the existing code style and error handling patterns 