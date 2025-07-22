# Chainflip Broker Scraper - Complete Solution

A comprehensive web scraping solution for extracting swaps data from Chainflip broker pages, with multiple approaches to capture full 0x addresses from tooltips and UI elements.

## Overview

This project provides several scraper implementations to extract data from the Chainflip broker page at:
`https://scan.chainflip.io/brokers/cFMeDPtPHccVYdBSJKTtCYuy7rewFNpro3xZBKaCGbSS2xhRi`

## Files Created

### Core Scrapers

1. **`chainflip_scraper.py`** - Basic scraper with simple table extraction
2. **`chainflip_scraper_enhanced.py`** - Enhanced version with better table detection and column identification
3. **`chainflip_tooltip_scraper.py`** - Focused on tooltip extraction for full addresses
4. **`chainflip_debug_scraper.py`** - Debug version to understand page structure
5. **`chainflip_final_scraper.py`** - Final version with multiple extraction methods

### Setup and Documentation

6. **`setup_chainflip_scraper.py`** - Automatic dependency installation
7. **`requirements_chainflip_scraper.txt`** - Python dependencies
8. **`README_chainflip_scraper.md`** - Detailed usage instructions
9. **`README_chainflip_complete.md`** - This comprehensive guide

## Installation

### Quick Setup

```bash
# Install all dependencies automatically
python setup_chainflip_scraper.py
```

### Manual Setup

```bash
# Install Python packages
pip install playwright==1.42.0 beautifulsoup4==4.12.3 pandas==2.1.4 typing-extensions==4.8.0

# Install Playwright browser
playwright install chromium
```

## Usage

### Basic Scraper

```bash
python chainflip_scraper.py
```

### Enhanced Scraper (Recommended)

```bash
python chainflip_scraper_enhanced.py
```

### Tooltip-Focused Scraper

```bash
python chainflip_tooltip_scraper.py
```

### Debug Scraper

```bash
python chainflip_debug_scraper.py
```

### Final Scraper (Multiple Methods)

```bash
python chainflip_final_scraper.py
```

## What Each Scraper Does

### 1. Basic Scraper (`chainflip_scraper.py`)
- Simple table extraction
- Basic address detection
- CSV and JSON output

### 2. Enhanced Scraper (`chainflip_scraper_enhanced.py`)
- **RECOMMENDED FOR MOST USERS**
- Smart column identification
- Better table detection
- Address type classification
- Data analysis features

### 3. Tooltip Scraper (`chainflip_tooltip_scraper.py`)
- Focused on extracting full addresses from tooltips
- Hover interactions
- Multiple tooltip detection methods

### 4. Debug Scraper (`chainflip_debug_scraper.py`)
- Analyzes page structure
- Helps understand where data is stored
- Useful for troubleshooting

### 5. Final Scraper (`chainflip_final_scraper.py`)
- Multiple extraction methods
- JavaScript injection
- Hidden element detection
- Comprehensive analysis

## Data Structure Extracted

The scrapers extract the following data structure:

```json
{
  "Swap Details": "#608637\n0.01 BTC\n$1,098.46\n1,089.88 USDC\n$1,089.71\n0.41968985 ETH\n$1,090.07",
  "Addresses": "0xd9…b663\nbc1q…72vq",
  "Status": "Success",
  "Commission": "$0.55",
  "Age": "4 hours ago\nTook 42m"
}
```

### Column Breakdown

- **Swap Details**: Transaction ID, amounts, tokens, and USD values
- **Addresses**: Abbreviated addresses (from/to addresses)
- **Status**: Transaction status (Success, Pending, etc.)
- **Commission**: Broker commission earned
- **Age**: Time since transaction and duration

## Address Extraction Challenge

### The Problem
The Chainflip interface shows abbreviated addresses (e.g., `0xd9…b663`) but the full addresses are not easily accessible through standard tooltip methods.

### What We Tried
1. **Title attributes** - Not found
2. **Data attributes** - Not found
3. **Hover tooltips** - Not found
4. **JavaScript injection** - Not found
5. **Hidden elements** - Not found

### Possible Reasons
- Full addresses might be loaded dynamically via JavaScript
- Addresses might be stored in a different format
- The site might use custom tooltip implementations
- Full addresses might require authentication or API access

## Working Solution

### Current Capabilities
✅ **Successfully extracts:**
- Complete swaps table data
- Transaction details and amounts
- Abbreviated addresses
- Status and commission information
- Timestamps and durations

