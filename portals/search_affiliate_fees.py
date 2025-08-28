#!/usr/bin/env python3
"""
Search for Portals transactions that send affiliate fees to ShapeShift treasury
"""

from portals_listener import CSVPortalsListener
from web3 import Web3
import os

def search_affiliate_fees():
    """Search for transactions sending affiliate fees to ShapeShift treasury"""
    
    print("🔍 Searching for Portals Affiliate Fee Transactions")
    print("==================================================")
    
    # Initialize the listener
    listener = CSVPortalsListener()
    
    # ShapeShift treasury addresses
    shapeshift_treasury = {
        "ethereum": "0x90A48D5CF7343B08dA12E067680B4C6dbfE551Be",
        "polygon": "0xB5F944600785724e31Edb90F9DFa16dBF01Af000",
        "optimism": "0x6268d07327f4fb7380732dc6d63d95F88c0E083b",
        "arbitrum": "0x38276553F8fbf2A027D901F8be45f00373d8Dd48",
        "base": "0x9c9aA90363630d4ab1D9dbF416cc3BBC8d3Ed502"
    }
    
    print("🎯 ShapeShift Treasury Addresses:")
    for chain, address in shapeshift_treasury.items():
        print(f"   {chain}: {address}")
    
    print("\n🔍 Searching for recent affiliate fee transactions...")
    
    # Search for recent transactions to treasury addresses
    for chain_name, treasury_address in shapeshift_treasury.items():
        print(f"\n🔍 Searching {chain_name} for transactions to treasury...")
        
        try:
            w3 = listener.chains[chain_name]['w3']
            current_block = w3.eth.block_number
            
            # Search recent blocks for transactions to treasury
            search_blocks = 1000  # Search last 1000 blocks
            
            print(f"   Current block: {current_block}")
            print(f"   Searching blocks: {current_block - search_blocks} to {current_block}")
            
            # Look for transactions to treasury address
            treasury_txs = []
            
            # Search in smaller chunks to avoid API limits
            chunk_size = 100
            for start_block in range(current_block - search_blocks, current_block, chunk_size):
                end_block = min(start_block + chunk_size, current_block)
                
                try:
                    # Get logs for transfers to treasury
                    logs = w3.eth.get_logs({
                        "fromBlock": start_block,
                        "toBlock": end_block,
                        "topics": [
                            "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef",  # Transfer event
                            None,  # from address (any)
                            f"0x000000000000000000000000{treasury_address[2:].lower()}"  # to treasury address
                        ]
                    })
                    
                    for log in logs:
                        try:
                            # Decode the transfer event
                            from eth_abi import decode
                            decoded = decode(
                                ["address", "address", "uint256"],
                                bytes.fromhex(log['data'][2:])
                            )
                            from_addr, to_addr, value = decoded
                            
                            # Get transaction details
                            tx = w3.eth.get_transaction(log['transactionHash'])
                            
                            # Check if this involves Portals router
                            portals_router = "0xbf5A7F3629fB325E2a8453D595AB103465F75E62"
                            is_portals_related = False
                            
                            # Check if transaction involves Portals router
                            if tx['to'] and tx['to'].lower() == portals_router.lower():
                                is_portals_related = True
                            
                            # Check transaction receipt for Portals router involvement
                            receipt = w3.eth.get_transaction_receipt(log['transactionHash'])
                            for log_entry in receipt['logs']:
                                if log_entry['address'].lower() == portals_router.lower():
                                    is_portals_related = True
                                    break
                            
                            if is_portals_related:
                                treasury_txs.append({
                                    'tx_hash': log['transactionHash'].hex(),
                                    'block': log['blockNumber'],
                                    'from': from_addr,
                                    'to': to_addr,
                                    'value': value,
                                    'token_address': log['address'],
                                    'is_portals': True
                                })
                            else:
                                # Still record treasury transfers for analysis
                                treasury_txs.append({
                                    'tx_hash': log['transactionHash'].hex(),
                                    'block': log['blockNumber'],
                                    'from': from_addr,
                                    'to': to_addr,
                                    'value': value,
                                    'token_address': log['address'],
                                    'is_portals': False
                                })
                                
                        except Exception as e:
                            continue
                            
                except Exception as e:
                    print(f"   ⚠️ Error searching blocks {start_block}-{end_block}: {e}")
                    continue
            
            print(f"   📋 Found {len(treasury_txs)} transactions to treasury")
            
            if treasury_txs:
                # Show Portals-related transactions first
                portals_txs = [tx for tx in treasury_txs if tx['is_portals']]
                other_txs = [tx for tx in treasury_txs if not tx['is_portals']]
                
                if portals_txs:
                    print(f"   🎯 Portals-related transactions: {len(portals_txs)}")
                    for tx in portals_txs[:5]:  # Show first 5
                        print(f"     Block {tx['block']}: {tx['tx_hash']}")
                        print(f"       From: {tx['from']}")
                        print(f"       Value: {tx['value']}")
                        print(f"       Token: {tx['token_address']}")
                        print()
                
                if other_txs:
                    print(f"   📊 Other treasury transactions: {len(other_txs)}")
                    for tx in other_txs[:3]:  # Show first 3
                        print(f"     Block {tx['block']}: {tx['tx_hash']}")
                        print(f"       From: {tx['from']}")
                        print(f"       Value: {tx['value']}")
                        print()
            
        except Exception as e:
            print(f"   ❌ Error searching {chain_name}: {e}")
    
    print("\n✅ Search completed!")

