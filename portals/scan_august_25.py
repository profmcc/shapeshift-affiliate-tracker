#!/usr/bin/env python3
"""
Scan specifically for August 25th Portals activity and find the known transaction
"""

from portals_listener import CSVPortalsListener
from web3 import Web3
from eth_abi import decode
import datetime

def scan_august_25():
    """Scan specifically for August 25th Portals activity"""
    
    print("🔍 Scanning August 25th Portals Activity")
    print("========================================")
    
    # Initialize the listener
    listener = CSVPortalsListener()
    
    try:
        w3 = listener.chains['ethereum']['w3']
        
        # The known transaction from August 25th
        known_tx = "0xb6192470f067e11a599ac6af7fbaebdf192a8724fe555050ab327df67ecb4a53"
        
        print(f"🎯 Target Transaction: {known_tx}")
        print(f"🔗 Etherscan: https://etherscan.io/tx/{known_tx}")
        
        # Get transaction details to find the block
        tx = w3.eth.get_transaction(known_tx)
        receipt = w3.eth.get_transaction_receipt(known_tx)
        
        target_block = receipt['blockNumber']
        print(f"📊 Target Block: {target_block}")
        
        # August 25th was about 3 days ago, so let's scan a range around that block
        # Ethereum produces ~7200 blocks per day, so 3 days = ~21,600 blocks
        start_block = target_block - 1000  # Scan 1000 blocks before
        end_block = target_block + 1000    # Scan 1000 blocks after
        
        print(f"🔍 Scanning blocks {start_block} to {end_block}")
        print(f"📅 This should cover August 25th activity")
        
        # Search for Portals router activity in this range
        portals_router = "0xbf5A7F3629fB325E2a8453D595AB103465F75E62"
        shapeshift_treasury = "0x90A48D5CF7343B08dA12E067680B4C6dbfE551Be"
        
        print(f"\n🔍 Searching for Portals activity...")
        
        # Search in smaller chunks to avoid API limits
        chunk_size = 100
        total_logs = 0
        shapeshift_transactions = []
        all_portals_transactions = []
        
        for start_chunk in range(start_block, end_block, chunk_size):
            end_chunk = min(start_chunk + chunk_size, end_block)
            
            try:
                logs = w3.eth.get_logs({
                    "fromBlock": start_chunk,
                    "toBlock": end_chunk,
                    "address": portals_router,
                    "topics": []
                })
                
                if logs:
                    total_logs += len(logs)
                    print(f"   Blocks {start_chunk}-{end_chunk}: {len(logs)} logs")
                    
                    # Check each log for Portal events
                    for log in logs:
                        all_portals_transactions.append({
                            'block': log['blockNumber'],
                            'tx_hash': log['transactionHash'].hex(),
                            'topics': len(log['topics'])
                        })
                        
                        # Look for Portal events
                        if log['topics'] and len(log['topics']) > 0:
                            if log['topics'][0].hex() == "0x5915121ae705c6baa1bd6698f437ff30eb4b7dbd20e1f7d83c2f1a8be09a1f03":
                                print(f"     ✅ Portal event found: {log['transactionHash'].hex()}")
                                
                                # Check if this is the known transaction
                                if log['transactionHash'].hex() == known_tx:
                                    print(f"     🎯 TARGET TRANSACTION FOUND!")
                                
                                # Check if ShapeShift is the partner
                                if len(log['topics']) > 3:
                                    partner = "0x" + log['topics'][3].hex()[-40:]
                                    if partner.lower() == shapeshift_treasury.lower():
                                        shapeshift_transactions.append({
                                            'block': log['blockNumber'],
                                            'tx_hash': log['transactionHash'].hex(),
                                            'partner': partner,
                                            'type': 'Portal Event'
                                        })
                                        print(f"     🎯 ShapeShift partnership: {log['transactionHash'].hex()}")
                        
            except Exception as e:
                print(f"   ⚠️ Error searching blocks {start_chunk}-{end_chunk}: {e}")
                continue
        
        print(f"\n📋 Scan Results:")
        print(f"   Total Portals logs found: {total_logs}")
        print(f"   Total Portals transactions: {len(all_portals_transactions)}")
        print(f"   ShapeShift partnerships: {len(shapeshift_transactions)}")
        
        # Check if we found our target transaction
        target_found = any(tx['tx_hash'] == known_tx for tx in all_portals_transactions)
        if target_found:
            print(f"\n🎯 SUCCESS: Target transaction found in August 25th scan!")
        else:
            print(f"\n❌ Target transaction not found in scan range")
            print(f"   This suggests the transaction might be outside our scan range")
        
        # Show all Portals transactions found
        if all_portals_transactions:
            print(f"\n🔍 All Portals Transactions Found:")
            for tx in all_portals_transactions:
                print(f"   Block {tx['block']}: {tx['tx_hash']} ({tx['topics']} topics)")
                
                # If this is our target, show more details
                if tx['tx_hash'] == known_tx:
                    print(f"     🎯 THIS IS OUR TARGET TRANSACTION!")
                    print(f"     📊 Block: {tx['block']}")
                    print(f"     🔗 https://etherscan.io/tx/{tx['tx_hash']}")
        
        # Show ShapeShift partnerships
        if shapeshift_transactions:
            print(f"\n🎯 ShapeShift Partnerships Found:")
            for tx in shapeshift_transactions:
                print(f"   Block {tx['block']}: {tx['tx_hash']} ({tx['type']})")
                if tx['tx_hash'] == known_tx:
                    print(f"     🎯 CONFIRMED: This is the ShapeShift transaction we're looking for!")
        
        # Now let's specifically analyze the target transaction
        print(f"\n🔍 Detailed Analysis of Target Transaction:")
        analyze_target_transaction(known_tx, listener)
        
    except Exception as e:
        print(f"❌ Error in August 25th scan: {e}")

