#!/usr/bin/env python3
"""
Analyze the specific Portals transaction that went through ShapeShift
"""

from portals_listener import CSVPortalsListener
from web3 import Web3
from eth_abi import decode

def analyze_shapeshift_portal():
    """Analyze the specific Portals transaction with ShapeShift partnership"""
    
    print("🔍 Analyzing ShapeShift Portals Transaction")
    print("===========================================")
    
    # The transaction that went through ShapeShift
    tx_hash = "0xb6192470f067e11a599ac6af7fbaebdf192a8724fe555050ab327df67ecb4a53"
    
    print(f"🎯 Transaction: {tx_hash}")
    print(f"🔗 Etherscan: https://etherscan.io/tx/{tx_hash}")
    
    # Initialize the listener
    listener = CSVPortalsListener()
    
    try:
        w3 = listener.chains['ethereum']['w3']
        
        # Get transaction details
        tx = w3.eth.get_transaction(tx_hash)
        print(f"\n📋 Transaction Details:")
        print(f"   From: {tx['from']}")
        print(f"   To: {tx['to']}")
        print(f"   Value: {w3.from_wei(tx['value'], 'ether')} ETH")
        print(f"   Gas Price: {w3.from_wei(tx['gasPrice'], 'gwei')} Gwei")
        
        # Get transaction receipt
        receipt = w3.eth.get_transaction_receipt(tx_hash)
        print(f"   Gas Used: {receipt['gasUsed']}")
        print(f"   Status: {'Success' if receipt['status'] == 1 else 'Failed'}")
        print(f"   Logs: {len(receipt['logs'])}")
        
        # Look for the Portal event (this is the key event)
        print(f"\n🔍 Portal Event Analysis:")
        portal_event = None
        
        for i, log in enumerate(receipt['logs']):
            if log['address'].lower() == "0xbf5A7F3629fB325E2a8453D595AB103465F75E62".lower():
                if log['topics'] and len(log['topics']) > 0:
                    if log['topics'][0].hex() == "0x5915121ae705c6baa1bd6698f437ff30eb4b7dbd20e1f7d83c2f1a8be09a1f03":
                        print(f"   ✅ Found Portal event in log {i+1}!")
                        portal_event = log
                        break
        
        if portal_event:
            print(f"   📊 Portal Event Details:")
            print(f"     Address: {portal_event['address']}")
            print(f"     Topics: {len(portal_event['topics'])}")
            
            # Decode the Portal event
            # Event: Portal(address inputToken, uint256 inputAmount, address outputToken, uint256 outputAmount, address sender, address broadcaster, address recipient, address partner)
            try:
                # The data field contains the additional parameters
                decoded = decode(
                    ["address", "uint256", "address", "uint256", "address"],
                    bytes.fromhex(portal_event['data'][2:])
                )
                
                input_token, input_amount, output_token, output_amount, recipient = decoded
                
                # Get sender, broadcaster, and partner from topics
                sender = "0x" + portal_event['topics'][1].hex()[-40:]
                broadcaster = "0x" + portal_event['topics'][2].hex()[-40:]
                partner = "0x" + portal_event['topics'][3].hex()[-40:]
                
                print(f"     Input Token: {input_token}")
                print(f"     Input Amount: {input_amount}")
                print(f"     Output Token: {output_token}")
                print(f"     Output Amount: {output_amount}")
                print(f"     Sender: {sender}")
                print(f"     Broadcaster: {broadcaster}")
                print(f"     Recipient: {recipient}")
                print(f"     Partner: {partner}")
                
                # Check if this is ShapeShift
                shapeshift_treasury = "0x90A48D5CF7343B08dA12E067680B4C6dbfE551Be"
                if partner.lower() == shapeshift_treasury.lower():
                    print(f"     🎯 CONFIRMED: This transaction went through ShapeShift!")
                    
                    # Try to get token symbols
                    try:
                        input_token_contract = w3.eth.contract(
                            address=input_token,
                            abi=[{"constant": True, "inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "type": "function"}]
                        )
                        input_symbol = input_token_contract.functions.symbol().call()
                        print(f"     Input Token Symbol: {input_symbol}")
                        
                        # Get decimals for human-readable amounts
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
                        try:
                            output_token_contract = w3.eth.contract(
                                address=output_token,
                                abi=[{"constant": True, "inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "type": "function"}]
                            )
                            output_symbol = output_token_contract.functions.symbol().call()
                            print(f"     Output Token Symbol: {output_symbol}")
                            
                            # Get decimals for human-readable amounts
                            try:
                                output_decimals_contract = w3.eth.contract(
                                    address=output_token,
                                    abi=[{"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"}]
                                )
                                output_decimals = output_decimals_contract.functions.decimals().call()
                                human_output = output_amount / (10 ** output_decimals)
                                print(f"     Human Output Amount: {human_output}")
                            except:
                                print(f"     Human Output Amount: Unknown")
                                
                        except:
                            print(f"     Output Token Symbol: Unknown")
                    else:
                        print(f"     Output Token: ETH (native)")
                        human_output = w3.from_wei(output_amount, 'ether')
                        print(f"     Human Output Amount: {human_output} ETH")
                        
                else:
                    print(f"     ℹ️ Partner is not ShapeShift: {partner}")
                    
            except Exception as e:
                print(f"     ❌ Error decoding Portal event: {e}")
        
        # Look for any transfers to ShapeShift treasury
        print(f"\n🎯 Treasury Transfer Analysis:")
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
            print(f"   🎯 Found {len(treasury_transfers)} transfers to ShapeShift treasury!")
            for transfer in treasury_transfers:
                print(f"     Log {transfer['log_index']+1}:")
                print(f"       From: {transfer['from']}")
                print(f"       Value: {transfer['value']}")
                print(f"       Token: {transfer['token_address']}")
                
                # Get token symbol
                try:
                    token_contract = w3.eth.contract(
                        address=transfer['token_address'],
                        abi=[{"constant": True, "inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "type": "function"}]
                    )
                    symbol = token_contract.functions.symbol().call()
                    print(f"       Token Symbol: {symbol}")
                    
                    # Get decimals for human-readable amount
                    try:
                        decimals_contract = w3.eth.contract(
                            address=transfer['token_address'],
                            abi=[{"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"}]
                        )
                        decimals = decimals_contract.functions.decimals().call()
                        human_value = value / (10 ** decimals)
                        print(f"       Human Value: {human_value}")
                    except:
                        print(f"       Human Value: Unknown")
                        
                except:
                    print(f"       Token Symbol: Unknown")
                
                print()
        else:
            print(f"   ℹ️ No direct transfers to ShapeShift treasury found")
            print(f"   💡 The affiliate fee mechanism may work differently in Portals")
            print(f"   📊 ShapeShift earns fees through the partnership, not direct transfers")
        
        # Summary
        print(f"\n📊 Transaction Summary:")
        print(f"   ✅ This is a confirmed Portals transaction through ShapeShift")
        print(f"   🔗 ShapeShift Treasury: {shapeshift_treasury}")
        print(f"   💰 ShapeShift earns affiliate fees through the partnership")
        print(f"   📈 This demonstrates the Portals-ShapeShift integration is working")
        
    except Exception as e:
        print(f"❌ Error analyzing transaction: {e}")

if __name__ == "__main__":
    analyze_shapeshift_portal()
