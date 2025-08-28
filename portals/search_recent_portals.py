#!/usr/bin/env python3
"""
Search for recent Portals activity and find transactions that went through ShapeShift
"""

from portals_listener import CSVPortalsListener
from web3 import Web3
from eth_abi import decode

def search_recent_portals_activity():
    """Search for recent Portals activity"""
    
    print("🔍 Searching for Recent Portals Activity")
    print("========================================")
    
    # Initialize the listener
    listener = CSVPortalsListener()
    
    try:
        w3 = listener.chains['ethereum']['w3']
        current_block = w3.eth.block_number
        
        print(f"📊 Current block: {current_block}")
        
        # Search for Portals router activity in recent blocks
        search_blocks = 2000  # Search last 2000 blocks
        print(f"🔍 Searching last {search_blocks} blocks for Portals activity...")
        
        portals_router = "0xbf5A7F3629fB325E2a8453D595AB103465F75E62"
        shapeshift_treasury = "0x90A48D5CF7343B08dA12E067680B4C6dbfE551Be"
        
        # Search in smaller chunks
        chunk_size = 100
        total_logs = 0
        shapeshift_transactions = []
        
        for start_block in range(current_block - search_blocks, current_block, chunk_size):
            end_block = min(start_block + chunk_size, current_block)
            
            try:
                logs = w3.eth.get_logs({
                    "fromBlock": start_block,
                    "toBlock": end_block,
                    "address": portals_router,
                    "topics": []
                })
                
                if logs:
                    total_logs += len(logs)
                    print(f"   Blocks {start_block}-{end_block}: {len(logs)} logs")
                    
                    # Check each log for ShapeShift involvement
                    for log in logs:
                        # Look for Portal events
                        if log['topics'] and len(log['topics']) > 0:
                            if log['topics'][0].hex() == "0x5915121ae705c6baa1bd6698f437ff30eb4b7dbd20e1f7d83c2f1a8be09a1f03":
                                # This is a Portal event, check if ShapeShift is the partner
                                if len(log['topics']) > 3:
                                    partner = "0x" + log['topics'][3].hex()[-40:]
                                    if partner.lower() == shapeshift_treasury.lower():
                                        shapeshift_transactions.append({
                                            'block': log['blockNumber'],
                                            'tx_hash': log['transactionHash'].hex(),
                                            'partner': partner,
                                            'type': 'Portal Event'
                                        })
                                        print(f"     🎯 Found ShapeShift Portal transaction: {log['transactionHash'].hex()}")
                        
                        # Also check for any other events that might involve ShapeShift
                        # Look for Transfer events to ShapeShift treasury
                        if log['topics'] and len(log['topics']) > 0:
                            if log['topics'][0].hex() == "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef":
                                if len(log['topics']) > 2:
                                    to_address = "0x" + log['topics'][2].hex()[-40:]
                                    if to_address.lower() == shapeshift_treasury.lower():
                                        shapeshift_transactions.append({
                                            'block': log['blockNumber'],
                                            'tx_hash': log['transactionHash'].hex(),
                                            'partner': to_address,
                                            'type': 'Treasury Transfer'
                                        })
                                        print(f"     🎯 Found ShapeShift treasury transfer: {log['transactionHash'].hex()}")
                        
            except Exception as e:
                print(f"   ⚠️ Error searching blocks {start_block}-{end_block}: {e}")
                continue
        
        print(f"\n📋 Total Portals logs found: {total_logs}")
        print(f"🎯 ShapeShift-related transactions found: {len(shapeshift_transactions)}")
        
        if shapeshift_transactions:
            print(f"\n🔍 ShapeShift Transactions Found:")
            for tx in shapeshift_transactions:
                print(f"   Block {tx['block']}: {tx['tx_hash']} ({tx['type']})")
                
            # Analyze the most recent one in detail
            if shapeshift_transactions:
                recent_tx = shapeshift_transactions[0]
                print(f"\n🔍 Analyzing recent ShapeShift transaction: {recent_tx['tx_hash']}")
                analyze_transaction_details(recent_tx['tx_hash'], listener)
        
    except Exception as e:
        print(f"❌ Error searching recent activity: {e}")