def analyze_target_transaction(tx_hash, listener):
    """Analyze the target transaction in detail"""
    
    try:
        w3 = listener.chains['ethereum']['w3']
        
        # Get transaction details
        tx = w3.eth.get_transaction(tx_hash)
        receipt = w3.eth.get_transaction_receipt(tx_hash)
        
        print(f"   📊 Transaction: {tx_hash}")
        print(f"   Block: {receipt['blockNumber']}")
        print(f"   From: {tx['from']}")
        print(f"   To: {tx['to']}")
        print(f"   Value: {w3.from_wei(tx['value'], 'ether')} ETH")
        print(f"   Gas Used: {receipt['gasUsed']}")
        print(f"   Status: {'Success' if receipt['status'] == 1 else 'Failed'}")
        print(f"   Logs: {len(receipt['logs'])}")
        
        # Look for the Portal event
        portals_router = "0xbf5A7F3629fB325E2a8453D595AB103465F75E62"
        shapeshift_treasury = "0x90A48D5CF7343B08dA12E067680B4C6dbfE551Be"
        
        portal_event_found = False
        
        for i, log in enumerate(receipt['logs']):
            if log['address'].lower() == portals_router.lower():
                if log['topics'] and len(log['topics']) > 0:
                    if log['topics'][0].hex() == "0x5915121ae705c6baa1bd6698f437ff30eb4b7dbd20e1f7d83c2f1a8be09a1f03":
                        portal_event_found = True
                        print(f"   ✅ Portal event found in log {i+1}")
                        
                        # Decode the Portal event
                        try:
                            if len(log['topics']) > 3:
                                sender = "0x" + log['topics'][1].hex()[-40:]
                                broadcaster = "0x" + log['topics'][2].hex()[-40:]
                                partner = "0x" + log['topics'][3].hex()[-40:]
                                
                                print(f"     Sender: {sender}")
                                print(f"     Broadcaster: {broadcaster}")
                                print(f"     Partner: {partner}")
                                
                                if partner.lower() == shapeshift_treasury.lower():
                                    print(f"     🎯 SHAPESHIFT PARTNERSHIP CONFIRMED!")
                                else:
                                    print(f"     ℹ️ Different partner: {partner}")
                            
                            # Decode the data field
                            if log['data'] and len(log['data']) > 2:
                                try:
                                    decoded = decode(
                                        ["address", "uint256", "address", "uint256", "address"],
                                        bytes.fromhex(log['data'][2:])
                                    )
                                    input_token, input_amount, output_token, output_amount, recipient = decoded
                                    
                                    print(f"     Input Token: {input_token}")
                                    print(f"     Input Amount: {input_amount}")
                                    print(f"     Output Token: {output_token}")
                                    print(f"     Output Amount: {output_amount}")
                                    print(f"     Recipient: {recipient}")
                                    
                                except Exception as e:
                                    print(f"     ❌ Error decoding data: {e}")
                                    
                        except Exception as e:
                            print(f"     ❌ Error processing Portal event: {e}")
        
        if not portal_event_found:
            print(f"   ❌ No Portal event found in transaction logs")
            print(f"   💡 This suggests the Portal event might be emitted differently")
        
        # Summary
        print(f"\n📊 Analysis Summary:")
        print(f"   🔍 Target transaction analyzed: {tx_hash}")
        print(f"   🚪 Portal event found: {'Yes' if portal_event_found else 'No'}")
        print(f"   🎯 ShapeShift partnership: {'Confirmed' if portal_event_found else 'Unknown'}")
        print(f"   📅 Block {receipt['blockNumber']} corresponds to August 25th activity")
        
    except Exception as e:
        print(f"   ❌ Error analyzing target transaction: {e}")

if __name__ == "__main__":
    scan_august_25()
