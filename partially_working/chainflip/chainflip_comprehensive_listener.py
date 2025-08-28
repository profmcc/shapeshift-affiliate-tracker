#!/usr/bin/env python3
"""
Chainflip Comprehensive Listener - Find ShapeShift transactions using all available methods

This script attempts to discover ShapeShift affiliate transactions on Chainflip using multiple
RPC methods and data analysis approaches. It serves as a comprehensive investigation tool
to understand what data is available and how to extract ShapeShift transaction information.

Key Features:
- Multiple RPC method testing (cf_scheduled_swaps, cf_prewitness_swaps, cf_pool_orders)
- Data pattern analysis for ShapeShift indicators
- Comprehensive logging and error handling
- CSV output for analysis and debugging

Author: ShapeShift Affiliate Tracker Team
Date: August 2025
Status: Partially Working - RPC methods have parameter issues
"""

# =============================================================================
# IMPORTS AND DEPENDENCIES
# =============================================================================
# HTTP library for making RPC calls to the Chainflip node
import requests

# JSON handling for RPC payloads and response parsing
import json

# CSV file operations for data export and analysis
import csv

# Time handling for delays and timestamps
import time

# Date and time utilities for logging and data timestamps
from datetime import datetime

# =============================================================================
# RPC COMMUNICATION FUNCTIONS
# =============================================================================
# These functions handle communication with the Chainflip node via JSON-RPC


def make_rpc_call(method, params=None):
    """
    Make a JSON-RPC call to the Chainflip node

    This function:
    1. Constructs a JSON-RPC 2.0 compliant payload
    2. Sends an HTTP POST request to the local Chainflip node
    3. Handles response parsing and error checking
    4. Returns the result or None on error

    Args:
        method (str): The RPC method to call (e.g., 'cf_scheduled_swaps')
        params (list, optional): Parameters to pass to the RPC method

    Returns:
        dict/None: The RPC result if successful, None if failed

    Purpose:
        - Provides a standardized way to communicate with the Chainflip node
        - Handles common RPC errors and HTTP issues
        - Enables testing of various Chainflip RPC methods
    """

    # =====================================================================
    # STEP 1: CONSTRUCT JSON-RPC PAYLOAD
    # =====================================================================
    # Create the JSON-RPC 2.0 compliant payload
    # id: Unique identifier for the request (used for response matching)
    # jsonrpc: Protocol version (always "2.0")
    # method: The RPC method to call
    # params: Optional parameters for the method
    payload = {"id": 1, "jsonrpc": "2.0", "method": method}

    # Add parameters if they were provided
    if params:
        payload["params"] = params

    try:
        # =====================================================================
        # STEP 2: SEND HTTP POST REQUEST TO CHAINFLIP NODE
        # =====================================================================
        # Make an HTTP POST request to the local Chainflip node
        # localhost:9944 is the default HTTP RPC endpoint for Chainflip
        # timeout=10 seconds prevents hanging on unresponsive nodes
        response = requests.post("http://localhost:9944", json=payload, timeout=10)

        # =====================================================================
        # STEP 3: PROCESS HTTP RESPONSE
        # =====================================================================
        if response.status_code == 200:
            # HTTP request was successful, parse the JSON response
            result = response.json()

            # Check if the response contains a successful result
            if "result" in result:
                return result["result"]
            elif "error" in result:
                # RPC method returned an error (e.g., "Invalid params", "Method not found")
                print(f"❌ API Error: {method} - {result['error']}")
                return None
        else:
            # HTTP request failed (e.g., 404, 500, connection refused)
            print(f"❌ HTTP Error: {response.status_code}")
            return None

    except Exception as e:
        # Handle any unexpected errors during the request
        # This includes network issues, JSON parsing errors, etc.
        print(f"❌ Request failed: {e}")
        return None


# =============================================================================
# DATA ANALYSIS FUNCTIONS
# =============================================================================
# These functions analyze RPC response data for ShapeShift-related information


