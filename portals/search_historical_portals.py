#!/usr/bin/env python3
"""
Search for historical Portals transactions and analyze them for affiliate fee patterns
"""

from portals_listener import CSVPortalsListener
from web3 import Web3
import os

def search_historical_portals():
    """Search for historical Portals transactions"""
    
    print("🔍 Searching for Historical Portals Transactions")
    print("===============================================")
    
    # Initialize the listener
    listener = CSVPortalsListener()
    
    # Search in specific historical block ranges where we know Portals activity exists
    historical_ranges = [
        {
            "name": "Block 22774490-22774500 (Known Portals)",
            "chain": "ethereum",
            "start_block": 22774490,
            "end_block": 22774500
        },
        {
            "name": "Block 23230050-23230070 (Known Portals)",
            "chain": "ethereum",
            "start_block": 23230050,
            "end_block": 23230070
        },
        {
            "name": "Block 23240000-23240100 (Recent)",
            "chain": "ethereum",
            "start_block": 23240000,
            "end_block": 23240100
        }
    ]
    
    for range_info in historical_ranges:
        print(f"\n🔍 Searching: {range_info['name']}")
        print(f"   Chain: {range_info['chain']}")
        print(f"   Blocks: {range_info['start_block']} to {range_info['end_block']}")
        
        try:
            # Get events from the specific block range
            events = listener.fetch_portals_events(
                range_info['chain'],
                range_info['start_block'],
                range_info['end_block']
            )
            
            print(f"   📋 Found {len(events)} Portals events")
            
            if events:
                for i, event in enumerate(events):
                    print(f"   Event {i+1}:")
                    print(f"     Tx Hash: {event['tx_hash']}")
                    print(f"     Block: {event['block_number']}")
                    print(f"     Chain: {event['chain']}")
                    print(f"     From: {event['from_address']}")
                    print(f"     To: {event['to_address']}")
                    
                    # Analyze this transaction for affiliate fees
                    analyze_transaction_for_fees(event['tx_hash'], listener)
                    
            else:
                print("   ℹ️ No events found in this range")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

