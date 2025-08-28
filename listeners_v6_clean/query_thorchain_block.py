#!/usr/bin/env python3
"""
Direct ThorChain Block Query for Block 22,456,113
================================================

This script directly queries ThorChain APIs to check for affiliate transactions
in block 22,456,113 without using the complex listener infrastructure.

Author: ShapeShift Affiliate Tracker Team
Date: 2024
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

# =============================================================================
# THORCHAIN API QUERY
# =============================================================================


class ThorChainBlockQuery:
    """Direct ThorChain API query for specific block"""

    def __init__(self):
        """Initialize ThorChain API endpoints"""
        self.midgard_api = "https://midgard.ninerealms.com/v2"
        self.thornode_api = "https://thornode.ninerealms.com"

        # ShapeShift affiliate identifiers
        self.shapeshift_affiliate_address = (
            "thor122h9hlrugzdny9ct95z6g7afvpzu34s73uklju"
        )
        self.shapeshift_affiliate_name = "ss"

        # API timeout and retry settings
        self.timeout = 60
        self.max_retries = 3

        print(f"🎯 ThorChain Block Query initialized")
        print(f"🌐 Midgard API: {self.midgard_api}")
        print(f"🌐 Thornode API: {self.thornode_api}")
        print(f"🎯 ShapeShift affiliate address: {self.shapeshift_affiliate_address}")
        print(f"🎯 ShapeShift affiliate name: {self.shapeshift_affiliate_name}")

    def query_block_swaps(
        self, target_block: int, blocks_range: int = 100
    ) -> List[Dict]:
        """Query swaps around the target block"""
        try:
            print(f"\n🔍 Querying ThorChain swaps around block {target_block}")
            print(f"📊 Blocks range: ±{blocks_range//2}")

            # Calculate offset range
            start_offset = max(0, target_block - blocks_range // 2)
            end_offset = target_block + blocks_range // 2

            print(f"📊 Offset range: {start_offset} to {end_offset}")

            # Query Midgard API for swaps
            swaps = self._fetch_midgard_swaps(start_offset, blocks_range)

            if not swaps:
                print("❌ No swaps found in the specified range")
                return []

            print(f"✅ Found {len(swaps)} swaps in range")

            # Filter for ShapeShift affiliate swaps
            affiliate_swaps = self._filter_affiliate_swaps(swaps)

            if affiliate_swaps:
                print(f"🎯 Found {len(affiliate_swaps)} ShapeShift affiliate swaps!")
            else:
                print("ℹ️  No ShapeShift affiliate swaps found in this range")

            return affiliate_swaps

        except Exception as e:
            print(f"❌ Error querying block swaps: {e}")
            return []

    def get_current_height(self) -> Optional[int]:
        """Get current ThorChain height"""
        try:
            url = f"{self.midgard_api}/network"
            print(f"📡 Fetching current network info from: {url}")

            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()

            data = response.json()
            current_height = data.get("height", 0)

            print(f"📊 Current ThorChain height: {current_height}")
            return current_height

        except Exception as e:
            print(f"❌ Error getting current height: {e}")
            return None

    def query_recent_swaps(self, limit: int = 1000) -> List[Dict]:
        """Query recent swaps to understand the data structure"""
        try:
            print(f"\n🔍 Querying recent ThorChain swaps (limit: {limit})")

            url = f"{self.midgard_api}/actions"
            params = {"limit": limit, "type": "swap"}

            print(f"📡 Fetching from Midgard API: {url}")
            print(f"📊 Parameters: {params}")

            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()

            data = response.json()
            actions = data.get("actions", [])

            print(f"📊 API response: {len(actions)} recent swap actions")

            if actions:
                # Show sample action structure
                sample_action = actions[0]
                print(f"📋 Sample swap action structure:")
                for key, value in list(sample_action.items())[
                    :10
                ]:  # Show first 10 fields
                    print(f"   {key}: {value}")

            return actions

        except Exception as e:
            print(f"❌ Error fetching recent swaps: {e}")
            return []

    def _fetch_midgard_swaps(self, offset: int, limit: int) -> List[Dict]:
        """Fetch swaps from Midgard API using actions endpoint"""
        try:
            url = f"{self.midgard_api}/actions"
            params = {"limit": limit, "type": "swap"}

            print(f"📡 Fetching from Midgard API: {url}")
            print(f"📊 Parameters: {params}")

            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()

            data = response.json()
            actions = data.get("actions", [])

            print(f"📊 API response: {len(actions)} swap actions")
            return actions

        except requests.exceptions.Timeout:
            print("⏰ Request timed out - Midgard API may be slow")
            return []
        except requests.exceptions.RequestException as e:
            print(f"❌ Request error: {e}")
            return []
        except Exception as e:
            print(f"❌ Error fetching swaps: {e}")
            return []

    def _filter_affiliate_swaps(self, swaps: List[Dict]) -> List[Dict]:
        """Filter swaps for ShapeShift affiliate activity"""
        affiliate_swaps = []

        for swap in swaps:
            try:
                # Check if this swap involves ShapeShift affiliate
                if self._is_shapeshift_affiliate_swap(swap):
                    affiliate_swaps.append(swap)
            except Exception as e:
                print(f"⚠️  Error processing swap: {e}")
                continue

        return affiliate_swaps

    def _is_shapeshift_affiliate_swap(self, action: Dict) -> bool:
        """Check if a swap action involves ShapeShift affiliate"""
        try:
            # Check for affiliate address in swap metadata
            affiliate_address = (
                action.get("metadata", {}).get("swap", {}).get("affiliateAddress", "")
            )

            # Check if this contains any of our affiliate identifiers
            if any(
                affiliate_id in affiliate_address.lower()
                for affiliate_id in [
                    self.shapeshift_affiliate_name,
                    self.shapeshift_affiliate_address,
                ]
            ):
                return True

            # Check memo field for ShapeShift affiliate pattern (:ss:)
            memo = action.get("metadata", {}).get("swap", {}).get("memo", "")
            if memo and ":ss:" in memo.lower():
                return True

            # Also check if memo contains our affiliate address
            if memo and self.shapeshift_affiliate_address in memo:
                return True

            return False

        except Exception as e:
            print(f"⚠️  Error checking affiliate status: {e}")
            return False

    def analyze_swap(self, action: Dict) -> Dict[str, Any]:
        """Analyze a swap action for relevant details"""
        try:
            analysis = {
                "tx_id": action.get("txID", ""),
                "height": action.get("height", 0),
                "pools": action.get("pools", []),
                "from_asset": "",
                "to_asset": "",
                "from_amount": 0,
                "to_amount": 0,
                "affiliate_info": "Not found",
                "timestamp": action.get("date", ""),
                "status": "success",  # Actions are typically successful
            }

            # Extract input/output data
            inputs = action.get("in", [])
            outputs = action.get("out", [])

            if inputs:
                in_data = inputs[0]
                analysis["from_asset"] = (
                    in_data.get("coins", [{}])[0].get("asset", "")
                    if in_data.get("coins")
                    else ""
                )
                analysis["from_amount"] = in_data.get("amount", 0)

            if outputs:
                out_data = outputs[0]
                analysis["to_asset"] = (
                    out_data.get("coins", [{}])[0].get("asset", "")
                    if out_data.get("coins")
                    else ""
                )
                analysis["to_amount"] = out_data.get("amount", 0)

            # Check for affiliate information in metadata
            swap_metadata = action.get("metadata", {}).get("swap", {})
            affiliate_address = swap_metadata.get("affiliateAddress", "")
            memo = swap_metadata.get("memo", "")

            if affiliate_address:
                analysis["affiliate_info"] = f"Address: {affiliate_address}"
            elif memo and ":ss:" in memo.lower():
                analysis["affiliate_info"] = f"Memo pattern: {memo}"
            elif memo and self.shapeshift_affiliate_address in memo:
                analysis["affiliate_info"] = f"Memo contains address: {memo}"

            return analysis

        except Exception as e:
            print(f"⚠️  Error analyzing swap action: {e}")
            return {}

    def analyze_memo_patterns(self, actions: List[Dict]) -> Dict[str, int]:
        """Analyze memo patterns in swap actions to find affiliate patterns"""
        memo_patterns = {}
        ss_memos = []

        for action in actions:
            try:
                memo = action.get("metadata", {}).get("swap", {}).get("memo", "")
                if memo:
                    # Check for :ss: pattern specifically
                    if ":ss:" in memo.lower():
                        ss_memos.append(memo)

                    # Count different memo patterns
                    memo_parts = memo.split(":")
                    if len(memo_parts) > 1:
                        pattern_key = f"parts_{len(memo_parts)}"
                        memo_patterns[pattern_key] = (
                            memo_patterns.get(pattern_key, 0) + 1
                        )
            except Exception:
                continue

        if ss_memos:
            print(f"🎯 Found {len(ss_memos)} swaps with ':ss:' in memo!")
            for i, memo in enumerate(ss_memos[:5]):  # Show first 5
                print(f"   {i+1}: {memo}")

        return memo_patterns


# =============================================================================
# MAIN EXECUTION
# =============================================================================


def main():
    """Main function to query ThorChain block 22,456,113"""
    target_block = 22456113

    try:
        print(f"\n🎯 ThorChain Block Query - Block {target_block}")
        print("=" * 60)

        # Initialize query
        query = ThorChainBlockQuery()

        # First, get current ThorChain height to understand the scale
        current_height = query.get_current_height()
        if current_height:
            print(f"📊 Target block {target_block} vs current height {current_height}")
            if target_block > current_height:
                print(
                    "⚠️  Target block is higher than current height - may not exist yet"
                )
            else:
                print(
                    f"✅ Target block {target_block} exists (current height: {current_height})"
                )

        # Query recent swaps to understand data structure and check for memo patterns
        recent_swaps = query.query_recent_swaps(limit=100)

        # Analyze memo patterns in recent swaps
        print(f"\n🔍 Analyzing memo patterns in recent swaps...")
        memo_patterns = query.analyze_memo_patterns(recent_swaps)

        # Check if any recent swaps are around our target block
        print(f"\n🔍 Checking if any recent swaps are around block {target_block}...")
        target_range_swaps = []
        for swap in recent_swaps:
            height = swap.get("height", 0)
            try:
                height_int = int(height) if height else 0
                if abs(height_int - target_block) <= 1000:  # Within 1000 blocks
                    target_range_swaps.append(swap)
            except (ValueError, TypeError):
                continue

        if target_range_swaps:
            print(
                f"✅ Found {len(target_range_swaps)} swaps within 1000 blocks of target block {target_block}"
            )
            for swap in target_range_swaps:
                print(f"   Block {swap.get('height', 0)}: {swap.get('txID', 'N/A')}")
        else:
            print(
                f"ℹ️  No recent swaps found within 1000 blocks of target block {target_block}"
            )

        # Query swaps around the target block with larger range to find data
        print(f"\n🔍 Querying larger range around target block {target_block}")
        target_swaps = query._fetch_midgard_swaps(0, 1000)  # Get 1000 recent swaps

        # Analyze memo patterns in the target range
        if target_swaps:
            print(f"\n🔍 Analyzing memo patterns in target range swaps...")
            target_memo_patterns = query.analyze_memo_patterns(target_swaps)

        # Filter for affiliate swaps using updated logic
        affiliate_swaps = query._filter_affiliate_swaps(target_swaps)

        # Analyze the block heights we found to understand the range
        if affiliate_swaps:
            print(f"\n📊 Analyzing found swaps...")
            heights = []
            for swap in affiliate_swaps:
                try:
                    height = int(swap.get("height", 0))
                    if height > 0:
                        heights.append(height)
                except (ValueError, TypeError):
                    continue

            if heights:
                heights.sort()
                print(f"📊 Block height range: {min(heights)} to {max(heights)}")
                print(f"📊 Total unique blocks: {len(set(heights))}")

                # Check if our target block is in this range
                if target_block in heights:
                    print(f"🎯 Target block {target_block} found in the data!")
                else:
                    print(f"ℹ️  Target block {target_block} not found in the data")
                    print(
                        f"💡 Closest blocks: {min(heights, key=lambda x: abs(x - target_block))}"
                    )
        else:
            print(f"\n🔍 No swaps found in the range around block {target_block}")
            print(f"💡 This suggests the block might be from an earlier time period")

        # Examine the actual swap data to understand affiliate patterns
        print(f"\n🔍 Examining swap data structure for affiliate patterns...")
        if affiliate_swaps:
            # Check a few swaps for affiliate data
            affiliate_addresses_found = set()
            for i, swap in enumerate(affiliate_swaps[:5]):  # Check first 5 swaps
                affiliate_address = (
                    swap.get("metadata", {}).get("swap", {}).get("affiliateAddress", "")
                )
                if affiliate_address:
                    affiliate_addresses_found.add(affiliate_address)
                    print(f"   Swap {i+1}: affiliateAddress = '{affiliate_address}'")
                else:
                    print(f"   Swap {i+1}: no affiliate address")

            if affiliate_addresses_found:
                print(f"✅ Found affiliate addresses: {affiliate_addresses_found}")
            else:
                print("ℹ️  No affiliate addresses found in the sample swaps")

            # Check if any swaps have our target affiliate identifiers
            print(f"\n🔍 Checking for ShapeShift affiliate patterns...")
            shapeshift_matches = 0
            for swap in affiliate_swaps:
                affiliate_address = (
                    swap.get("metadata", {}).get("swap", {}).get("affiliateAddress", "")
                )
                if (
                    query.shapeshift_affiliate_name in affiliate_address.lower()
                    or query.shapeshift_affiliate_address in affiliate_address.lower()
                ):
                    shapeshift_matches += 1

            print(f"📊 ShapeShift affiliate matches found: {shapeshift_matches}")

            if shapeshift_matches == 0:
                print("💡 No ShapeShift affiliate activity found in this block range")
                print("   This could mean:")
                print("   - The block range is too narrow")
                print("   - ShapeShift affiliate activity is rare")
                print("   - Different affiliate identifiers are used")
                print("   - The target block is from a different time period")

        if not affiliate_swaps:
            print(
                f"\nℹ️  No ShapeShift affiliate swaps found around block {target_block}"
            )
            print("💡 This could mean:")
            print("   - No affiliate activity in this block range")
            print("   - Different affiliate identifiers were used")
            print("   - The block range needs to be expanded")
            print("   - The block number format might be different")

            # Try to find any swaps with affiliate activity to confirm detection works
            print(f"\n🔍 Checking recent swaps for any affiliate activity patterns...")
            recent_affiliate_swaps = query._filter_affiliate_swaps(recent_swaps)
            if recent_affiliate_swaps:
                print(
                    f"🎯 Found {len(recent_affiliate_swaps)} recent ShapeShift affiliate swaps!"
                )
                print("💡 This confirms affiliate detection is working")

                # Show a sample affiliate swap
                sample_affiliate = recent_affiliate_swaps[0]
                analysis = query.analyze_swap(sample_affiliate)
                print(f"\n📋 Sample affiliate swap:")
                print(f"   Block: {analysis['height']}")
                print(f"   Affiliate: {analysis['affiliate_info']}")
                print(
                    f"   Pools: {', '.join(analysis['pools']) if analysis['pools'] else 'N/A'}"
                )
            else:
                print("ℹ️  No recent ShapeShift affiliate swaps found either")
                print("💡 This could mean:")
                print("   - No affiliate activity in recent blocks")
                print("   - Different affiliate identifiers are being used")
                print("   - The affiliate detection logic needs adjustment")

        if not affiliate_swaps:
            print(
                f"\nℹ️  No ShapeShift affiliate swaps found around block {target_block}"
            )
            print("💡 This could mean:")
            print("   - No affiliate activity in this block range")
            print("   - Different affiliate identifiers were used")
            print("   - The block range needs to be expanded")
            print("   - The block number format might be different")

            # Try to find any swaps with affiliate activity to confirm detection works
            print(f"\n🔍 Checking recent swaps for any affiliate activity patterns...")
            recent_affiliate_swaps = query._filter_affiliate_swaps(recent_swaps)
            if recent_affiliate_swaps:
                print(
                    f"🎯 Found {len(recent_affiliate_swaps)} recent ShapeShift affiliate swaps!"
                )
                print("💡 This confirms affiliate detection is working")

                # Show a sample affiliate swap
                sample_affiliate = recent_affiliate_swaps[0]
                analysis = query.analyze_swap(sample_affiliate)
                print(f"\n📋 Sample affiliate swap:")
                print(f"   Block: {analysis['height']}")
                print(f"   Affiliate: {analysis['affiliate_info']}")
                print(
                    f"   Pools: {', '.join(analysis['pools']) if analysis['pools'] else 'N/A'}"
                )
            else:
                print("ℹ️  No recent ShapeShift affiliate swaps found either")
                print("💡 This could mean:")
                print("   - No affiliate activity in recent blocks")
                print("   - Different affiliate identifiers are being used")
                print("   - The affiliate detection logic needs adjustment")

        # Analyze and display results
        print(f"\n🎯 ShapeShift Affiliate Swaps Found: {len(affiliate_swaps)}")
        print("=" * 60)

        for i, swap in enumerate(affiliate_swaps, 1):
            analysis = query.analyze_swap(swap)

            print(f"\n📊 Swap {i}:")
            print(f"   Transaction ID: {analysis['tx_id']}")
            print(f"   Block Height: {analysis['height']}")
            print(
                f"   Pools: {', '.join(analysis['pools']) if analysis['pools'] else 'N/A'}"
            )
            print(f"   From: {analysis['from_amount']} {analysis['from_asset']}")
            print(f"   To: {analysis['to_amount']} {analysis['to_asset']}")
            print(f"   Affiliate: {analysis['affiliate_info']}")
            print(f"   Status: {analysis['status']}")
            print(f"   Timestamp: {analysis['timestamp']}")

        print(f"\n✅ ThorChain block query completed successfully!")
        print(f"   Target block: {target_block}")
        print(f"   Affiliate swaps found: {len(affiliate_swaps)}")

    except Exception as e:
        print(f"❌ Error running ThorChain block query: {e}")
        raise


if __name__ == "__main__":
    main()