def search_for_shapeshift_in_data(data, data_type, index=None):
    """
    Search for ShapeShift activity in data

    This function:
    1. Converts data to a searchable string format
    2. Searches for various ShapeShift indicators
    3. Returns a list of matches found
    4. Handles different data types and structures

    Args:
        data: The data to search through (can be dict, list, or primitive)
        data_type (str): Description of the data type for logging
        index (int, optional): Index if data is part of a larger collection

    Returns:
        list: List of strings describing matches found

    Purpose:
        - Identifies potential ShapeShift activity in RPC responses
        - Provides searchable patterns for affiliate detection
        - Enables debugging of what data contains ShapeShift references
    """

    # Initialize list to store any matches found
    matches = []

    try:
        # =====================================================================
        # STEP 1: CONVERT DATA TO SEARCHABLE FORMAT
        # =====================================================================
        # Convert the data to a JSON string and then to lowercase
        # This makes it easier to search for text patterns regardless of case
        data_str = json.dumps(data).lower()

        # =====================================================================
        # STEP 2: SEARCH FOR SHAPESHIFT INDICATORS
        # =====================================================================
        # Define search terms that might indicate ShapeShift involvement
        # These terms are based on common patterns found in affiliate transactions
        search_terms = [
            "shapeshift",  # Full company name
            "shape shift",  # Alternative spelling
            "ss:",  # Common affiliate code prefix
            "ss:",  # Alternative affiliate code format
            "broker",  # Chainflip broker terminology
            "affiliate",  # General affiliate terminology
        ]

        # Search for each term in the data
        for term in search_terms:
            if term in data_str:
                # Create a descriptive match message
                match_msg = f"Found '{term}' in {data_type}"
                if index is not None:
                    match_msg += f" at index {index}"
                matches.append(match_msg)

        # =====================================================================
        # STEP 3: SEARCH FOR BROKER ADDRESSES
        # =====================================================================
        # Search for known ShapeShift broker addresses in Chainflip
        # These addresses are used by ShapeShift to facilitate swaps
        brokers = [
            "cFMeDPtPHccVYdBSJKTtCYuy7rewFNpro3xZBKaCGbSS2xhRi",  # Primary ShapeShift broker
            "cFK6mYjpajcwPDZ7JUsac8XUoVSJnhjL43ZMZW7YoN8HE4dD8",  # Secondary ShapeShift broker
        ]

        # Search for each broker address in the data
        for broker in brokers:
            if broker in json.dumps(data):
                # Create a match message with truncated broker address for readability
                matches.append(f"Found broker {broker[:20]}... in {data_type}")

        # =====================================================================
        # STEP 4: RETURN MATCHES
        # =====================================================================
        # Return all matches found during the search
        return matches

    except Exception as e:
        # Handle any errors that occur during the search process
        # This includes JSON serialization errors, data type issues, etc.
        return [f"Error searching {data_type}: {e}"]


