# ShapeShift Volume Analysis Tool

A comprehensive Python script that analyzes ShapeShift trading data to compute USD volumes, generate visualizations, and export insights.

## Features

- **JSON Parsing**: Automatically parses exported ShapeShift transaction data
- **Price Resolution**: Maps crypto symbols to CoinMarketCap IDs and fetches historical prices
- **USD Volume Calculation**: Computes USD value for each swap using daily OHLCV data
- **Visualizations**: Generates charts for daily volume and top trading routes
- **CSV Export**: Exports clean data for further analysis in Excel/Tableau

## Quick Start

### 1. Install Dependencies

```bash
# Run the setup script
./setup_volume_analysis.sh

# Or manually install
pip install pandas matplotlib python-dateutil requests tqdm
```

### 2. Set CoinMarketCap API Key

```bash
export CMC_API_KEY=your_api_key_here
```

**Note**: You need a CoinMarketCap API key with access to historical OHLCV data. Free tier usually includes this.

### 3. Run Analysis

```bash
python shapeshift_volume.py /path/to/your/data.json --start 2025-06-01 --end 2025-08-28
```

## Input Data Format

The script expects JSON data with these fields:
- `timestamp`: Transaction timestamp
- `type`: Should be "Swap" for trading data
- `from_amount`: Input token amount
- `to_amount`: Output token amount  
- `from_asset`: Input token symbol
- `to_asset`: Output token symbol
- `raw_row_text`: Fallback text for asset extraction

## Output Files

- **`daily_volume_usd.csv`**: Daily trading volume in USD
- **`top_routes_usd.csv`**: Top trading pairs by volume
- **`daily_volume_usd.png`**: Chart of daily volume over time
- **`top_routes_usd.png`**: Bar chart of top trading routes

## Symbol Normalization

The script automatically handles common symbol variations:
- `WETH` → `ETH` (priced using ETH)
- `WBTC` → `BTC` (priced using BTC)
- Stablecoins (`USDT`, `USDC`, `DAI`) → `1.0 USD`

## Customization

### Adding New Symbol Aliases

Edit the `SYMBOL_ALIAS` dictionary in the script:

```python
SYMBOL_ALIAS = {
    "WETH": "ETH",
    "WBTC": "BTC",
    "YOUR_SYMBOL": "CMC_SYMBOL"
}
```

### Changing Date Range

Modify the `--start` and `--end` arguments to analyze different periods.

### Adjusting Chart Styles

Modify the `plot_and_export()` function to customize chart appearance, colors, and layout.

## Troubleshooting

### "No CMC ID found" Warnings
- Some tokens may not be listed on CoinMarketCap
- The script will try to price swaps using available data
- Check coverage percentage in the output

### Empty Price Table
- Verify your CMC API key has access to historical OHLCV data
- Check API rate limits and plan restrictions
- Consider using a different pricing source (CoinGecko, etc.)

### Missing Dependencies
- Run `pip install -r requirements.txt`
- Ensure you're using Python 3.8+ with pip

## Advanced Usage

### Batch Processing Multiple Files

```bash
for file in data/*.json; do
    python shapeshift_volume.py "$file" --start 2025-06-01 --end 2025-08-28
done
```

### Custom Date Ranges

```bash
# Last 30 days
python shapeshift_volume.py data.json --start $(date -d '30 days ago' +%Y-%m-%d) --end $(date +%Y-%m-%d)

# Specific quarter
python shapeshift_volume.py data.json --start 2025-01-01 --end 2025-03-31
```

## Data Quality Notes

- **Coverage**: The script reports what percentage of swaps could be priced
- **Fallbacks**: Uses input-side pricing first, falls back to output-side
- **Gaps**: Forward-fills small gaps in price data
- **Stables**: Anchors stablecoins to 1.0 USD for consistency

## Next Steps

Once basic volume analysis is working, consider adding:
- Whale vs retail user segmentation
- Asset pair correlation analysis  
- Time-of-day trading patterns
- Fee revenue analysis
- Cross-chain volume comparisons
