# Portals Repository Structure

## 📁 Core Files

### **Main Application**
- `portals_listener.py` - Core CSVPortalsListener class for multi-chain monitoring
- `run_portals.py` - Interactive launcher and main entry point
- `portals` - Quick command script for common operations

### **Configuration & Setup**
- `requirements.txt` - Python dependencies
- `install.sh` - Automated installation script
- `.env` - Environment configuration (created during install)

### **Documentation**
- `README.md` - Main project documentation
- `README_PORTALS.md` - Technical implementation details
- `PORTALS_FRESH_START_SUMMARY.md` - Development history and findings
- `PROJECT_STRUCTURE.md` - This file

## 📊 Data Storage

### **CSV Data Directory**
```
csv_data/
├── portals_transactions.csv          # All detected Portals transactions
├── portals_block_tracker.csv         # Block processing progress
└── portals_transactions_downloaded.csv  # Downloaded transaction data
```

### **Data Structure**
- **Transactions CSV**: Complete transaction details with affiliate detection
- **Block Tracker**: Last processed block numbers per chain
- **Downloaded Data**: Specific transaction analysis results

## 🔧 Key Components

### **CSVPortalsListener Class**
- Multi-chain RPC connection management
- Portal event detection and parsing
- Affiliate fee identification
- CSV data persistence
- Block range tracking

### **Supported Chains**
- **Ethereum**: Mainnet with Alchemy/Infura
- **Polygon**: Polygon PoS with Alchemy
- **Optimism**: L2 with Alchemy
- **Arbitrum**: L2 with Alchemy  
- **Base**: L2 with Alchemy

### **Event Detection**
- **Portal Events**: Cross-chain bridge transactions
- **ERC-20 Transfers**: Token movements
- **Affiliate Partnerships**: ShapeShift DAO integration

## 🚀 Quick Start Commands

```bash
# Install
./install.sh

# Run interactive
./portals run

# Quick scan
./portals scan

# Test functionality
./portals test

# Help
./portals help
```

## 📝 Environment Variables

Required in `.env` file:
- `ALCHEMY_API_KEY` - Primary RPC provider
- `INFURA_API_KEY` - Fallback RPC provider (optional)
- `RPC_RATE_LIMIT` - Rate limiting (default: 10 req/s)
- `BLOCK_CHUNK_SIZE` - Block processing chunks (default: 100)

## 🎯 What It Tracks

- **Portals Router**: `0xbf5A7F3629fB325E2a8453D595AB103465F75E62`
- **ShapeShift Treasury**: `0x90A48D5CF7343B08dA12E067680B4C6dbfE551Be`
- **Portal Events**: Cross-chain bridge transactions
- **Affiliate Fees**: Token transfers to ShapeShift DAO

## 🔍 Analysis Tools

- `corrected_august_25_analysis.py` - Transaction analysis and testing
- `download_portals_data.py` - Data download utilities

## 📈 Output Format

All data is stored in CSV format for:
- Easy analysis in Excel/Google Sheets
- Database import
- Automated processing
- Human readability

## 🚨 Important Notes

- **No Database Required**: Pure CSV-based storage
- **Rate Limiting**: Built-in RPC protection
- **Block Tracking**: Avoids reprocessing
- **Multi-Chain**: Simultaneous monitoring
- **Real-Time**: Live transaction detection