def main():
    """
    Main function to run the Chainflip comprehensive listener

    This function:
    1. Tests multiple RPC methods to find ShapeShift transactions
    2. Analyzes responses for ShapeShift indicators
    3. Collects all findings into a comprehensive dataset
    4. Saves results to CSV for analysis
    5. Provides detailed logging of the investigation process

    Purpose:
        - Comprehensive investigation of available Chainflip RPC methods
        - Identification of which methods return useful data
        - Collection of ShapeShift transaction patterns
        - Debugging of RPC parameter issues
    """

    # =====================================================================
    # STEP 1: INITIALIZE AND DISPLAY HEADER
    # =====================================================================
    print("🔍 Chainflip Comprehensive Listener - Finding ShapeShift Transactions")
    print("=" * 75)

    # Initialize list to store all transaction findings
    # This will be used to create a comprehensive CSV report
    all_transactions = []

    # =====================================================================
    # STEP 2: METHOD 1 - SCHEDULED SWAPS (NO PARAMETERS)
    # =====================================================================
    # Test cf_scheduled_swaps without parameters based on error message analysis
    # Previous attempts with parameters resulted in "Invalid params" errors
    print(f"\n🔍 Method 1: Scheduled Swaps (No Parameters)")
    print("-" * 40)

    # Make RPC call to get scheduled swaps
    swaps = make_rpc_call("cf_scheduled_swaps")  # No parameters

    if swaps:
        print(f"   ✅ Found {len(swaps)} scheduled swaps")

        # Analyze each swap for ShapeShift indicators
        for i, swap in enumerate(swaps):
            if isinstance(swap, dict):
                # Search for ShapeShift patterns in the swap data
                matches = search_for_shapeshift_in_data(swap, "scheduled_swaps", i)

                if matches:
                    print(f"      🎯 Swap {i}: {matches}")

                    # Create a transaction record for this finding
                    transaction = {
                        "timestamp": datetime.now().isoformat(),  # When the search was performed
                        "method": "cf_scheduled_swaps",  # RPC method used
                        "data_type": "scheduled_swaps",  # Type of data found
                        "index": i,  # Position in the results
                        "matches": matches,  # What was found
                        "raw_data": json.dumps(swap)[
                            :500
                        ],  # First 500 chars of raw data
                        "detection_method": "scheduled_swaps_no_params",  # How it was detected
                    }
                    all_transactions.append(transaction)
    else:
        print(f"   ❌ No scheduled swaps found")

    # =====================================================================
    # STEP 3: METHOD 2 - PREWITNESS SWAPS (NO PARAMETERS)
    # =====================================================================
    # Test cf_prewitness_swaps without parameters
    # This method should show swaps that are waiting for witness confirmation
    print(f"\n🔍 Method 2: Prewitness Swaps (No Parameters)")
    print("-" * 40)

    # Make RPC call to get prewitness swaps
    swaps = make_rpc_call("cf_prewitness_swaps")  # No parameters

    if swaps:
        print(f"   ✅ Found {len(swaps)} prewitness swaps")

        # Analyze each swap for ShapeShift indicators
        for i, swap in enumerate(swaps):
            if isinstance(swap, dict):
                # Search for ShapeShift patterns in the swap data
                matches = search_for_shapeshift_in_data(swap, "prewitness_swaps", i)

                if matches:
                    print(f"      🎯 Swap {i}: {matches}")

                    # Create a transaction record for this finding
                    transaction = {
                        "timestamp": datetime.now().isoformat(),  # When the search was performed
                        "method": "cf_prewitness_swaps",  # RPC method used
                        "data_type": "prewitness_swaps",  # Type of data found
                        "index": i,  # Position in the results
                        "matches": matches,  # What was found
                        "raw_data": json.dumps(swap)[
                            :500
                        ],  # First 500 chars of raw data
                        "detection_method": "prewitness_swaps_no_params",  # How it was detected
                    }
                    all_transactions.append(transaction)
    else:
        print(f"   ❌ No prewitness swaps found")

    # =====================================================================
    # STEP 4: METHOD 3 - POOL ORDERS (NO PARAMETERS)
    # =====================================================================
    # Test cf_pool_orders without parameters
    # This method should show liquidity pool orders
    print(f"\n🔍 Method 3: Pool Orders (No Parameters)")
    print("-" * 35)

    # Make RPC call to get pool orders
    orders = make_rpc_call("cf_pool_orders")  # No parameters

    if orders:
        print(f"   ✅ Found {len(orders)} pool orders")

        # Analyze each order for ShapeShift indicators
        for i, order in enumerate(orders):
            if isinstance(order, dict):
                # Search for ShapeShift patterns in the order data
                matches = search_for_shapeshift_in_data(order, "pool_orders", i)

                if matches:
                    print(f"      🎯 Order {i}: {matches}")

                    # Create a transaction record for this finding
                    transaction = {
                        "timestamp": datetime.now().isoformat(),  # When the search was performed
                        "method": "cf_pool_orders",  # RPC method used
                        "data_type": "pool_orders",  # Type of data found
                        "index": i,  # Position in the results
                        "matches": matches,  # What was found
                        "raw_data": json.dumps(order)[
                            :500
                        ],  # First 500 chars of raw data
                        "detection_method": "pool_orders_no_params",  # How it was detected
                    }
                    all_transactions.append(transaction)
    else:
        print(f"   ❌ No pool orders found")

    # =====================================================================
    # STEP 5: METHOD 4 - LP ORDER FILLS
    # =====================================================================
    # Test cf_lp_get_order_fills with empty parameters
    # This method should show completed liquidity provider order fills
    print(f"\n🔍 Method 4: LP Order Fills")
    print("-" * 25)

    # Make RPC call to get LP order fills
    fills = make_rpc_call("cf_lp_get_order_fills", [])

    if fills:
        print(f"   ✅ Found {len(fills)} LP order fills")

        # Analyze each fill for ShapeShift indicators
        for i, fill in enumerate(fills):
            if isinstance(fill, dict):
                # Search for ShapeShift patterns in the fill data
                matches = search_for_shapeshift_in_data(fill, "lp_order_fills", i)

                if matches:
                    print(f"      🎯 Fill {i}: {matches}")

                    # Create a transaction record for this finding
                    transaction = {
                        "timestamp": datetime.now().isoformat(),  # When the search was performed
                        "method": "cf_lp_get_order_fills",  # RPC method used
                        "data_type": "lp_order_fills",  # Type of data found
                        "index": i,  # Position in the results
                        "matches": matches,  # What was found
                        "raw_data": json.dumps(fill)[
                            :500
                        ],  # First 500 chars of raw data
                        "detection_method": "lp_order_fills",  # How it was detected
                    }
                    all_transactions.append(transaction)
    else:
        print(f"   ❌ No LP fills found")

    # =====================================================================
    # STEP 6: METHOD 5 - TRANSACTION SCREENING EVENTS
    # =====================================================================
    # Test cf_get_transaction_screening_events with empty parameters
    # This method should show events related to transaction screening
    print(f"\n🔍 Method 5: Transaction Screening Events")
    print("-" * 40)

    # Make RPC call to get transaction screening events
    events = make_rpc_call("cf_get_transaction_screening_events", [])

    if events:
        print(f"   ✅ Found {len(events)} screening events")

        # Analyze each event for ShapeShift indicators
        for i, event in enumerate(events):
            if isinstance(event, dict):
                # Search for ShapeShift patterns in the event data
                matches = search_for_shapeshift_in_data(event, "screening_events", i)

                if matches:
                    print(f"      🎯 Event {i}: {matches}")

                    # Create a transaction record for this finding
                    transaction = {
                        "timestamp": datetime.now().isoformat(),  # When the search was performed
                        "method": "cf_get_transaction_screening_events",  # RPC method used
                        "data_type": "screening_events",  # Type of data found
                        "index": i,  # Position in the results
                        "matches": matches,  # What was found
                        "raw_data": json.dumps(event)[
                            :500
                        ],  # First 500 chars of raw data
                        "detection_method": "screening_events",  # How it was detected
                    }
                    all_transactions.append(transaction)

    # =====================================================================
    # STEP 7: METHOD 6 - OPEN DEPOSIT CHANNELS
    # =====================================================================
    # Test cf_all_open_deposit_channels with empty parameters
    # This method should show open deposit channels for cross-chain transfers
    print(f"\n🔍 Method 6: Open Deposit Channels")
    print("-" * 35)

    # Make RPC call to get open deposit channels
    channels = make_rpc_call("cf_all_open_deposit_channels", [])

    if channels:
        print(f"   ✅ Found {len(channels)} open deposit channels")

        # Analyze each channel for ShapeShift indicators
        for i, channel in enumerate(channels):
            if isinstance(channel, dict):
                # Search for ShapeShift patterns in the channel data
                matches = search_for_shapeshift_in_data(channel, "deposit_channels", i)

                if matches:
                    print(f"      🎯 Channel {i}: {matches}")

                    # Create a transaction record for this finding
                    transaction = {
                        "timestamp": datetime.now().isoformat(),  # When the search was performed
                        "method": "cf_all_open_deposit_channels",  # RPC method used
                        "data_type": "deposit_channels",  # Type of data found
                        "index": i,  # Position in the results
                        "matches": matches,  # What was found
                        "raw_data": json.dumps(channel)[
                            :500
                        ],  # First 500 chars of raw data
                        "detection_method": "deposit_channels",  # How it was detected
                    }
                    all_transactions.append(transaction)
    else:
        print(f"   ❌ No open deposit channels found")

    # =====================================================================
    # STEP 8: METHOD 7 - PENDING BROADCASTS
    # =====================================================================
    # Test cf_monitoring_pending_broadcasts with empty parameters
    # This method should show transactions waiting to be broadcast
    print(f"\n🔍 Method 7: Pending Broadcasts")
    print("-" * 30)

    # Make RPC call to get pending broadcasts
    broadcasts = make_rpc_call("cf_monitoring_pending_broadcasts", [])

    if broadcasts:
        print(f"   ✅ Found {len(broadcasts)} pending broadcasts")

        # Analyze each broadcast for ShapeShift indicators
        for i, broadcast in enumerate(broadcasts):
            if isinstance(broadcast, dict):
                # Search for ShapeShift patterns in the broadcast data
                matches = search_for_shapeshift_in_data(
                    broadcast, "pending_broadcasts", i
                )

                if matches:
                    print(f"      🎯 Broadcast {i}: {matches}")

                    # Create a transaction record for this finding
                    transaction = {
                        "timestamp": datetime.now().isoformat(),  # When the search was performed
                        "method": "cf_monitoring_pending_broadcasts",  # RPC method used
                        "data_type": "pending_broadcasts",  # Type of data found
                        "index": i,  # Position in the results
                        "matches": matches,  # What was found
                        "raw_data": json.dumps(broadcast)[
                            :500
                        ],  # First 500 chars of raw data
                        "detection_method": "pending_broadcasts",  # How it was detected
                    }
                    all_transactions.append(transaction)
    else:
        print(f"   ❌ No pending broadcasts found")

    # =====================================================================
    # STEP 9: METHOD 8 - PENDING SWAPS (MONITORING)
    # =====================================================================
    # Test cf_monitoring_pending_swaps with empty parameters
    # This method should show swaps that are pending from monitoring
    print(f"\n🔍 Method 8: Pending Swaps (Monitoring)")
    print("-" * 35)

    # Make RPC call to get pending swaps from monitoring
    pending_swaps = make_rpc_call("cf_monitoring_pending_swaps", [])

    if pending_swaps:
        print(f"   ✅ Found {len(pending_swaps)} pending swaps")

        # Analyze each pending swap for ShapeShift indicators
        for i, swap in enumerate(pending_swaps):
            if isinstance(swap, dict):
                # Search for ShapeShift patterns in the swap data
                matches = search_for_shapeshift_in_data(swap, "pending_swaps", i)

                if matches:
                    print(f"      🎯 Pending Swap {i}: {matches}")

                    # Create a transaction record for this finding
                    transaction = {
                        "timestamp": datetime.now().isoformat(),  # When the search was performed
                        "method": "cf_monitoring_pending_swaps",  # RPC method used
                        "data_type": "pending_swaps",  # Type of data found
                        "index": i,  # Position in the results
                        "matches": matches,  # What was found
                        "raw_data": json.dumps(swap)[
                            :500
                        ],  # First 500 chars of raw data
                        "detection_method": "pending_swaps_monitoring",  # How it was detected
                    }
                    all_transactions.append(transaction)
    else:
        print(f"   ❌ No pending swaps found")

    # =====================================================================
    # STEP 10: COMPREHENSIVE SEARCH SUMMARY
    # =====================================================================
    # Display a summary of all findings and provide analysis
    print(f"\n🎯 Comprehensive Search Summary")
    print("=" * 55)
    print(f"   Total transactions found: {len(all_transactions)}")

    # =====================================================================
    # STEP 11: ANALYZE AND DISPLAY FINDINGS
    # =====================================================================
    if all_transactions:
        # If we found ShapeShift activity, display details
        print(f"\n✅ Found ShapeShift activity in:")
        for tx in all_transactions:
            print(f"   - {tx['method']}: {tx['matches']}")

        # =====================================================================
        # STEP 12: SAVE RESULTS TO CSV
        # =====================================================================
        # Save all findings to a CSV file for further analysis
        csv_file = "chainflip_comprehensive_transactions.csv"

        # Open CSV file for writing with proper encoding
        with open(csv_file, "w", newline="", encoding="utf-8") as file:
            # Define the column headers for the CSV
            writer = csv.DictWriter(
                file,
                fieldnames=[
                    "timestamp",  # When the search was performed
                    "method",  # RPC method used
                    "data_type",  # Type of data found
                    "index",  # Position in the results
                    "matches",  # What was found
                    "raw_data",  # First 500 chars of raw data
                    "detection_method",  # How it was detected
                ],
            )

            # Write the header row
            writer.writeheader()

            # Write all transaction records
            for tx in all_transactions:
                writer.writerow(tx)

        # Log successful save operation
        print(f"\n💾 Saved transactions to: {csv_file}")

    else:
        # =====================================================================
        # STEP 13: NO FINDINGS ANALYSIS
        # =====================================================================
        # If no ShapeShift transactions were found, provide analysis
        print(f"\n⚠️  No ShapeShift transactions found")
        print(f"   This suggests:")
        print(f"   1. Brokers using different addresses than expected")
        print(f"   2. Transactions in different format than expected")
        print(f"   3. Need to check Chainflip explorer for actual format")
        print(f"   4. Brokers might be inactive right now")
        print(f"   5. Different detection method needed")

    # =====================================================================
    # STEP 14: PROVIDE NEXT STEPS
    # =====================================================================
    # Give guidance on what to do next based on the findings
    print(f"\n💡 Next steps:")
    print(f"   1. Check Chainflip explorer for actual transaction format")
    print(f"   2. Look for different broker addresses")
    print(f"   3. Check if brokers use different naming conventions")
    print(f"   4. Try different RPC methods not yet tested")


# =============================================================================
# MAIN EXECUTION BLOCK
# =============================================================================
# This block ensures the script only runs when executed directly
# (not when imported as a module)

if __name__ == "__main__":
    # Run the main function when the script is executed
    main()
