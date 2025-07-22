# ShapeShift Affiliate Fee Implementation

This document describes the implementation of correct ShapeShift affiliate fee calculation for the Chainflip broker transaction database.

## Overview

The system now correctly calculates and stores ShapeShift affiliate fees based on the swap date, distinguishing between the "Broker as a Service" fee (0.05%) and the true ShapeShift affiliate fee (0.5% or 0.55% depending on date).

## Fee Structure

### Broker Fees (Always)
- **Rate**: 0.05% (5 basis points)
- **Purpose**: "Broker as a Service" fee
- **Stored in**: `commission_usd` field

### ShapeShift Affiliate Fees (Date-based)
- **Before May 31, 2024**: 0.5% (50 basis points)
- **On/after May 31, 2024**: 0.55% (55 basis points)
- **Purpose**: True ShapeShift affiliate revenue
- **Stored in**: `affiliate_fee_usd` field

## Database Changes

### New Column
- Added `affiliate_fee_usd REAL NOT NULL DEFAULT 0.0` to the `transactions` table
- This column stores the calculated ShapeShift affiliate fee for each transaction

### Updated Schema
```sql
CREATE TABLE transactions (
    -- ... existing columns ...
    commission_usd REAL NOT NULL,           -- Broker fee (0.05%)
    affiliate_fee_usd REAL NOT NULL DEFAULT 0.0,  -- ShapeShift affiliate fee (0.5% or 0.55%)
    -- ... remaining columns ...
);
```

## Implementation Details

### Fee Calculation Logic
```python
def calculate_affiliate_fee(from_amount_usd: float, timestamp: datetime) -> float:
    cutoff_date = datetime(2024, 5, 31, 0, 0, 0)
    
    if timestamp < cutoff_date:
        return from_amount_usd * 0.005  # 0.5%
    else:
        return from_amount_usd * 0.0055  # 0.55%
```

### Backfill Process
- All existing transactions have been updated with correct affiliate fees
- The backfill script (`backfill_affiliate_fees.py`) can be re-run if needed
- New transactions automatically calculate the correct fee based on swap date

## Usage

### Running Updates
```bash
# Update database with new transactions (includes affiliate fee calculation)
python update_chainflip_db.py

# Backfill existing transactions with correct affiliate fees
python backfill_affiliate_fees.py

# View comprehensive summary
python affiliate_fee_summary.py
```

### Querying Data
```bash
# View database statistics (includes affiliate fees)
python quick_db_test.py

# Interactive query tool (updated to show affiliate fees)
python query_chainflip_db.py
```

### Direct SQL Queries
```sql
-- Get total affiliate fees
SELECT SUM(affiliate_fee_usd) FROM transactions WHERE status = 'Success';

-- Get affiliate fees by date range
SELECT 
    DATE(timestamp) as date,
    SUM(affiliate_fee_usd) as daily_affiliate_fees
FROM transactions 
WHERE status = 'Success'
GROUP BY DATE(timestamp)
ORDER BY date DESC;

-- Compare broker vs affiliate fees
SELECT 
    transaction_id,
    from_amount_usd,
    commission_usd as broker_fee,
    affiliate_fee_usd as affiliate_fee,
    (commission_usd + affiliate_fee_usd) as total_fees
FROM transactions 
WHERE status = 'Success'
ORDER BY CAST(transaction_id AS INTEGER) DESC
LIMIT 10;
```

## Current Results

As of the latest update:
- **Total Transactions**: 1,610
- **Total Volume**: $11,035,891.02
- **Broker Fees**: $5,500.63 (0.05%)
- **ShapeShift Affiliate Fees**: $60,697.40 (0.55% average)
- **Total Fees**: $66,198.03 (0.60% average)

## Files Modified

### Core Files
- `chainflip_database.py` - Updated schema and fee calculation logic
- `query_chainflip_db.py` - Updated to include affiliate fee data
- `update_chainflip_db.py` - Now uses updated database schema

### New Files
- `backfill_affiliate_fees.py` - Script to update existing transactions
- `affiliate_fee_summary.py` - Comprehensive summary report
- `README_affiliate_fees.md` - This documentation

## Verification

The implementation has been verified by:
1. ✅ Correct fee calculations for recent transactions
2. ✅ Backfill of all existing transactions
3. ✅ New transactions automatically get correct fees
4. ✅ Database statistics show expected totals
5. ✅ Query tools display affiliate fee data

## Expected Revenue

Based on the current data, ShapeShift's expected affiliate revenue from these brokers is approximately **$60,697.40**.

This represents the true affiliate revenue, separate from the broker service fees that were previously the only fees being tracked. 