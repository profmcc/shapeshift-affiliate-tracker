# ButterSwap Listener v1 - Complete Implementation

## 📁 What Was Created

This folder contains a complete, production-ready ButterSwap affiliate transaction listener for the ShapeShift affiliate tracker project.

### Files Created:
- **`butterswap_listener.py`** - Main listener script (400+ lines)
- **`requirements.txt`** - Python dependencies
- **`README.md`** - Comprehensive usage documentation
- **`test_listener.py`** - Test script to verify functionality
- **`install.sh`** - Automated installation script
- **`BUTTERSWAP_LISTENER_SUMMARY.md`** - This summary file

## 🎯 Core Functionality

The listener tracks ShapeShift affiliate transactions on **Base blockchain** (where ButterSwap operates) using the affiliate address:
```
0x35339070f178dC4119732982C23F5a8d88D3f8a3
```

### Detection Methods:
1. **Direct Involvement** - Affiliate sends/receives directly
2. **In Calldata** - Affiliate address in transaction data (DEX calls)
3. **In Event Logs** - Affiliate address in smart contract events

## 🚀 Quick Start Guide

### 1. Install Dependencies
```bash
cd butterswap_listener_v1
pip install -r requirements.txt
```

### 2. Test Connection
```bash
python butterswap_listener.py --test-connection
```

### 3. Check Affiliate Address
```bash
python butterswap_listener.py --check-address
```

### 4. Start Scanning
```bash
# Start small
python butterswap_listener.py --max-blocks 100

# Increase if no results
python butterswap_listener.py --max-blocks 1000
```

## 🔧 Key Features

- **Smart RPC Management** - Automatically uses `.env` file or Alchemy API key
- **Progress Tracking** - Saves scan progress to resume later
- **Multiple Detection Methods** - Finds transactions in various ways
- **CSV Export** - Saves results to `butterswap_affiliate_transactions.csv`
- **Resume Capability** - Continue from last scanned block
- **Error Handling** - Graceful handling of RPC issues and rate limits

## 📊 Expected Output

### Successful Scan:
```
✅ SUCCESS: Found 5 affiliate transactions!
📁 Data saved to: butterswap_affiliate_transactions.csv

📊 Sample transactions:
   1. Block 12345678: in_calldata - 0x1234...5678
   2. Block 12345680: in_logs - 0x2345...6789
   3. Block 12345682: direct_involvement - 0x3456...7890
```

### No Results:
```
⚠️ No transactions found in the scanned range.
💡 Try: python butterswap_listener.py --max-blocks 1000
```

## 🛠️ Configuration Options

### Environment Variables (`.env` file):
```bash
ALCHEMY_API_KEY=your_api_key_here
BASE_RPC_URL=https://base-mainnet.g.alchemy.com/v2/your_api_key_here
```

### Command Line Options:
- `--test-connection` - Test blockchain connection
- `--check-address` - Get affiliate address details
- `--max-blocks N` - Scan N blocks (default: 100)
- `--resume` - Resume from last scanned block
- `--start-block N` - Start from specific block number

## 📈 Data Output

### CSV Columns:
- `block_number` - Block where transaction occurred
- `hash` - Transaction hash
- `from` - Sender address
- `to` - Recipient address
- `value` - Transaction value in ETH
- `gas_price` - Gas price in Gwei
- `timestamp` - Block timestamp
- `detection_method` - How transaction was detected

### Progress Tracking:
- `butterswap_scan_progress.json` - Tracks last scanned block

## 🔍 Technical Details

- **Blockchain**: Base (Ethereum L2)
- **RPC Provider**: Alchemy (with fallback to demo endpoint)
- **Detection**: Multi-method approach for comprehensive coverage
- **Storage**: CSV format for easy analysis
- **Resume**: JSON-based progress tracking

## 🚨 Important Notes

1. **Rate Limits**: Demo RPC has strict limits - use API key for production
2. **Block Range**: Start small (100 blocks) then increase
3. **Progress**: Always use `--resume` for large scans
4. **Validation**: Verify found transactions on BaseScan explorer

## 🔄 Integration with Project

This listener follows the same patterns as other affiliate listeners in the project:
- CSV-based data storage
- Progress tracking for resuming scans
- Comprehensive error handling
- Clear command-line interface
- Detailed documentation

## 📚 Next Steps

1. **Test the listener** with small block ranges
2. **Get Alchemy API key** for better performance
3. **Run initial scans** to find affiliate transactions
4. **Analyze results** using the CSV output
5. **Integrate with master runner** if needed

## 🎉 Ready to Use!

The ButterSwap listener is complete and ready for production use. It provides a robust, efficient way to track ShapeShift affiliate transactions on the Base blockchain through ButterSwap.