def search_specific_portals_transactions():
    """Search for specific Portals transactions that might have affiliate fees"""
    
    print("\n🔍 Searching for Specific Portals Transactions")
    print("==============================================")
    
    listener = CSVPortalsListener()
    
    # Known Portals transaction hashes to analyze
    known_txs = [
        "0x0840bba848e991cdcfbf2b71b8e1cb94fb72d6343ad4bb182f7ee1c48612221d",
        "0x25510d5b5599ece7c7517604171fee476773bb35691fb57a85bb836f2d7fa79c"
    ]
    
    for tx_hash in known_txs:
        print(f"\n🔍 Analyzing transaction: {tx_hash}")
        
        try:
            w3 = listener.chains['ethereum']['w3']
            
            # Get transaction receipt
            receipt = w3.eth.get_transaction_receipt(tx_hash)
            
            # Look for transfers to ShapeShift treasury
            treasury_address = "0x90A48D5CF7343B08dA12E067680B4C6dbfE551Be"
            
            for log in receipt['logs']:
                if log['topics'] and len(log['topics']) > 0:
                    # Check if this is a transfer to treasury
                    if log['topics'][0].hex() == "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef":
                        try:
                            from eth_abi import decode
                            decoded = decode(
                                ["address", "address", "uint256"],
                                bytes.fromhex(log['data'][2:])
                            )
                            from_addr, to_addr, value = decoded
                            
                            if to_addr.lower() == treasury_address.lower():
                                print(f"   🎯 Found transfer to ShapeShift treasury!")
                                print(f"      From: {from_addr}")
                                print(f"      To: {to_addr}")
                                print(f"      Value: {value}")
                                print(f"      Token: {log['address']}")
                                
                                # Try to get token symbol
                                try:
                                    token_contract = w3.eth.contract(
                                        address=log['address'],
                                        abi=[{"constant": True, "inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "type": "function"}]
                                    )
                                    symbol = token_contract.functions.symbol().call()
                                    print(f"      Token Symbol: {symbol}")
                                except:
                                    print(f"      Token Symbol: Unknown")
                                
                                print()
                                
                        except Exception as e:
                            continue
                            
        except Exception as e:
            print(f"   ❌ Error analyzing transaction: {e}")

if __name__ == "__main__":
    search_affiliate_fees()
    search_specific_portals_transactions()
