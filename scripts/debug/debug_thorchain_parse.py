#!/usr/bin/env python3
"""
Debug THORChain Parsing Logic Step by Step
"""

import requests
from datetime import datetime
import time

SPECIFIC_TX = 'F0FA85DC49BF6754E5999E897364D39CEB3420A24D66ED6AD64FFF39B364DA6A'
SHAPESHIFT_AFFILIATE_IDS = ['ss']

def debug_parse_step_by_step():
    """Debug the parsing logic step by step"""
    print(f"🐛 Debug THORChain Parsing Step by Step")
    print("=" * 60)
    
    try:
        # Fetch the specific transaction
        url = f"https://midgard.ninerealms.com/v2/actions?txid={SPECIFIC_TX}"
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        actions = data.get('actions', [])
        
        if not actions:
            print("❌ Transaction not found")
            return
        
        action = actions[0]
        print(f"✅ Found transaction: {SPECIFIC_TX[:20]}...")
        
        # Step 1: Extract basic transaction info
        print(f"\n📍 Step 1: Basic Transaction Info")
        tx_id = action.get('txID', '')
        print(f"   TX ID: {tx_id}")
        
        if not tx_id:
            print("   ❌ No TX ID found")
            return
        
        # Step 2: Timestamp conversion
        print(f"\n📍 Step 2: Timestamp Conversion")
        date_timestamp_raw = action.get('date', 0)
        print(f"   Raw timestamp: {date_timestamp_raw}")
        
        if not date_timestamp_raw:
            print("   ❌ No timestamp found")
            return
        
        date_timestamp = int(date_timestamp_raw) / 1000000000
        date_str = datetime.fromtimestamp(date_timestamp).isoformat()
        print(f"   Converted: {date_str}")
        
        # Step 3: Status check
        print(f"\n📍 Step 3: Status Check")
        height = action.get('height', 0)
        status = action.get('status', '')
        print(f"   Height: {height}")
        print(f"   Status: {status}")
        
        if status != 'success':
            print("   ❌ Status is not 'success'")
            return
        
        # Step 4: Extract swap metadata
        print(f"\n📍 Step 4: Swap Metadata")
        metadata = action.get('metadata', {})
        swap = metadata.get('swap', {})
        print(f"   Has metadata: {bool(metadata)}")
        print(f"   Has swap: {bool(swap)}")
        
        # Step 5: Affiliate address check
        print(f"\n📍 Step 5: Affiliate Address Check")
        affiliate_address = swap.get('affiliateAddress', '')
        print(f"   Affiliate address: '{affiliate_address}'")
        print(f"   In ShapeShift IDs: {affiliate_address in SHAPESHIFT_AFFILIATE_IDS}")
        
        if affiliate_address not in SHAPESHIFT_AFFILIATE_IDS:
            print("   ❌ Affiliate address not in ShapeShift IDs")
            return
        
        # Step 6: Affiliate fee extraction
        print(f"\n📍 Step 6: Affiliate Fee Extraction")
        affiliate_fee_raw = swap.get('affiliateFee', 0)
        print(f"   Raw affiliate fee: {affiliate_fee_raw} (type: {type(affiliate_fee_raw)})")
        
        try:
            affiliate_fee = int(affiliate_fee_raw) if affiliate_fee_raw else 0
            print(f"   Converted fee: {affiliate_fee}")
        except (ValueError, TypeError) as e:
            print(f"   ❌ Conversion failed: {e}")
            affiliate_fee = 0
        
        if affiliate_fee == 0:
            print("   ❌ Affiliate fee is 0")
            return
        
        # Step 7: Extract transaction details
        print(f"\n📍 Step 7: Transaction Details")
        in_txs = action.get('in', [])
        out_txs = action.get('out', [])
        print(f"   Input transactions: {len(in_txs)}")
        print(f"   Output transactions: {len(out_txs)}")
        
        if not in_txs or not out_txs:
            print("   ❌ Missing input or output transactions")
            return
        
        # Step 8: Input details
        print(f"\n📍 Step 8: Input Details")
        in_tx = in_txs[0]
        from_address = in_tx.get('address', '')
        in_coins = in_tx.get('coins', [])
        print(f"   From address: {from_address}")
        print(f"   Input coins: {len(in_coins)}")
        
        if not in_coins:
            print("   ❌ No input coins")
            return
        
        in_coin = in_coins[0]
        from_asset = in_coin.get('asset', '')
        from_amount_raw = int(in_coin.get('amount', 0))
        print(f"   From asset: {from_asset}")
        print(f"   From amount (raw): {from_amount_raw}")
        
        # Step 9: Output details
        print(f"\n📍 Step 9: Output Details")
        main_out = None
        affiliate_out = None
        
        for i, out_tx in enumerate(out_txs):
            is_affiliate = out_tx.get('affiliate', False)
            print(f"   Output {i}: affiliate={is_affiliate}")
            if is_affiliate:
                affiliate_out = out_tx
            else:
                main_out = out_tx
        
        if not main_out:
            print("   ❌ No main output found")
            return
        
        to_address = main_out.get('address', '')
        out_coins = main_out.get('coins', [])
        print(f"   To address: {to_address}")
        print(f"   Output coins: {len(out_coins)}")
        
        if not out_coins:
            print("   ❌ No output coins")
            return
        
        out_coin = out_coins[0]
        to_asset = out_coin.get('asset', '')
        to_amount_raw = int(out_coin.get('amount', 0))
        print(f"   To asset: {to_asset}")
        print(f"   To amount (raw): {to_amount_raw}")
        
        # Step 10: USD prices
        print(f"\n📍 Step 10: USD Prices")
        try:
            in_price_usd = float(swap.get('inPriceUSD', 0))
            print(f"   Input price USD: {in_price_usd}")
        except (ValueError, TypeError):
            in_price_usd = 0
            print(f"   ❌ Failed to parse input price USD")
        
        try:
            out_price_usd = float(swap.get('outPriceUSD', 0))
            print(f"   Output price USD: {out_price_usd}")
        except (ValueError, TypeError):
            out_price_usd = 0
            print(f"   ❌ Failed to parse output price USD")
        
        # Step 11: Calculate amounts
        print(f"\n📍 Step 11: Calculate Amounts")
        from_amount = from_amount_raw / 1e8
        to_amount = to_amount_raw / 1e8
        print(f"   From amount: {from_amount}")
        print(f"   To amount: {to_amount}")
        
        from_amount_usd = from_amount * in_price_usd
        to_amount_usd = to_amount * out_price_usd
        print(f"   From amount USD: ${from_amount_usd}")
        print(f"   To amount USD: ${to_amount_usd}")
        
        # Step 12: Calculate affiliate fee
        print(f"\n📍 Step 12: Calculate Affiliate Fee")
        affiliate_fee_percent = affiliate_fee / 10000
        affiliate_fee_amount = from_amount_usd * affiliate_fee_percent
        print(f"   Affiliate fee percent: {affiliate_fee_percent}%")
        print(f"   Affiliate fee amount: ${affiliate_fee_amount}")
        
        # Step 13: Create result
        print(f"\n📍 Step 13: Create Result")
        from_asset_name = from_asset.split('.')[-1] if '.' in from_asset else from_asset.split('-')[0]
        to_asset_name = to_asset.split('.')[-1] if '.' in to_asset else to_asset.split('-')[0]
        swap_path = f"{from_asset_name} -> {to_asset_name}"
        
        result = {
            'tx_id': tx_id,
            'date': date_str,
            'height': height,
            'from_address': from_address,
            'to_address': to_address,
            'affiliate_address': affiliate_address,
            'affiliate_fee_basis_points': affiliate_fee,
            'affiliate_fee_amount': affiliate_fee_amount,
            'from_asset': from_asset,
            'to_asset': to_asset,
            'from_amount': from_amount,
            'to_amount': to_amount,
            'from_amount_usd': from_amount_usd,
            'to_amount_usd': to_amount_usd,
            'swap_path': swap_path,
            'created_at': int(time.time())
        }
        
        print(f"✅ Successfully created result!")
        print(f"   TX: {result['tx_id'][:20]}...")
        print(f"   Date: {result['date']}")
        print(f"   Affiliate: {result['affiliate_address']}")
        print(f"   Fee: ${result['affiliate_fee_amount']:.4f}")
        print(f"   Path: {result['swap_path']}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error in debug parsing: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    debug_parse_step_by_step()

if __name__ == "__main__":
    main() 