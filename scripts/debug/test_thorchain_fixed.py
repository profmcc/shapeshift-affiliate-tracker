#!/usr/bin/env python3
"""
Test the fixed THORChain parser on the known ShapeShift transaction
"""

import requests
from run_thorchain_listener_fixed import parse_thorchain_swap_for_affiliate

SPECIFIC_TX = "F0FA85DC49BF6754E5999E897364D39CEB3420A24D66ED6AD64FFF39B364DA6A"


def test_known_transaction():
    """Test parsing the known ShapeShift transaction"""
    print(f"🧪 Testing Known ShapeShift Transaction")
    print("=" * 60)

    try:
        # Fetch the specific transaction
        url = f"https://midgard.ninerealms.com/v2/actions?txid={SPECIFIC_TX}"
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        data = response.json()
        actions = data.get("actions", [])

        if not actions:
            print("❌ Transaction not found")
            return

        action = actions[0]
        print(f"✅ Found transaction: {SPECIFIC_TX[:20]}...")

        # Test our parser
        parsed = parse_thorchain_swap_for_affiliate(action)

        if parsed:
            print(f"🎉 Successfully parsed affiliate fee!")
            print(f"   TX ID: {parsed['tx_id']}")
            print(f"   Date: {parsed['date']}")
            print(f"   Affiliate: {parsed['affiliate_address']}")
            print(f"   Fee BPS: {parsed['affiliate_fee_basis_points']}")
            print(f"   Fee Amount: ${parsed['affiliate_fee_amount']:.4f}")
            print(
                f"   From: {parsed['from_amount']:.2f} {parsed['from_asset'].split('.')[-1]}"
            )
            print(
                f"   To: {parsed['to_amount']:.2f} {parsed['to_asset'].split('.')[-1]}"
            )
            print(f"   Volume: ${parsed['from_amount_usd']:.2f}")
            print(f"   Path: {parsed['swap_path']}")
        else:
            print(f"❌ Failed to parse affiliate fee")

            # Debug the raw data
            print(f"\nDebug info:")
            print(f"  Status: {action.get('status')}")
            metadata = action.get("metadata", {})
            swap = metadata.get("swap", {})
            print(f"  Affiliate address: '{swap.get('affiliateAddress', '')}'")
            print(
                f"  Affiliate fee: {swap.get('affiliateFee', 0)} (type: {type(swap.get('affiliateFee', 0))})"
            )

    except Exception as e:
        print(f"Error: {e}")


def test_recent_actions_sample():
    """Test parsing recent actions to find any affiliate fees"""
    print(f"\n🔍 Testing Recent Actions for Affiliate Fees")
    print("=" * 60)

    try:
        url = "https://midgard.ninerealms.com/v2/actions"
        params = {"limit": 50, "type": "swap"}

        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()

        data = response.json()
        actions = data.get("actions", [])

        affiliate_count = 0
        shapeshift_count = 0

        for i, action in enumerate(actions):
            status = action.get("status", "")
            metadata = action.get("metadata", {})
            swap = metadata.get("swap", {})
            affiliate_addr = swap.get("affiliateAddress", "")
            affiliate_fee = swap.get("affiliateFee", 0)

            if affiliate_addr:
                affiliate_count += 1
                if affiliate_addr == "ss":
                    shapeshift_count += 1

                    # Try to parse this one
                    parsed = parse_thorchain_swap_for_affiliate(action)
                    if parsed:
                        print(f"  ✅ Found ShapeShift affiliate fee:")
                        print(f"     TX: {parsed['tx_id'][:20]}...")
                        print(f"     Fee: ${parsed['affiliate_fee_amount']:.4f}")
                        print(f"     Path: {parsed['swap_path']}")

        print(f"\nSummary of {len(actions)} recent actions:")
        print(f"  Actions with affiliate: {affiliate_count}")
        print(f"  ShapeShift affiliate: {shapeshift_count}")

    except Exception as e:
        print(f"Error: {e}")


def main():
    test_known_transaction()
    test_recent_actions_sample()


if __name__ == "__main__":
    main()
