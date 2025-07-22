# ShapeShift Affiliate Tracker

## Python Package Requirements

To use the debug scripts and token cache utilities, install the following Python packages:

```sh
pip install web3 eth-abi requests
```

- `web3` — for interacting with EVM blockchains
- `eth-abi` — for ABI decoding of logs and events
- `requests` — for HTTP API calls (Etherscan, 4byte.directory, etc.)

If you use Jupyter notebooks in `databases/`, you may also need:

```sh
pip install jupyter pandas matplotlib
```

**Note:**
- All scripts in `shared/` and `scripts/debug/` are compatible with Python 3.8+.
- If you encounter missing package errors, install the required package with `pip install <package>`.

---

A comprehensive multi-protocol affiliate fee tracking system for ShapeShift's cross-chain affiliate program. Tracks affiliate revenues from Relay, Portals, Chainflip, THORChain, CowSwap, and 0x Protocol.

## 🏗️ Repository Structure

```
shapeshift-affiliate-tracker/
├── listeners/                          # Consolidated listeners (one per protocol)
│   ├── relay_listener.py              # Arbitrum relay contract tracker
│   ├── portals_listener.py            # Multi-chain Portals affiliate events
│   ├── chainflip_listener.py          # Chainflip broker affiliate fees
│   ├── thorchain_listener.py          # THORChain Midgard API tracker
│   ├── cowswap_listener.py            # CowSwap affiliate fees (EVM chains)
│   ├── zerox_listener.py              # 0x Protocol affiliate fees (EVM chains)
│   └── master_runner.py               # Unified runner for all protocols
│
├── databases/                          # Organized databases (one per protocol + master)
│   ├── relay_transactions.db          # Relay contract transactions
│   ├── portals_transactions.db        # Portals affiliate events
│   ├── chainflip_transactions.db      # Chainflip broker transactions
│   ├── thorchain_transactions.db      # THORChain affiliate swaps
│   ├── cowswap_transactions.db        # CowSwap affiliate events
│   ├── zerox_transactions.db          # 0x Protocol affiliate events
│   └── comprehensive_affiliate.db     # Master database (all protocols)
│
├── scripts/                           # Utility and analysis scripts
│   ├── debug/                         # Debug and testing scripts
│   ├── analysis/                      # Data analysis and visualization
│   └── utils/                         # Shared utilities and helpers
│
├── abis/                              # Contract ABIs for event parsing
├── docs/                              # Documentation and guides
└── README.md                          # This file
```

## 🚀 Quick Start

### Prerequisites

1. **Install Dependencies**
   ```bash
   pip install web3 requests sqlite3 eth-abi
   ```

2. **Set Environment Variables**
   ```bash
   export INFURA_API_KEY="your_infura_api_key"
   export CMC_API_KEY="your_coinmarketcap_api_key"  # Optional for price data
   ```

### Running Individual Listeners

```bash
# Run specific protocol listeners
cd listeners/

# Relay (Arbitrum) - tracks ShapeShift relay transactions
python relay_listener.py --limit 20

# Portals (Multi-chain) - tracks Portals affiliate events
python portals_listener.py --blocks 2000

# Chainflip - tracks broker affiliate fees via API
python chainflip_listener.py --limit 100

# THORChain - tracks affiliate swaps via Midgard API
python thorchain_listener.py --limit 100

# CowSwap (EVM chains) - tracks CowSwap affiliate events
python cowswap_listener.py --blocks 2000

# 0x Protocol (EVM chains) - tracks 0x affiliate events
python zerox_listener.py --blocks 2000
```

### Running All Listeners (Recommended)

```bash
# Run all listeners and consolidate data
cd listeners/
python master_runner.py --blocks 2000 --limit 100

# Only consolidate existing databases
python master_runner.py --consolidate-only

# Show comprehensive statistics
python master_runner.py --stats-only
```

## 📊 Protocol Coverage

### Supported Protocols

| Protocol | Chains | Type | Data Source |
|----------|--------|------|-------------|
| **Relay** | Arbitrum | Blockchain | Contract events |
| **Portals** | Ethereum, Polygon, Arbitrum, Optimism, Base | Blockchain | Contract events |
| **Chainflip** | Cross-chain | API | Broker feeds |
| **THORChain** | Cross-chain | API | Midgard API |
| **CowSwap** | Ethereum, Polygon, Optimism, Arbitrum, Base | Blockchain | Contract events |
| **0x Protocol** | 7 EVM chains | Blockchain | Contract events |

### ShapeShift Affiliate Addresses

| Chain | Address |
|-------|---------|
| **Ethereum** | `0x90A48D5CF7343B08dA12E067680B4C6dbfE551Be` |
| **Polygon** | `0xB5F944600785724e31Edb90F9DFa16dBF01Af000` |
| **Optimism** | `0x6268d07327f4fb7380732dc6d63d95F88c0E083b` |
| **Arbitrum** | `0x38276553F8fbf2A027D901F8be45f00373d8Dd48` |
| **Base** | `0x9c9aA90363630d4ab1D9dbF416cc3BBC8d3Ed502` |
| **Avalanche** | `0x74d63F31C2335b5b3BA7ad2812357672b2624cEd` |
| **BSC** | `0x8b92b1698b57bEDF2142297e9397875ADBb2297E` |

## 🗄️ Database Schema

### Comprehensive Database (`comprehensive_affiliate.db`)

The master database consolidates all protocols with a unified schema:

