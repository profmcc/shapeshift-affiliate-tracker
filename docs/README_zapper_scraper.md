# Zapper Wallet Token Data Scraper

This tool extracts token data from Zapper's wallet tables, capturing token information, prices, balances, and values for portfolio analysis.

## Features

- ✅ **Comprehensive Data Extraction**: Captures Token, Price, Balance, and Value columns
- ✅ **Dynamic Loading Support**: Handles pagination and lazy-loaded content
- ✅ **Multiple Output Formats**: Saves data as CSV and JSON
- ✅ **Robust Error Handling**: Graceful handling of network issues and missing elements
- ✅ **Data Validation**: Ensures data completeness and quality
- ✅ **Real-time Logging**: Detailed progress and error reporting
- ✅ **Portfolio Analysis**: Calculates total value and shows top holdings

## Quick Start

### 1. Install Dependencies

The scraper uses your existing project dependencies. Ensure you have:

```bash
pip install -r requirements.txt
```

### 2. Run the Scraper

#### Basic Usage (Default SS DAO Bundle)
```bash
python run_zapper_scraper.py
```

#### Custom URL
```bash
python run_zapper_scraper.py --url "https://zapper.xyz/bundle/your-addresses..."
```

#### Visible Browser Mode (for debugging)
```bash
python run_zapper_scraper.py --visible
```

#### Custom Output Directory
```bash
python run_zapper_scraper.py --output-dir "my_portfolio_data"
```

## Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--url` | Zapper URL to scrape | SS DAO bundle URL |
| `--visible` | Run browser in visible mode | False (headless) |
| `--output-dir` | Output directory for files | `data/` |

## Output Files

The scraper generates timestamped files:

- **CSV**: `data/zapper_wallet_data_YYYYMMDD_HHMMSS.csv`
- **JSON**: `data/zapper_wallet_data_YYYYMMDD_HHMMSS.json`
- **Log**: `zapper_scraper.log`

## Example Output

```
============================================================
ZAPPER WALLET DATA SCRAPER
============================================================
2025-01-09 02:45:12 - INFO - Starting Zapper wallet data scraper
2025-01-09 02:45:13 - INFO - Navigating to: https://zapper.xyz/bundle/...
2025-01-09 02:45:15 - INFO - Page loaded successfully
2025-01-09 02:45:16 - INFO - Found table with selector: table
2025-01-09 02:45:16 - INFO - Found 25 rows in table
2025-01-09 02:45:16 - INFO - Successfully extracted 24 token entries
2025-01-09 02:45:16 - INFO - Data validation passed. Extracted 24 valid rows
2025-01-09 02:45:16 - INFO - Data saved to: data/zapper_wallet_data_20250109_024516.csv and data/zapper_wallet_data_20250109_024516.json
============================================================
SCRAPING COMPLETED SUCCESSFULLY!
============================================================
📁 CSV file: data/zapper_wallet_data_20250109_024516.csv
📁 JSON file: data/zapper_wallet_data_20250109_024516.json
📊 Total tokens extracted: 24
💰 Total portfolio value: $1,234,567.89
🏆 Top 5 tokens by value:
   ETH: $500,000.00
   FOX: $300,000.00
   USDC: $200,000.00
   ...
```

## Data Structure

### CSV Format
```csv
Token,Price,Balance,Value
ETH,$2,500.00,200.0,$500,000.00
FOX,$0.15,2,000,000.0,$300,000.00
USDC,$1.00,200,000.0,$200,000.00
```

### JSON Format
```json
[
  {
    "Token": "ETH",
    "Price": "$2,500.00",
    "Balance": "200.0",
    "Value": "$500,000.00"
  },
  {
    "Token": "FOX",
    "Price": "$0.15",
    "Balance": "2,000,000.0",
    "Value": "$300,000.00"
  }
]
```

## Advanced Usage

### Programmatic Usage

```python
import asyncio
from zapper_wallet_scraper import ZapperWalletScraper

async def scrape_portfolio():
    scraper = ZapperWalletScraper(headless=True)
    url = "https://zapper.xyz/bundle/your-addresses..."
    result = await scraper.scrape_wallet_data(url, "my_data")
    
    if result:
        csv_file, json_file = result
        print(f"Data saved to: {csv_file}, {json_file}")

# Run the scraper
asyncio.run(scrape_portfolio())
```

### Custom URL Format

The scraper works with any Zapper bundle URL. Common formats:

- **Single Address**: `https://zapper.xyz/0x1234...`
- **Multiple Addresses**: `https://zapper.xyz/bundle/0x1234...,0x5678...`
- **With Parameters**: `https://zapper.xyz/bundle/...&tab=wallet&label=My%20Portfolio`

## Troubleshooting

### Common Issues

1. **"No table found"**
   - The page may be loading slowly
   - Try running with `--visible` to see what's happening
   - Check if the URL is correct and accessible

2. **"Timeout while loading page"**
   - Network connection issues
   - Zapper site may be down
   - Try again later

3. **"No data extracted"**
   - The wallet may be empty
   - Check if the addresses in the URL are correct
   - Verify the wallet tab is active

4. **Browser crashes**
   - Ensure you have enough system memory
   - Try running in visible mode to debug
   - Update Playwright: `playwright install`

### Debug Mode

Run with visible browser to debug issues:

```bash
python run_zapper_scraper.py --visible
```

This will show the browser window so you can see what's happening during scraping.

## Integration with Existing Project

This scraper integrates seamlessly with your existing ShapeShift affiliate tracker project:

- Uses existing dependencies (Playwright, pandas)
- Follows your project's logging patterns
- Saves data in the same `data/` directory structure
- Compatible with your existing data processing workflows

## Performance Notes

- **Headless mode**: Faster, uses less resources
- **Visible mode**: Slower but useful for debugging
- **Timeout**: 30 seconds default, adjustable in code
- **Pagination**: Automatically handles up to 5 pagination attempts

## Security & Ethics

- ✅ **Respectful scraping**: Uses reasonable delays and doesn't overwhelm servers
- ✅ **User agent**: Uses standard browser user agent
- ✅ **Rate limiting**: Built-in delays between actions
- ✅ **Data privacy**: Only extracts publicly available portfolio data

## License

This tool is part of the ShapeShift affiliate tracker project and follows the same licensing terms. 