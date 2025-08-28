# ButterSwap Web Scraper

A standalone web scraper for extracting transaction data from the [ButterSwap Explorer](https://explorer.butterswap.io/en) with copy-paste address handling.

## Quick Start

1. **Setup**:
   ```bash
   python setup.py
   ```

2. **Test**:
   ```bash
   python test_butterswap_scraper.py
   ```

3. **Demo**:
   ```bash
   python demo_butterswap_scraper.py
   ```

4. **Run**:
   ```bash
   python butterswap_web_scraper.py --chains ethereum --max-tx 100
   ```

## Features

- 🌐 **Web scraping** from Butterswap explorer
- 📋 **Copy-paste address handling** for full addresses
- 🔗 **Multi-chain support** (Ethereum, Polygon, Optimism, Arbitrum, Base, Avalanche, BSC)
- 🎯 **ShapeShift affiliate detection**
- 💾 **SQLite database storage**

## Files

- `butterswap_web_scraper.py` - Main scraper
- `test_butterswap_scraper.py` - Test suite
- `demo_butterswap_scraper.py` - Demo script
- `setup.py` - Setup and dependency installation
- `README_butterswap_web_scraper.md` - Detailed documentation
- `BUTTERSWAP_WEB_SCRAPER_SUMMARY.md` - Implementation summary

## Usage Examples

```bash
# Basic scraping
python butterswap_web_scraper.py --chains ethereum --max-tx 50

# Multi-chain scraping
python butterswap_web_scraper.py --chains ethereum polygon --max-tx 100 --headless

# All chains
python butterswap_web_scraper.py --chains ethereum polygon optimism arbitrum base avalanche bsc --max-tx 50
```

## Requirements

- Python 3.8+
- Chrome browser
- Internet connection

The setup script will install all required Python packages automatically.