```sql
CREATE TABLE comprehensive_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    protocol TEXT NOT NULL,              -- 'Relay', 'Portals', 'Chainflip', etc.
    chain TEXT NOT NULL,                 -- 'Ethereum', 'Arbitrum', 'THORChain', etc.
    tx_hash TEXT NOT NULL,               -- Transaction hash
    block_number INTEGER,                -- Block number (if applicable)
    timestamp INTEGER NOT NULL,          -- Unix timestamp
    from_asset TEXT,                     -- Input asset symbol/address
    to_asset TEXT,                       -- Output asset symbol/address
    from_amount REAL,                    -- Input amount (normalized)
    to_amount REAL,                      -- Output amount (normalized)
    from_amount_usd REAL,                -- Input amount in USD
    to_amount_usd REAL,                  -- Output amount in USD
    volume_usd REAL,                     -- Total volume in USD
    affiliate_fee_amount REAL,           -- Affiliate fee amount
    affiliate_fee_usd REAL,              -- Affiliate fee in USD
    affiliate_fee_asset TEXT,            -- Affiliate fee asset
    affiliate_address TEXT,              -- ShapeShift affiliate address
    sender_address TEXT,                 -- Transaction sender
    recipient_address TEXT,              -- Transaction recipient
    event_type TEXT,                     -- Event type (trade, swap, etc.)
    raw_data TEXT,                       -- Original data as JSON
    created_at INTEGER DEFAULT (strftime('%s', 'now'))
);
```

## 📈 Usage Examples

### Query Affiliate Fees by Protocol

```sql
-- Total affiliate fees by protocol
SELECT 
    protocol,
    COUNT(*) as transaction_count,
    SUM(affiliate_fee_usd) as total_fees_usd,
    SUM(volume_usd) as total_volume_usd
FROM comprehensive_transactions 
GROUP BY protocol 
ORDER BY total_fees_usd DESC;
```

### Daily Affiliate Revenue

```sql
-- Daily affiliate revenue across all protocols
SELECT 
    DATE(timestamp, 'unixepoch') as date,
    SUM(affiliate_fee_usd) as daily_fees,
    COUNT(*) as transaction_count
FROM comprehensive_transactions 
WHERE timestamp > strftime('%s', 'now', '-30 days')
GROUP BY DATE(timestamp, 'unixepoch')
ORDER BY date DESC;
```

### Top Performing Chains

```sql
-- Affiliate performance by chain
SELECT 
    chain,
    COUNT(*) as transactions,
    SUM(affiliate_fee_usd) as total_fees,
    AVG(affiliate_fee_usd) as avg_fee_per_tx
FROM comprehensive_transactions 
GROUP BY chain 
ORDER BY total_fees DESC;
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `INFURA_API_KEY` | Infura project ID for EVM chains | Yes | - |
| `CMC_API_KEY` | CoinMarketCap API key for price data | No | - |
| `THORCHAIN_MIDGARD_URL` | THORChain Midgard API URL | No | `https://midgard.ninerealms.com` |

### Listener Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--blocks` | Number of blocks to scan (blockchain listeners) | 2000 |
| `--limit` | Number of records to fetch (API listeners) | 100 |
| `--skip-consolidation` | Skip database consolidation | False |
| `--consolidate-only` | Only run database consolidation | False |
| `--stats-only` | Only show comprehensive statistics | False |

## 📊 Performance & Monitoring

### Expected Performance

| Listener | Avg Time | Data Volume | Rate Limits |
|----------|----------|-------------|-------------|
| Relay | 30-60s | 20-50 transactions | Infura limits |
| Portals | 2-5 min | 1-10 events | Infura limits |
| Chainflip | 1-2 min | 100-500 transactions | API rate limits |
| THORChain | 1-2 min | 10-50 swaps | API rate limits |
| CowSwap | 3-5 min | 5-20 events | Infura limits |
| 0x Protocol | 3-5 min | 10-30 events | Infura limits |

### Monitoring

```bash
# Monitor comprehensive database growth
sqlite3 databases/comprehensive_affiliate.db "
SELECT 
    datetime('now') as check_time,
    COUNT(*) as total_transactions,
    MAX(timestamp) as latest_timestamp
FROM comprehensive_transactions;
"

# Check individual protocol health
for db in databases/*.db; do
    echo "=== $(basename $db) ==="
    sqlite3 "$db" "SELECT COUNT(*) as records FROM sqlite_master WHERE type='table';"
done
```

## 🚨 Troubleshooting

### Common Issues

1. **Infura Rate Limits**
   - Reduce `--blocks` parameter
   - Add delays between requests
   - Use multiple API keys

2. **Database Locks**
   - Close other database connections
   - Run listeners sequentially instead of parallel

3. **API Timeouts**
   - Check network connectivity
   - Verify API keys are valid
   - Reduce request batch sizes

### Debug Mode

```bash
# Run with debug logging
export PYTHONPATH=.
python -m logging --level DEBUG listeners/master_runner.py
```

## 🤝 Contributing

1. **Adding New Protocols**
   - Create new listener in `listeners/`
   - Follow existing pattern for database schema
   - Add to `master_runner.py` consolidation

2. **Improving Listeners**
   - Add error handling and retries
   - Implement proper rate limiting
   - Add comprehensive logging

## 📄 License

This project is part of ShapeShift's affiliate tracking infrastructure.

## 🔗 Related Resources

- [ShapeShift Documentation](https://docs.shapeshift.com)
- [Chainflip Broker API](https://docs.chainflip-broker.io)
- [THORChain Midgard API](https://midgard.ninerealms.com)
- [CowSwap Documentation](https://docs.cow.fi)
- [0x Protocol Documentation](https://docs.0x.org)

---

**Last Updated:** $(date)  
**Repository Version:** 2.0 (Consolidated) 