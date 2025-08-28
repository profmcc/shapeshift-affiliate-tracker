#!/usr/bin/env python3
"""
Direct analysis of known Portals transactions to extract token transfer information
"""

from portals_listener import CSVPortalsListener
from web3 import Web3
from eth_abi import decode

def analyze_known_transactions():
    """Directly analyze the known Portals transactions"""
    
    print("🔍 Direct Analysis of Known Portals Transactions")
    print("===============================================")
    
    # Initialize the listener
    listener = CSVPortalsListener()
    
    # Known Portals transactions
    known_transactions = [
        {
            "name": "Portals Transaction 1",
            "tx_hash": "0x0840bba848e991cdcfbf2b71b8e1cb94fb72d6343ad4bb182f7ee1c48612221d",
            "block": 22774492
        },
        {
            "name": "Portals Transaction 2",
            "tx_hash": "0x25510d5b5599ece7c7517604171fee476773bb35691fb57a85bb836f2d7fa79c",
            "block": 23230059
        }
    ]
    
    for tx_info in known_transactions:
        print(f"\n🔍 Analyzing: {tx_info['name']}")
        print(f"   Transaction: {tx_info['tx_hash']}")
        print(f"   Block: {tx_info['block']}")
        
        try:
            w3 = listener.chains['ethereum']['w3']
            
            # Get transaction
            tx = w3.eth.get_transaction(tx_info['tx_hash'])
            print(f"   📋 Transaction Details:")
            print(f"     From: {tx['from']}")
            print(f"     To: {tx['to']}")
            print(f"     Value: {w3.from_wei(tx['value'], 'ether')} ETH")
            print(f"     Gas Price: {w3.from_wei(tx['gasPrice'], 'gwei')} Gwei")
            
            # Get transaction receipt
            receipt = w3.eth.get_transaction_receipt(tx_info['tx_hash'])
            print(f"     Gas Used: {receipt['gasUsed']}")
            print(f"     Status: {'Success' if receipt['status'] == 1 else 'Failed'}")
            print(f"     Logs: {len(receipt['logs'])}")
            
            # Analyze all logs
            print(f"   🔍 Log Analysis:")
            
            # ShapeShift treasury address
            treasury_address = "0x90A48D5CF7343B08dA12E067680B4C6dbfE551Be"
            
            for i, log in enumerate(receipt['logs']):
                print(f"     Log {i+1}:")
                print(f"       Address: {log['address']}")
                print(f"       Topics: {len(log['topics'])}")
                
                if log['topics']:
                    print(f"       Topic 0: {log['topics'][0].hex()}")
                    
                    # Check if this is an ERC-20 transfer
                    if log['topics'][0].hex() == "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef":
                        print(f"       ✅ ERC-20 Transfer detected!")
                        
                        try:
                            # Decode the transfer event
                            decoded = decode(
                                ["address", "address", "uint256"],
                                bytes.fromhex(log['data'][2:])
                            )
                            from_addr, to_addr, value = decoded
                            
                            print(f"         From: {from_addr}")
                            print(f"         To: {to_addr}")
                            print(f"         Value: {value}")
                            
                            # Check if this is a transfer to ShapeShift treasury
                            if to_addr.lower() == treasury_address.lower():
                                print(f"         🎯 TRANSFER TO SHAPESHIFT TREASURY!")
                                
                                # Try to get token symbol
                                try:
                                    token_contract = w3.eth.contract(
                                        address=log['address'],
                                        abi=[{"constant": True, "inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "type": "function"}]
                                    )
                                    symbol = token_contract.functions.symbol().call()
                                    print(f"         Token Symbol: {symbol}")
                                    
                                    # Try to get token decimals
                                    try:
                                        decimals_contract = w3.eth.contract(
                                            address=log['address'],
                                            abi=[{"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"}]
                                        )
                                        decimals = decimals_contract.functions.decimals().call()
                                        human_value = value / (10 ** decimals)
                                        print(f"         Human Value: {human_value}")
                                    except:
                                        print(f"         Human Value: Unknown (decimals not available)")
                                        
                                except Exception as e:
                                    print(f"         Token Symbol: Unknown (error: {e})")
                            
                            # Try to get token symbol for any transfer
                            try:
                                token_contract = w3.eth.contract(
                                    address=log['address'],
                                    abi=[{"constant": True, "inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "type": "function"}]
                                )
                                symbol = token_contract.functions.symbol().call()
                                print(f"         Token Symbol: {symbol}")
                            except:
                                print(f"         Token Symbol: Unknown")
                                
                        except Exception as e:
                            print(f"         ❌ Error decoding: {e}")
                
                print()
            
            # Look for any transfers to ShapeShift treasury
            print(f"   🎯 Treasury Transfer Summary:")
            treasury_transfers = []
            
            for log in receipt['logs']:
                if log['topics'] and len(log['topics']) > 0:
                    if log['topics'][0].hex() == "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef":
                        try:
                            decoded = decode(
                                ["address", "address", "uint256"],
                                bytes.fromhex(log['data'][2:])
                            )
                            from_addr, to_addr, value = decoded
                            
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
                print(f"     Found {len(treasury_transfers)} transfers to ShapeShift treasury:")
                for transfer in treasury_transfers:
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
                    except:
                        print(f"       Token Symbol: Unknown")
                    
                    print()
            else:
                print(f"     No direct transfers to ShapeShift treasury found")
                
        except Exception as e:
            print(f"   ❌ Error analyzing transaction: {e}")

def search_for_recent_portals_activity():
    """Search for more recent Portals activity"""
    
    print("\n🔍 Searching for Recent Portals Activity")
    print("========================================")
    
    listener = CSVPortalsListener()
    
    try:
        w3 = listener.chains['ethereum']['w3']
        current_block = w3.eth.block_number
        
        print(f"📊 Current block: {current_block}")
        
        # Search for Portals router activity in recent blocks
        search_blocks = 1000
        print(f"🔍 Searching last {search_blocks} blocks for Portals activity...")
        
        portals_router = "0xbf5A7F3629fB325E2a8453D595AB103465F75E62"
        
        # Search in smaller chunks
        chunk_size = 100
        total_logs = 0
        
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
                    
                    # Show details of first few logs
                    for i, log in enumerate(logs[:3]):
                        print(f"     Log {i+1}: Block {log['blockNumber']}, Tx: {log['transactionHash'].hex()}")
                        
            except Exception as e:
                print(f"   ⚠️ Error searching blocks {start_block}-{end_block}: {e}")
                continue
        
        print(f"\n📋 Total Portals logs found: {total_logs}")
        
        if total_logs > 0:
            print("🎯 Found recent Portals activity! Run detailed analysis on these transactions.")
        
    except Exception as e:
        print(f"❌ Error searching recent activity: {e}")

if __name__ == "__main__":
    analyze_known_transactions()
    search_for_recent_portals_activity()
