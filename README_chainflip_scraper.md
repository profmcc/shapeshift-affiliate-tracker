# Chainflip Broker Swaps Table Scraper

A powerful web scraper designed to extract swaps data from Chainflip broker pages, with special focus on capturing full 0x addresses from abbreviated display text and tooltips.

## Features

- 🚀 **Automated Table Extraction**: Scrapes swaps tables from Chainflip broker pages
- 🔍 **Full Address Capture**: Extracts complete 0x addresses from tooltips and hover states
- 📊 **Multiple Output Formats**: Saves data to both CSV and JSON formats
- 🔄 **Pagination Support**: Automatically loads all available data
- 🎯 **Smart Column Detection**: Identifies common column types (transaction hashes, addresses, amounts)
- 📈 **Data Analysis**: Provides insights about the scraped data

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

## Installation

### Option 1: Automatic Setup (Recommended)

Run the setup script to automatically install all dependencies:

```bash
python setup_chainflip_scraper.py
```

### Option 2: Manual Installation

1. **Install Python dependencies**:
   ```bash
   pip install playwright==1.42.0 beautifulsoup4==4.12.3 pandas==2.1.4 typing-extensions==4.8.0
   ```

2. **Install Playwright browser**:
   ```bash
   playwright install chromium
   ```

## Usage

### Basic Scraper

Run the basic scraper for simple table extraction:

```bash
python chainflip_scraper.py
```

### Enhanced Scraper (Recommended)

Run the enhanced scraper with advanced features:

```bash
python chainflip_scraper_enhanced.py
```

## How It Works

### Address Extraction Methods

The scraper uses multiple techniques to capture full 0x addresses:

1. **Title Attributes**: Checks `title` attributes for full addresses
2. **Data Attributes**: Looks for `data-tooltip`, `data-title`, `aria-label` attributes
3. **Child Elements**: Searches for child elements with tooltip information
4. **Hover Interactions**: Triggers hover events to reveal dynamic tooltips

### Table Detection

The scraper automatically detects tables using various selectors:
- Standard HTML tables (`<table>`)
- Custom table components (`[data-testid="swaps-table"]`)
- CSS-based tables (`.swaps-table`, `.table`)
- ARIA tables (`div[role="table"]`)

### Data Loading

Automatically handles pagination and "Load More" buttons to capture all available data.

## Output Files

The scraper generates two types of output files:

### CSV Format
- **Filename**: `chainflip_swaps_YYYYMMDD_HHMMSS.csv`
- **Format**: Comma-separated values with headers
- **Use Case**: Excel, Google Sheets, data analysis tools

### JSON Format
- **Filename**: `chainflip_swaps_YYYYMMDD_HHMMSS.json`
- **Format**: Structured JSON data
- **Use Case**: API integration, programmatic processing

## Data Structure

Each swap record contains:

```json
{
  "column_0": "display_text",
  "column_0_full_address": "0x1234567890abcdef...",
  "column_0_display": "0x1234...abcd",
  "column_0_type": "transaction_hash",
  "column_1": "amount_value",
  "column_2": "timestamp",
  ...
}
```

### Column Types

The scraper automatically identifies common column types:

- **transaction_hash**: Full transaction hash (0x...)
- **from_address**: Sender address
- **to_address**: Recipient address
- **contract_address**: Smart contract address
- **address**: Generic address
- **amount**: Numeric values with decimals
- **block_number**: Block numbers or timestamps

## Customization

### Changing the Target URL

Edit the `broker_url` variable in the main function:

```python
broker_url = "https://scan.chainflip.io/brokers/YOUR_BROKER_ADDRESS"
```

### Modifying Output Format

Customize the output by modifying the save methods in the scraper class:

```python
# Custom filename
scraper.save_to_csv(swaps_data, "my_custom_filename.csv")
scraper.save_to_json(swaps_data, "my_custom_filename.json")
```

### Adding Custom Selectors

Extend the table detection by adding custom selectors:

```python
table_selectors = [
    'table tbody tr',
    'your-custom-selector',
    # Add more selectors here
]
```

## Troubleshooting

### Common Issues

1. **No table found**
   - The page structure may have changed
   - Try running with `headless=False` to see what's happening
   - Check if the page requires authentication

2. **Missing addresses**
   - Some addresses might not have tooltips
   - The page might use different tooltip mechanisms
   - Try the enhanced scraper for better address detection

3. **Slow performance**
   - Reduce the number of load attempts in `_load_all_data`
   - Increase timeout values for slower connections

### Debug Mode

To run in debug mode (shows browser window):

```python
# In the scraper class, change:
browser = await p.chromium.launch(headless=False)
```

## Example Output

```
Starting Enhanced Chainflip swaps table scraper...
Target URL: https://scan.chainflip.io/brokers/cFMeDPtPHccVYdBSJKTtCYuy7rewFNpro3xZBKaCGbSS2xhRi
Loading page: https://scan.chainflip.io/brokers/cFMeDPtPHccVYdBSJKTtCYuy7rewFNpro3xZBKaCGbSS2xhRi
Found table with selector: table
Found 25 rows with selector: table tbody tr
Found headers: ['Transaction', 'From', 'To', 'Amount', 'Time']
Processed 10 rows...
Processed 20 rows...
Processed 25 rows...

Successfully scraped 25 swaps

=== Data Analysis ===
Total swaps: 25

Address types found:
  transaction_hash: 25
  from_address: 25
  to_address: 25

Sample data structure:
  Transaction_full_address: 0x1234567890abcdef1234567890abcdef12345678
  Transaction_display: 0x1234...5678
  Transaction_type: transaction_hash
  From_full_address: 0xabcdef1234567890abcdef1234567890abcdef12
  From_display: 0xabcd...ef12
  From_type: from_address
  To_full_address: 0x567890abcdef1234567890abcdef1234567890abcd
  To_display: 0x5678...abcd
  To_type: to_address
  Amount: 1.234 ETH
  Time: 2024-01-15 14:30:25

Saved 25 swaps to chainflip_swaps_enhanced_20240115_143025.csv
Saved 25 swaps to chainflip_swaps_enhanced_20240115_143025.json
```

## Contributing

To contribute to this project:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source and available under the MIT License.

## Support

For issues or questions:

1. Check the troubleshooting section
2. Review the example output
3. Open an issue on the repository

---

**Note**: This scraper is designed for educational and research purposes. Please respect the website's terms of service and rate limits when using this tool. 