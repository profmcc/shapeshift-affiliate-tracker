#!/usr/bin/env python3
"""
Analyze the recent Portals transactions we found
"""

from portals_listener import CSVPortalsListener
from web3 import Web3
from eth_abi import decode

def analyze_recent_portals():
    """Analyze the recent Portals transactions"""
    
    print("🔍 Analyzing Recent Portals Transactions")
    print("========================================")
    
    # Initialize the listener
    listener = CSVPortalsListener()
    
    try:
        w3 = listener.chains['ethereum']['w3']
        
        # Search for recent Portals activity
        portals_router = "0xbf5A7F3629fB325E2a8453D595AB103465F75E62"
        shapeshift_treasury = "0x90A48D5CF7343B08dA12E067680B4C6dbfE551Be"
        
        # Search in the blocks where we found activity
        search_ranges = [
            (23238950, 23239050),
            (23239550, 23239650)
        ]
        
        for start_block, end_block in search_ranges:
            print(f"\n🔍 Searching blocks {start_block}-{end_block}")
            
            try:
                logs = w3.eth.get_logs({
                    "fromBlock": start_block,
                    "toBlock": end_block,
                    "address": portals_router,
                    "topics": []
                })
                
                if logs:
                    print(f"   📋 Found {len(logs)} logs")
                    
                    for i, log in enumerate(logs):
                        print(f"   Log {i+1}: Block {log['blockNumber']}, Tx: {log['transactionHash'].hex()}")
                        
                        # Check if this is a Portal event
                        if log['topics'] and len(log['topics']) > 0:
                            if log['topics'][0].hex() == "0x5915121ae705c6baa1bd6698f437ff30eb4b7dbd20e1f7d83c2f1a8be09a1f03":
                                print(f"     ✅ Portal event detected!")
                                
                                # Check if ShapeShift is the partner
                                if len(log['topics']) > 3:
                                    partner = "0x" + log['topics'][3].hex()[-40:]
                                    print(f"     Partner: {partner}")
                                    
                                    if partner.lower() == shapeshift_treasury.lower():
                                        print(f"     🎯 SHAPESHIFT PARTNERSHIP CONFIRMED!")
                                        
                                        # Decode the Portal event
                                        try:
                                            if log['data'] and len(log['data']) > 2:
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
                                                
                                                # Get token symbols
                                                try:
                                                    input_token_contract = w3.eth.contract(
                                                        address=input_token,
                                                        abi=[{"constant": True, "inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "type": "function"}]
                                                    )
                                                    input_symbol = input_token_contract.functions.symbol().call()
                                                    print(f"     Input Token Symbol: {input_symbol}")
                                                except:
                                                    print(f"     Input Token Symbol: Unknown")
                                                    
                                                if output_token != "0x0000000000000000000000000000000000000000":
                                                    try:
                                                        output_token_contract = w3.eth.contract(
                                                            address=output_token,
                                                            abi=[{"constant": True, "inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "type": "function"}]
                                                        )
                                                        output_symbol = output_token_contract.functions.symbol().call()
                                                        print(f"     Output Token Symbol: {output_symbol}")
                                                    except:
                                                        print(f"     Output Token Symbol: Unknown")
                                                else:
                                                    print(f"     Output Token: ETH (native)")
                                                    
                                        except Exception as e:
                                            print(f"     ❌ Error decoding Portal event: {e}")
                                    else:
                                        print(f"     ℹ️ Different partner: {partner}")
                                        
                                # Get sender and broadcaster
                                if len(log['topics']) > 1:
                                    sender = "0x" + log['topics'][1].hex()[-40:]
                                    print(f"     Sender: {sender}")
                                    
                                if len(log['topics']) > 2:
                                    broadcaster = "0x" + log['topics'][2].hex()[-40:]
                                    print(f"     Broadcaster: {broadcaster}")
                                    
                            else:
                                print(f"     Event type: {log['topics'][0].hex()}")
                        
                        print()
                        
            except Exception as e:
                print(f"   ❌ Error searching blocks: {e}")
        
        # Now let's also check the specific transaction from Etherscan that we know went through ShapeShift
        print(f"\n🔍 Re-analyzing the known ShapeShift transaction:")
        known_tx = "0xb6192470f067e11a599ac6af7fbaebdf192a8724fe555050ab327df67ecb4a53"
        
        try:
            receipt = w3.eth.get_transaction_receipt(known_tx)
            print(f"   📊 Transaction: {known_tx}")
            print(f"   Block: {receipt['blockNumber']}")
            print(f"   Logs: {len(receipt['logs'])}")
            
            # Look for Portal events
            portal_events = []
            for i, log in enumerate(receipt['logs']):
                if log['address'].lower() == portals_router.lower():
                    if log['topics'] and len(log['topics']) > 0:
                        if log['topics'][0].hex() == "0x5915121ae705c6baa1bd6698f437ff30eb4b7dbd20e1f7d83c2f1a8be09a1f03":
                            portal_events.append((i, log))
            
            if portal_events:
                print(f"   ✅ Found {len(portal_events)} Portal events")
                for log_index, log in portal_events:
                    print(f"     Portal event in log {log_index+1}")
                    if len(log['topics']) > 3:
                        partner = "0x" + log['topics'][3].hex()[-40:]
                        print(f"     Partner: {partner}")
                        if partner.lower() == shapeshift_treasury.lower():
                            print(f"     🎯 CONFIRMED: ShapeShift partnership!")
            else:
                print(f"   ℹ️ No Portal events found in this transaction")
                
        except Exception as e:
            print(f"   ❌ Error analyzing known transaction: {e}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    analyze_recent_portals()