def analyze_transaction_details(tx_hash, listener):
    """Analyze a specific transaction for details"""
    
    try:
        w3 = listener.chains['ethereum']['w3']
        
        # Get transaction receipt
        receipt = w3.eth.get_transaction_receipt(tx_hash)
        
        print(f"   📊 Transaction Details:")
        print(f"     Block: {receipt['blockNumber']}")
        print(f"     Logs: {len(receipt['logs'])}")
        
        # Look for Portal events
        portal_events = []
        for i, log in enumerate(receipt['logs']):
            if log['address'].lower() == "0xbf5A7F3629fB325E2a8453D595AB103465F75E62".lower():
                if log['topics'] and len(log['topics']) > 0:
                    if log['topics'][0].hex() == "0x5915121ae705c6baa1bd6698f437ff30eb4b7dbd20e1f7d83c2f1a8be09a1f03":
                        portal_events.append((i, log))
        
        if portal_events:
            print(f"     ✅ Found {len(portal_events)} Portal events")
            for log_index, log in portal_events:
                print(f"       Portal event in log {log_index+1}")
                print(f"       Topics: {len(log['topics'])}")
                
                # Try to decode the Portal event
                try:
                    if len(log['topics']) > 3:
                        sender = "0x" + log['topics'][1].hex()[-40:]
                        broadcaster = "0x" + log['topics'][2].hex()[-40:]
                        partner = "0x" + log['topics'][3].hex()[-40:]
                        
                        print(f"       Sender: {sender}")
                        print(f"       Broadcaster: {broadcaster}")
                        print(f"       Partner: {partner}")
                        
                        # Decode the data field
                        if log['data'] and len(log['data']) > 2:
                            try:
                                decoded = decode(
                                    ["address", "uint256", "address", "uint256", "address"],
                                    bytes.fromhex(log['data'][2:])
                                )
                                input_token, input_amount, output_token, output_amount, recipient = decoded
                                
                                print(f"       Input Token: {input_token}")
                                print(f"       Input Amount: {input_amount}")
                                print(f"       Output Token: {output_token}")
                                print(f"       Output Amount: {output_amount}")
                                print(f"       Recipient: {recipient}")
                                
                            except Exception as e:
                                print(f"       Error decoding data: {e}")
                                
                except Exception as e:
                    print(f"       Error processing topics: {e}")
        else:
            print(f"     ℹ️ No Portal events found")
        
        # Look for any transfers to ShapeShift treasury
        shapeshift_treasury = "0x90A48D5CF7343B08dA12E067680B4C6dbfE551Be"
        treasury_transfers = []
        
        for i, log in enumerate(receipt['logs']):
            if log['topics'] and len(log['topics']) > 0:
                if log['topics'][0].hex() == "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef":
                    try:
                        decoded = decode(
                            ["address", "address", "uint256"],
                            bytes.fromhex(log['data'][2:])
                        )
                        from_addr, to_addr, value = decoded
                        
                        if to_addr.lower() == shapeshift_treasury.lower():
                            treasury_transfers.append({
                                'from': from_addr,
                                'to': to_addr,
                                'value': value,
                                'token_address': log['address'],
                                'log_index': i
                            })
                            
                    except Exception as e:
                        continue
        
        if treasury_transfers:
            print(f"     🎯 Found {len(treasury_transfers)} transfers to ShapeShift treasury")
            for transfer in treasury_transfers:
                print(f"       Log {transfer['log_index']+1}: {transfer['value']} from {transfer['from']}")
        else:
            print(f"     ℹ️ No direct transfers to ShapeShift treasury")
            
    except Exception as e:
        print(f"   ❌ Error analyzing transaction: {e}")

if __name__ == "__main__":
    search_recent_portals_activity()
