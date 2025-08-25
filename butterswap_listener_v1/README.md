# ButterSwap Affiliate Transaction Listener

A Python tool to track ShapeShift affiliate transactions on the ButterSwap DEX operating on Base blockchain.

## 🎯 What It Does

This listener scans Base blockchain blocks to find transactions involving the ShapeShift affiliate address `0x35339070f178dC4119732982C23F5a8d88D3f8a3` in three ways:

1. **Direct Involvement** - Affiliate sends/receives transactions directly
2. **In Calldata** - Affiliate address appears in transaction input data (DEX calls)
3. **In Event Logs** - Affiliate address appears in smart contract events

## 🚀 Quick Start

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Test Connection
```bash
python butterswap_listener.py --test-connection
```

### Step 3: Check Affiliate Address
```bash
python butterswap_listener.py --check-address
```

### Step 4: Start Scanning
```bash
# Start with 100 blocks
python butterswap_listener.py --max-blocks 100

# If no results, try more blocks
python butterswap_listener.py --max-blocks 1000
```

## 🔧 Configuration

### Environment Variables (Optional)
Create a `.env` file in the same directory for better performance:

```bash
# Get a free API key from alchemy.com
ALCHEMY_API_KEY=your_api_key_here
BASE_RPC_URL=https://base-mainnet.g.alchemy.com/v2/your_api_key_here
```

**Note**: Without an API key, the tool uses a demo RPC endpoint with rate limits.

## 📊 Command Line Options

| Option | Description | Example |
|--------|-------------|---------|
| `--test-connection` | Test blockchain connection | `python butterswap_listener.py --test-connection` |
| `--check-address` | Get affiliate address details | `python butterswap_listener.py --check-address` |
| `--max-blocks` | Number of blocks to scan | `python butterswap_listener.py --max-blocks 500` |
| `--resume` | Resume from last scanned block | `python butterswap_listener.py --resume` |
| `--start-block` | Start from specific block | `python butterswap_listener.py --start-block 50000000` |

## 📁 Output Files

### CSV Data
- **`butterswap_affiliate_transactions.csv`** - All found transactions with details
- Columns: block_number, hash, from, to, value, gas_price, timestamp, detection_method

### Progress Tracking
- **`butterswap_scan_progress.json`** - Tracks last scanned block for resuming

## 🔍 Detection Methods

The listener uses three detection strategies:

1. **Direct Involvement** - Transaction directly involves the affiliate address
2. **In Calldata** - Affiliate address found in transaction input data
3. **In Logs** - Affiliate address found in transaction receipt event logs

## 📈 Expected Results

### Successful Scan
```
✅ SUCCESS: Found 5 affiliate transactions!
📁 Data saved to: butterswap_affiliate_transactions.csv

📊 Sample transactions:
   1. Block 12345678: in_calldata - 0x1234...5678
   2. Block 12345680: in_logs - 0x2345...6789
   3. Block 12345682: direct_involvement - 0x3456...7890
```

### No Transactions Found
```
⚠️ No transactions found in the scanned range.
💡 Try: python butterswap_listener.py --max-blocks 1000
```

## 🛠️ Troubleshooting

### Connection Issues
```bash
❌ Cannot connect to Base RPC
```
**Solutions:**
- Check internet connection
- Verify RPC URL in `.env` file
- Try using Alchemy API key for better reliability

### Rate Limiting
```bash
⚠️ Using demo RPC URL (rate limited)
```
**Solutions:**
- Get free API key from [alchemy.com](https://alchemy.com)
- Add to `.env` file
- Use `--max-blocks` with smaller numbers

### No Transactions Found
**Solutions:**
- Increase block range: `--max-blocks 1000`
- Check different time periods
- Verify affiliate address is correct
- Use `--check-address` to verify connection

## 🔄 Resuming Scans

The listener automatically saves progress and can resume:

```bash
# Resume from last scanned block
python butterswap_listener.py --resume --max-blocks 500

# Start from specific block
python butterswap_listener.py --start-block 50000000 --max-blocks 1000
```

## 📊 Data Analysis

After finding transactions, analyze the CSV file:

```python
import pandas as pd

# Load transactions
df = pd.read_csv('butterswap_affiliate_transactions.csv')

# Summary by detection method
print(df['detection_method'].value_counts())

# Transactions by block range
print(df.groupby(df['block_number'] // 1000 * 1000)['hash'].count())
```

## 🚨 Important Notes

- **Rate Limits**: Demo RPC has strict limits. Use API key for production
- **Block Range**: Start small (100 blocks) then increase if needed
- **Progress**: Always use `--resume` for large scans
- **Validation**: Verify found transactions on BaseScan explorer

## 🔗 Related Resources

- [Base Blockchain Explorer](https://basescan.org/)
- [Alchemy API](https://alchemy.com/) - Free RPC endpoints
- [ButterSwap Documentation](https://docs.butterswap.finance/)
- [ShapeShift Affiliate Program](https://shapeshift.com/affiliate)

## 📝 License

This tool is part of the ShapeShift Affiliate Tracker project.