def analyze_transaction_for_fees(tx_hash, listener):
    """Analyze a specific transaction for affiliate fee patterns"""
    
    print(f"     🔍 Analyzing transaction for affiliate fees...")
    
    try:
        w3 = listener.chains['ethereum']['w3']
        
        # Get transaction receipt
        receipt = w3.eth.get_transaction_receipt(tx_hash)
        
        # ShapeShift treasury address
        treasury_address = "0x90A48D5CF7343B08dA12E067680B4C6dbfE551Be"
        
        # Look for transfers to ShapeShift treasury
        treasury_transfers = []
        
        for log in receipt['logs']:
            if log['topics'] and len(log['topics']) > 0:
                # Check if this is a transfer event
                if log['topics'][0].hex() == "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef":
                    try:
                        from eth_abi import decode
                        decoded = decode(
                            ["address", "address", "uint256"],
                            bytes.fromhex(log['data'][2:])
                        )
                        from_addr, to_addr, value = decoded
                        
                        # Check if this is a transfer to treasury
                        if to_addr.lower() == treasury_address.lower():
                            treasury_transfers.append({
                                'from': from_addr,
                                'to': to_addr,
                                'value': value,
                                'token_address': log['address']
                            })
                            
                    except Exception as e:
                        continue
        
        if treasury_transfers:
            print(f"     🎯 Found {len(treasury_transfers)} transfers to ShapeShift treasury!")
            for transfer in treasury_transfers:
                print(f"       From: {transfer['from']}")
                print(f"       To: {transfer['to']}")
                print(f"       Value: {transfer['value']}")
                print(f"       Token: {transfer['token_address']}")
                
                # Try to get token symbol
                try:
                    token_contract = w3.eth.contract(
                        address=transfer['token_address'],
                        abi=[{"constant": True, "inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "type": "function"}]
                    )
                    symbol = token_contract.functions.symbol().call()
                    print(f"       Token Symbol: {symbol}")
                except:
                    print(f"       Token Symbol: Unknown")
                
                print()
        else:
            print(f"     ℹ️ No direct transfers to ShapeShift treasury found")
            
            # Look for any token transfers in the transaction
            print(f"     🔍 Looking for other token transfers...")
            token_transfers = []
            
            for log in receipt['logs']:
                if log['topics'] and len(log['topics']) > 0:
                    if log['topics'][0].hex() == "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef":
                        try:
                            from eth_abi import decode
                            decoded = decode(
                                ["address", "address", "uint256"],
                                bytes.fromhex(log['data'][2:])
                            )
                            from_addr, to_addr, value = decoded
                            
                            token_transfers.append({
                                'from': from_addr,
                                'to': to_addr,
                                'value': value,
                                'token_address': log['address']
                            })
                            
                        except Exception as e:
                            continue
            
            if token_transfers:
                print(f"     📊 Found {len(token_transfers)} token transfers in transaction")
                for i, transfer in enumerate(token_transfers[:5]):  # Show first 5
                    print(f"       Transfer {i+1}: {transfer['from'][:10]}... → {transfer['to'][:10]}...")
                    print(f"         Value: {transfer['value']}")
                    print(f"         Token: {transfer['token_address']}")
                    
                    # Try to get token symbol
                    try:
                        token_contract = w3.eth.contract(
                            address=transfer['token_address'],
                            abi=[{"constant": True, "inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "type": "function"}]
                        )
                        symbol = token_contract.functions.symbol().call()
                        print(f"         Token Symbol: {symbol}")
                    except:
                        print(f"         Token Symbol: Unknown")
                    
                    print()
            else:
                print(f"     ℹ️ No token transfers found")
                
    except Exception as e:
        print(f"     ❌ Error analyzing transaction: {e}")

def search_portals_router_activity():
    """Search for any activity involving the Portals router"""
    
    print("\n🔍 Searching for Portals Router Activity")
    print("========================================")
    
    listener = CSVPortalsListener()
    
    # Portals router address
    portals_router = "0xbf5A7F3629fB325E2a8453D595AB103465F75E62"
    
    print(f"🎯 Portals Router: {portals_router}")
    
    try:
        w3 = listener.chains['ethereum']['w3']
        current_block = w3.eth.block_number
        
        print(f"📊 Current block: {current_block}")
        
        # Search recent blocks for any transactions involving Portals router
        search_blocks = 500  # Search last 500 blocks
        
        print(f"🔍 Searching last {search_blocks} blocks for Portals router activity...")
        
        portals_activity = []
        
        # Search in smaller chunks
        chunk_size = 50
        for start_block in range(current_block - search_blocks, current_block, chunk_size):
            end_block = min(start_block + chunk_size, current_block)
            
            try:
                # Get logs from Portals router
                logs = w3.eth.get_logs({
                    "fromBlock": start_block,
                    "toBlock": end_block,
                    "address": portals_router,
                    "topics": []
                })
                
                if logs:
                    for log in logs:
                        portals_activity.append({
                            'block': log['blockNumber'],
                            'tx_hash': log['transactionHash'].hex(),
                            'topics': len(log['topics'])
                        })
                        
            except Exception as e:
                print(f"   ⚠️ Error searching blocks {start_block}-{end_block}: {e}")
                continue
        
        print(f"📋 Found {len(portals_activity)} Portals router interactions")
        
        if portals_activity:
            print(f"   Recent activity:")
            for activity in portals_activity[:10]:  # Show first 10
                print(f"     Block {activity['block']}: {activity['tx_hash']} ({activity['topics']} topics)")
                
                # Analyze one recent transaction in detail
                if len(portals_activity) > 0:
                    recent_tx = portals_activity[0]
                    print(f"\n🔍 Analyzing recent transaction: {recent_tx['tx_hash']}")
                    analyze_transaction_for_fees(recent_tx['tx_hash'], listener)
        
    except Exception as e:
        print(f"❌ Error searching Portals router activity: {e}")

if __name__ == "__main__":
    search_historical_portals()
    search_portals_router_activity()