⚠️ **Limitations:**
- Full addresses remain abbreviated
- Tooltip extraction not successful with current methods

### Recommended Approach

Use the **Enhanced Scraper** (`chainflip_scraper_enhanced.py`) as it provides:

1. **Complete data extraction** - All table data captured
2. **Smart column identification** - Automatically identifies column types
3. **Data analysis** - Provides insights about the data
4. **Multiple output formats** - CSV and JSON
5. **Robust error handling** - Handles various page structures

## Output Files

Each scraper generates timestamped output files:

- **CSV**: `chainflip_swaps_enhanced_YYYYMMDD_HHMMSS.csv`
- **JSON**: `chainflip_swaps_enhanced_YYYYMMDD_HHMMSS.json`

## Example Output

```
Starting Enhanced Chainflip swaps table scraper...
Target URL: https://scan.chainflip.io/brokers/cFMeDPtPHccVYdBSJKTtCYuy7rewFNpro3xZBKaCGbSS2xhRi
Loading page: https://scan.chainflip.io/brokers/cFMeDPtPHccVYdBSJKTtCYuy7rewFNpro3xZBKaCGbSS2xhRi
Found swaps tab with selector: button:has-text("Swaps")
Found table with selector: table
Found 20 rows with selector: table tbody tr
Found headers: ['Swap Details', 'Addresses', 'Status', 'Commission', 'Age']
Processed 10 rows...
Processed 20 rows...

Successfully scraped 20 swaps

=== Data Analysis ===
Total swaps: 20

Sample data structure:
  Swap Details: #608637\n0.01 BTC\n$1,098.46\n1,089.88 USDC\n$1,089.71\n0.41968985 ETH\n$1,090.07
  Addresses: 0xd9…b663\nbc1q…72vq
  Status: Success
  Commission: $0.55
  Age: 4 hours ago\nTook 42m

Saved 20 swaps to chainflip_swaps_enhanced_20240115_143025.csv
Saved 20 swaps to chainflip_swaps_enhanced_20240115_143025.json
```

## Customization

### Changing the Target URL

Edit the `broker_url` variable in any scraper:

```python
broker_url = "https://scan.chainflip.io/brokers/YOUR_BROKER_ADDRESS"
```

### Modifying Output Format

```python
# Custom filename
scraper.save_to_csv(swaps_data, "my_custom_filename.csv")
scraper.save_to_json(swaps_data, "my_custom_filename.json")
```

## Troubleshooting

### Common Issues

1. **No table found**
   - Page structure may have changed
   - Try running with `headless=False` to see the browser
   - Check if the page requires authentication

2. **Missing data**
   - The page might be loading data dynamically
   - Increase wait times in the scraper
   - Check network connectivity

3. **Address extraction not working**
   - Full addresses might not be available through standard methods
   - The site might require API access for full addresses
   - Consider using the abbreviated addresses for now

### Debug Mode

To run in debug mode (shows browser window):

```python
# In any scraper, change:
browser = await p.chromium.launch(headless=False)
```

## Future Improvements

### Potential Enhancements

1. **API Integration**: If Chainflip provides an API, use it for full address data
2. **Database Storage**: Add SQLite/PostgreSQL storage for historical data
3. **Real-time Monitoring**: Set up continuous scraping with notifications
4. **Address Resolution**: Use blockchain APIs to resolve abbreviated addresses
5. **Data Visualization**: Add charts and analytics

### Alternative Approaches

1. **Blockchain APIs**: Use Etherscan/Blockchain.info APIs to get full addresses
2. **Reverse Engineering**: Analyze the site's JavaScript to find data sources
3. **Network Analysis**: Monitor network requests to find API endpoints
4. **Selenium Alternative**: Try Selenium if Playwright doesn't work

## Conclusion

While we couldn't extract the full 0x addresses through tooltips (likely due to the site's implementation), we've created a comprehensive scraping solution that:

✅ **Successfully extracts all visible table data**
✅ **Provides multiple scraper implementations**
✅ **Handles various page structures**
✅ **Generates clean CSV and JSON output**
✅ **Includes comprehensive documentation**

The **Enhanced Scraper** (`chainflip_scraper_enhanced.py`) is recommended for most use cases as it provides the most complete and robust data extraction.

## Support

For issues or questions:
1. Check the troubleshooting section
2. Run the debug scraper to understand page structure
3. Review the example output
4. Check if the page structure has changed

---

**Note**: This scraper is designed for educational and research purposes. Please respect the website's terms of service and rate limits when using this tool. 