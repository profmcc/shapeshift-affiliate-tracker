# Affiliate Fee Listener 2

A modular affiliate fee tracking system organized by platform for debugging and analysis purposes.

## Structure

```
affiliate_fee_listener_2/
├── portals/                    # Portals-specific data and scripts
│   ├── run_portals_listener.py
│   ├── portals_affiliate_events.db
│   └── extract_portals_data.py
├── 0x_protocol/               # 0x Protocol-specific data and scripts
│   └── extract_0x_data.py
├── cowswap/                   # CowSwap-specific data and scripts
│   └── extract_cowswap_data.py
├── shared/                    # Shared resources
│   ├── comprehensive_affiliate_data.db
│   └── comprehensive_summary.py
├── run_all_extractors.py      # Master script to run all extractors
└── README.md
```

## Usage

### Run All Platform Extractors
```bash
python run_all_extractors.py
```

### Run Individual Platform Extractors
```bash
# Portals
python portals/extract_portals_data.py

# 0x Protocol
python 0x_protocol/extract_0x_data.py

# CowSwap
python cowswap/extract_cowswap_data.py
```

### Run Comprehensive Summary
```bash
python shared/comprehensive_summary.py
```

## Data Sources

- **Portals**: Direct blockchain listening via `run_portals_listener.py`
- **0x Protocol**: Extracted from comprehensive database
- **CowSwap**: Extracted from comprehensive database

## Database Schema

The comprehensive database contains the following fields:
- `tx_hash`: Transaction hash
- `timestamp`: Block timestamp
- `protocol`: Platform name (Portals, 0x Protocol, CowSwap)
- `chain`: Blockchain network
- `from_asset`: Input token address/symbol
- `to_asset`: Output token address/symbol
- `from_amount`: Input amount
- `to_amount`: Output amount
- `affiliate_fee`: Affiliate fee amount
- `affiliate_fee_asset`: Affiliate fee token
- `affiliate_address`: Affiliate wallet address
- `pool`: Pool information (if applicable)
- `status`: Transaction status

## Current Data Summary

- **Total Events**: 10 unique transactions
- **Platforms**: Portals (8), 0x Protocol (1), CowSwap (1)
- **Chains**: Ethereum (8), Arbitrum (1), Polygon (1)
- **Total Affiliate Fees**: FOX, USDC, USDT, ARB, ETH, MATIC

## Debugging Features

Each platform has its own extractor script that:
- Filters data by platform
- Handles missing data gracefully
- Provides detailed transaction information
- Shows platform-specific statistics

## Requirements

- Python 3.7+
- pandas
- sqlite3 (built-in)
- web3 (for blockchain interaction)

## Setup

1. Clone the repository
2. Install dependencies: `pip install pandas web3`
3. Run extractors as needed for debugging

## Notes

- All scripts handle missing data gracefully
- Timestamps are converted to human-readable format
- Duplicate transactions are filtered out
- Each platform can be debugged independently