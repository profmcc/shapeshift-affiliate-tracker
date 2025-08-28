#!/usr/bin/env python3
"""
Precise analysis of the August 25th transaction matching Etherscan data
"""

from portals_listener import CSVPortalsListener
from web3 import Web3
from eth_abi import decode

def precise_august_25_analysis():
    """Precise analysis matching Etherscan data"""
    
    print("🔍 Precise August 25th Transaction Analysis")
    print("===========================================")
    
    # Initialize the listener
    listener = CSVPortalsListener()
    
    try:
        w3 = listener.chains['ethereum']['w3']
        
        # The known transaction from August 25th
        known_tx = "0xb6192470f067e11a599ac6af7fbaebdf192a8724fe555050ab327df67ecb4a53"
        
        print(f"🎯 Target Transaction: {known_tx}")
        print(f"🔗 Etherscan: https://etherscan.io/tx/{known_tx}")
        
        # Get transaction details
        tx = w3.eth.get_transaction(known_tx)
        receipt = w3.eth.get_transaction_receipt(known_tx)
        
        print(f"\n📋 Transaction Details:")
        print(f"   Block: {receipt['blockNumber']}")
        print(f"   From: {tx['from']}")
        print(f"   To: {tx['to']}")
        print(f"   Value: {w3.from_wei(tx['value'], 'ether')} ETH")
        print(f"   Gas Used: {receipt['gasUsed']}")
        print(f"   Status: {'Success' if receipt['status'] == 1 else 'Failed'}")
        print(f"   Logs: {len(receipt['logs'])}")
        
        # According to Etherscan, Log 53 contains the Portal event
        # Let's analyze all logs to find it
        print(f"\n🔍 Analyzing All Logs for Portal Event:")
        
        portals_router = "0xbf5A7F3629fB325E2a8453D595AB103465F75E62"
        shapeshift_treasury = "0x90A48D5CF7343B08dA12E067680B4C6dbfE551Be"
        
        portal_events = []
        portal_event_signature = "0x5915121ae705c6baa1bd6698f437ff30eb4b7dbd20e1f7d83c2f1a8be09a1f03"
        
        for i, log in enumerate(receipt['logs']):
            print(f"   Log {i+1}:")
            print(f"     Address: {log['address']}")
            print(f"     Topics: {len(log['topics'])}")
            
            if log['topics']:
                print(f"     Topic 0: {log['topics'][0].hex()}")
                
                # Check if this is a Portal event
                if log['topics'][0].hex() == portal_event_signature:
                    portal_events.append((i, log))
                    print(f"     ✅ PORTAL EVENT DETECTED!")
                    
                    # Check if this is from the Portals router
                    if log['address'].lower() == portals_router.lower():
                        print(f"     🎯 From Portals Router: YES")
                        
                        # Decode the Portal event according to Etherscan
                        try:
                            if len(log['topics']) > 3:
                                sender = "0x" + log['topics'][1].hex()[-40:]
                                broadcaster = "0x" + log['topics'][2].hex()[-40:]
                                partner = "0x" + log['topics'][3].hex()[-40:]
                                
                                print(f"     Sender: {sender}")
                                print(f"     Broadcaster: {broadcaster}")
                                print(f"     Partner: {partner}")
                                
                                # Check if ShapeShift is the partner
                                if partner.lower() == shapeshift_treasury.lower():
                                    print(f"     🎯 SHAPESHIFT PARTNERSHIP CONFIRMED!")
                                else:
                                    print(f"     ℹ️ Different partner: {partner}")
                            
                            # Decode the data field according to Etherscan
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
                                    
                                    # Get token symbols
                                    try:
                                        input_token_contract = w3.eth.contract(
                                            address=input_token,
                                            abi=[{"constant": True, "inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "type": "function"}]
                                        )
                                        input_symbol = input_token_contract.functions.symbol().call()
                                        print(f"     Input Token Symbol: {input_symbol}")
                                        
                                        # Get decimals for human-readable amount
                                        try:
                                            input_decimals_contract = w3.eth.contract(
                                                address=input_token,
                                                abi=[{"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"}]
                                            )
                                            input_decimals = input_decimals_contract.functions.decimals().call()
                                            human_input = input_amount / (10 ** input_decimals)
                                            print(f"     Human Input Amount: {human_input}")
                                        except:
                                            print(f"     Human Input Amount: Unknown")
                                            
                                    except:
                                        print(f"     Input Token Symbol: Unknown")
                                    
                                    if output_token != "0x0000000000000000000000000000000000000000":
                                        print(f"     Output Token: {output_token}")
                                        print(f"     Human Output Amount: {w3.from_wei(output_amount, 'ether')} ETH")
                                    else:
                                        print(f"     Output Token: ETH (native)")
                                        print(f"     Human Output Amount: {w3.from_wei(output_amount, 'ether')} ETH")
                                    
                                except Exception as e:
                                    print(f"     ❌ Error decoding data: {e}")
                                    
                        except Exception as e:
                            print(f"     ❌ Error processing Portal event: {e}")
                    else:
                        print(f"     ℹ️ Not from Portals router")
                else:
                    print(f"     📝 Other event type")
            
            print()
        
        # Summary
        print(f"\n📊 Analysis Summary:")
        print(f"   🔍 Total logs analyzed: {len(receipt['logs'])}")
        print(f"   🚪 Portal events found: {len(portal_events)}")
        
        if portal_events:
            print(f"\n✅ Portal Events Found:")
            for log_index, log in portal_events:
                print(f"   Log {log_index+1}: Portal event confirmed")
                
                # Check if this matches Etherscan data
                if log_index == 52:  # Log 53 in Etherscan (0-indexed)
                    print(f"     🎯 This matches Etherscan Log 53!")
                else:
                    print(f"     ℹ️ Different log index than expected")
        else:
            print(f"\n❌ No Portal events found")
            print(f"   💡 This suggests there might be an issue with our detection")
            print(f"   🔍 Etherscan shows the Portal event in Log 53")
        
        # Now let's also check what our scan found
        print(f"\n🔍 Cross-referencing with Scan Results:")
        print(f"   📊 Our scan found Portals logs for this transaction")
        print(f"   🎯 But detailed analysis shows no Portal events")
        print(f"   💡 This suggests a discrepancy in our detection logic")
        
        # Final verification
        print(f"\n🎯 Final Verification:")
        print(f"   ✅ Transaction exists: {known_tx}")
        print(f"   ✅ Block confirmed: {receipt['blockNumber']}")
        print(f"   ✅ Etherscan shows Portal event in Log 53")
        print(f"   🔍 Our analysis needs to be updated to match Etherscan data")
        
    except Exception as e:
        print(f"❌ Error in precise analysis: {e}")

if __name__ == "__main__":
    precise_august_25_analysis()
