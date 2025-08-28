#!/usr/bin/env python3
"""
Analyze Portal events in detail to see if any went through ShapeShift
"""

from portals_listener import CSVPortalsListener
from web3 import Web3
from eth_abi import decode

def analyze_portal_events():
    """Analyze Portal events in detail"""
    
    print("🔍 Analyzing Portal Events in Detail")
    print("====================================")
    
    # Initialize the listener
    listener = CSVPortalsListener()
    
    try:
        w3 = listener.chains['ethereum']['w3']
        
        # The recent Portals transactions we found
        recent_transactions = [
            "0xf8b5b93b410797234c7a7e429e2a17ed00b4892c56337fbc1fc3fb9071fdf2fb",
            "0x1ea23d5023ddf8fd1f33137afee58b9b2c455568c83d3a81867f591cc8d58f48",
            "0xaaacd7533e125a4557a65191c527651fd570cfeb099f1b9f06f4ecdd8e2cb376",
            "0x0a1b682cd86649b18f700f7901ed84d47cc8e48e10cc36be45e7d0b30665cdc3"
        ]
        
        shapeshift_treasury = "0x90A48D5CF7343B08dA12E067680B4C6dbfE551Be"
        
        for i, tx_hash in enumerate(recent_transactions):
            print(f"\n🔍 Analyzing Transaction {i+1}: {tx_hash}")
            print(f"🔗 Etherscan: https://etherscan.io/tx/{tx_hash}")
            
            try:
                # Get transaction receipt
                receipt = w3.eth.get_transaction_receipt(tx_hash)
                print(f"   📊 Block: {receipt['blockNumber']}")
                print(f"   📋 Logs: {len(receipt['logs'])}")
                
                # Look for Portal events
                portal_events = []
                for j, log in enumerate(receipt['logs']):
                    if log['address'].lower() == "0xbf5A7F3629fB325E2a8453D595AB103465F75E62".lower():
                        if log['topics'] and len(log['topics']) > 0:
                            if log['topics'][0].hex() == "0x5915121ae705c6baa1bd6698f437ff30eb4b7dbd20e1f7d83c2f1a8be09a1f03":
                                portal_events.append((j, log))
                
                if portal_events:
                    print(f"   ✅ Found {len(portal_events)} Portal events")
                    
                    for log_index, log in portal_events:
                        print(f"     Portal event in log {log_index+1}:")
                        print(f"       Address: {log['address']}")
                        print(f"       Topics: {len(log['topics'])}")
                        
                        # Decode the Portal event
                        try:
                            if len(log['topics']) > 3:
                                sender = "0x" + log['topics'][1].hex()[-40:]
                                broadcaster = "0x" + log['topics'][2].hex()[-40:]
                                partner = "0x" + log['topics'][3].hex()[-40:]
                                
                                print(f"       Sender: {sender}")
                                print(f"       Broadcaster: {broadcaster}")
                                print(f"       Partner: {partner}")
                                
                                # Check if this is ShapeShift
                                if partner.lower() == shapeshift_treasury.lower():
                                    print(f"       🎯 SHAPESHIFT PARTNERSHIP CONFIRMED!")
                                else:
                                    print(f"       ℹ️ Different partner: {partner}")
                                
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
                                        
                                        # Get token symbols
                                        try:
                                            input_token_contract = w3.eth.contract(
                                                address=input_token,
                                                abi=[{"constant": True, "inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "type": "function"}]
                                            )
                                            input_symbol = input_token_contract.functions.symbol().call()
                                            print(f"       Input Token Symbol: {input_symbol}")
                                            
                                            # Get decimals for human-readable amount
                                            try:
                                                input_decimals_contract = w3.eth.contract(
                                                    address=input_token,
                                                    abi=[{"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"}]
                                                )
                                                input_decimals = input_decimals_contract.functions.decimals().call()
                                                human_input = input_amount / (10 ** input_decimals)
                                                print(f"       Human Input Amount: {human_input}")
                                            except:
                                                print(f"       Human Input Amount: Unknown")
                                                
                                        except:
                                            print(f"       Input Token Symbol: Unknown")
                                        
                                        if output_token != "0x0000000000000000000000000000000000000000":
                                            try:
                                                output_token_contract = w3.eth.contract(
                                                    address=output_token,
                                                    abi=[{"constant": True, "inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "type": "function"}]
                                                )
                                                output_symbol = output_token_contract.functions.symbol().call()
                                                print(f"       Output Token Symbol: {output_symbol}")
                                                
                                                # Get decimals for human-readable amount
                                                try:
                                                    output_decimals_contract = w3.eth.contract(
                                                        address=output_token,
                                                        abi=[{"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"}]
                                                    )
                                                    output_decimals = output_decimals_contract.functions.decimals().call()
                                                    human_output = output_amount / (10 ** output_decimals)
                                                    print(f"       Human Output Amount: {human_output}")
                                                except:
                                                    print(f"       Human Output Amount: Unknown")
                                                    
                                            except:
                                                print(f"       Output Token Symbol: Unknown")
                                        else:
                                            print(f"       Output Token: ETH (native)")
                                            human_output = w3.from_wei(output_amount, 'ether')
                                            print(f"       Human Output Amount: {human_output} ETH")
                                            
                                    except Exception as e:
                                        print(f"       ❌ Error decoding data: {e}")
                                else:
                                    print(f"       ℹ️ No data field in log")
                                    
                        except Exception as e:
                            print(f"       ❌ Error processing topics: {e}")
                        
                        print()
                else:
                    print(f"   ℹ️ No Portal events found")
                
                # Also check for any transfers to ShapeShift treasury
                treasury_transfers = []
                for j, log in enumerate(receipt['logs']):
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
                                        'log_index': j
                                    })
                                    
                            except Exception as e:
                                continue
                
                if treasury_transfers:
                    print(f"   🎯 Found {len(treasury_transfers)} transfers to ShapeShift treasury")
                    for transfer in treasury_transfers:
                        print(f"     Log {transfer['log_index']+1}: {transfer['value']} from {transfer['from']}")
                        
                        # Get token symbol
                        try:
                            token_contract = w3.eth.contract(
                                address=transfer['token_address'],
                                abi=[{"constant": True, "inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "type": "function"}]
                            )
                            symbol = token_contract.functions.symbol().call()
                            print(f"       Token Symbol: {symbol}")
                        except:
                            print(f"       Token Symbol: Unknown")
                else:
                    print(f"   ℹ️ No direct transfers to ShapeShift treasury")
                
            except Exception as e:
                print(f"   ❌ Error analyzing transaction: {e}")
        
        # Summary
        print(f"\n📊 Analysis Summary:")
        print(f"   🔍 Analyzed {len(recent_transactions)} recent Portals transactions")
        print(f"   🎯 Looking for ShapeShift partnership in Portal events")
        print(f"   💰 ShapeShift earns fees through partnerships, not direct transfers")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    analyze_portal_events()
