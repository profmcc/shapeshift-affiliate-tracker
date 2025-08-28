# 🌉 Portals Affiliate Listener

A comprehensive CSV-based listener for tracking ShapeShift affiliate fees from Portals bridge transactions across multiple EVM chains.

## 🚀 Quick Start

### 1. **Installation**
```bash
# Clone the repository (if not already done)
git clone https://github.com/profmcc/shapeshift-affiliate-tracker.git
cd shapeshift-affiliate-tracker/portals

# Run the installation script
./install_portals.sh
```

### 2. **Configuration**
Create a `.env` file in the root directory with your API keys:
```bash
# Option 1: Alchemy (Recommended)
ALCHEMY_API_KEY=your_alchemy_api_key_here

# Option 2: Infura
INFURA_API_KEY=your_infura_api_key_here
```

### 3. **Testing**
```bash
# Test connections to all chains
python portals_listener.py --test-connection

# Check affiliate addresses
python portals_listener.py --check-addresses
```

### 4. **Running**
```bash
# Scan last 200 blocks on all chains
python portals_listener.py --max-blocks 200

# Use the interactive launcher
./run_portals.py

# Quick alias
./portals --max-blocks 100
```

## 📋 Features

### **Multi-Chain Support**
- **Ethereum** - Mainnet
- **Polygon** - Polygon PoS
- **Optimism** - Optimism L2
- **Arbitrum** - Arbitrum One
- **Base** - Coinbase L2

### **Smart Block Tracking**
- Automatically tracks last processed block per chain
- Prevents duplicate processing
- Resume from where you left off

### **CSV Data Storage**
- `portals_transactions.csv` - Main transaction data
- `portals_block_tracker.csv` - Block processing progress
- Easy to analyze with Excel, pandas, or other tools

### **Affiliate Fee Detection**
- Monitors Portals router contracts
- Identifies ShapeShift affiliate transactions
- Extracts token amounts and symbols
- Tracks cross-chain bridge activity

## 🔧 Technical Details

### **Portals Protocol**
Portals is a cross-chain bridge protocol that enables users to move assets between different blockchain networks. The listener monitors:

- **Router Contract**: `0xbf5A7F3629fB325E2a8453D595AB103465F75E62`
- **Bridge Events**: Cross-chain asset transfers
- **Affiliate Fees**: Revenue sharing with ShapeShift DAO

### **Event Detection**
The listener monitors these event types:
- Bridge transactions
- ERC-20 transfers
- Affiliate fee distributions

### **Data Extraction**
For each detected transaction:
- Transaction hash and block information
- Source and destination addresses
- Token details (address, symbol, amount)
- Affiliate fee information
- Cross-chain bridge metadata

## 📊 Output Format

### **Transactions CSV Columns**
| Column | Description |
|--------|-------------|
| `tx_hash` | Transaction hash |
| `block_number` | Block number |
| `timestamp` | Block timestamp |
| `chain` | Source chain name |
| `from_address` | Sender address |
| `to_address` | Recipient address |
| `token_address` | Token contract address |
| `token_symbol` | Token symbol |
| `amount` | Token amount (raw) |
| `amount_usd` | USD value (if available) |
| `affiliate_address` | ShapeShift affiliate address |
| `affiliate_fee` | Affiliate fee amount |
| `affiliate_fee_usd` | Affiliate fee USD value |
| `bridge_type` | Always "portals" |
| `source_chain` | Source blockchain |
| `destination_chain` | Target blockchain |
| `processed_at` | Processing timestamp |

### **Block Tracker CSV Columns**
| Column | Description |
|--------|-------------|
| `chain` | Chain name |
| `last_processed_block` | Last processed block number |
| `last_processed_timestamp` | Processing timestamp |
| `status` | Processing status |

## 🛠️ Usage Examples

### **Basic Scanning**
```bash
# Scan last 1000 blocks on all chains
python portals_listener.py --max-blocks 1000

# Scan specific chains only
python portals_listener.py --chains ethereum polygon --max-blocks 500
```

### **Testing and Validation**
```bash
# Test all connections
python portals_listener.py --test-connection

# Validate affiliate addresses
python portals_listener.py --check-addresses
```

### **Interactive Mode**
```bash
# Launch interactive menu
./run_portals.py

# Or use the quick alias
./portals
```

## 🔍 Monitoring Specific Transactions

### **Known Portals Transactions**
The listener is configured to detect transactions like:
- **Block 22774492**: Known Portals affiliate transaction
- **Router Address**: `0xbf5A7F3629fB325E2a8453D595AB103465F75E62`

### **Custom Block Ranges**
```bash
# Scan specific block range
python portals_listener.py --block-range 22774490 22774500
```

## 📈 Performance and Optimization

### **Block Processing**
- Processes blocks sequentially to avoid rate limits
- Tracks progress to prevent duplicate work
- Configurable block ranges for testing

### **Rate Limiting**
- Uses Alchemy API with Infura fallback
- Respects RPC provider limits
- Configurable delays between requests

### **Memory Management**
- Processes transactions in batches
- Minimal memory footprint
- CSV streaming for large datasets

## 🚨 Troubleshooting

### **Common Issues**

#### **Connection Errors**
```bash
# Test individual chain connections
python portals_listener.py --test-connection
```

#### **API Key Issues**
```bash
# Check .env file
cat .env

# Verify API key format
ALCHEMY_API_KEY=your_key_here
```

#### **Block Processing Errors**
```bash
# Reset block tracker
rm csv_data/portals_block_tracker.csv

# Restart listener
python portals_listener.py --max-blocks 100
```

### **Debug Mode**
```bash
# Enable verbose logging
export PYTHONPATH=.
python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
from portals_listener import CSVPortalsListener
listener = CSVPortalsListener()
"
```

## 🔄 Updates and Maintenance

### **Regular Maintenance**
- Monitor CSV file sizes
- Check for new Portals contract addresses
- Update affiliate addresses if needed

### **Data Backup**
```bash
# Backup CSV files
cp csv_data/portals_transactions.csv backups/
cp csv_data/portals_block_tracker.csv backups/
```

## 📚 Additional Resources

### **Portals Protocol**
- [Portals Documentation](https://docs.portals.fi/)
- [Router Contract](https://etherscan.io/address/0xbf5A7F3629fB325E2a8453D595AB103465F75E62)
- [Bridge Interface](https://app.portals.fi/)

### **ShapeShift DAO**
- [Treasury Addresses](https://docs.shapeshift.com/)
- [Affiliate Program](https://shapeshift.com/affiliate)

### **Development Tools**
- [Web3.py Documentation](https://web3py.readthedocs.io/)
- [Ethereum ABI](https://docs.soliditylang.org/en/latest/abi-spec.html)

## 🤝 Contributing

### **Development Setup**
```bash
# Create virtual environment
python -m venv venv-portals
source venv-portals/bin/activate

# Install dependencies
pip install -r requirements_portals.txt

# Run tests
python portals_listener.py --test-connection
```

### **Code Style**
- Follow PEP 8 guidelines
- Use type hints for all functions
- Include docstrings for all methods
- Add logging for debugging

## 📄 License

This project is part of the ShapeShift Affiliate Tracker and follows the same licensing terms.

---

## 🎯 Next Steps

1. **Test the listener** with `--test-connection`
2. **Scan recent blocks** with `--max-blocks 200`
3. **Monitor for transactions** and verify data quality
4. **Customize configurations** for your specific needs
5. **Integrate with other tools** for data analysis

For questions or issues, please refer to the main project documentation or create an issue in the repository.

