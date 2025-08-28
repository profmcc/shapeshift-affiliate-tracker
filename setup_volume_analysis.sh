#!/bin/bash

echo "Setting up ShapeShift Volume Analysis dependencies..."

# Install Python dependencies
pip install -r requirements.txt

echo ""
echo "✅ Dependencies installed!"
echo ""
echo "Next steps:"
echo "1. Set your CoinMarketCap API key:"
echo "   export CMC_API_KEY=your_api_key_here"
echo ""
echo "2. Run the analysis:"
echo "   python shapeshift_volume.py /path/to/your/data.json --start 2025-06-01 --end 2025-08-28"
echo ""
echo "Note: Make sure you have a CoinMarketCap API key with access to historical OHLCV data."
