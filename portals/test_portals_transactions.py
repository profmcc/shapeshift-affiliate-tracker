#!/usr/bin/env python3
"""
Test script to find Portals transactions in specific block ranges
"""

import os
import sys
from web3 import Web3
from eth_abi import decode

def test_portals_blocks():
    """Test specific block ranges where Portals transactions are known to exist"""
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Get API key
    alchemy_api_key = os.getenv('ALCHEMY_API_KEY')
    if not alchemy_api_key:
        print("❌ No Alchemy API key found in .env")
        return
    
    # Connect to Ethereum
    w3 = Web3(Web3.HTTPProvider(f"https://eth-mainnet.g.alchemy.com/v2/{alchemy_api_key}"))
    
    if not w3.is_connected():
        print("❌ Failed to connect to Ethereum")
        return
    
    print("✅ Connected to Ethereum")
    
    # Portals router address
    portals_router = "0xbf5A7F3629fB325E2a8453D595AB103465F75E62"
    print(f"🔍 Portals Router: {portals_router}")
    
    # Test block ranges
    test_ranges = [
        (22774490, 22774500),  # Known Portals transaction
        (23240000, 23240100),  # Recent blocks
        (23230000, 23230100),  # Slightly older
    ]
    
    for start_block, end_block in test_ranges:
        print(f"\n🔍 Testing blocks {start_block} to {end_block}")
        
        try:
            # Get logs from Portals router
            logs = w3.eth.get_logs({
                "fromBlock": start_block,
                "toBlock": end_block,
                "address": portals_router,
                "topics": []
            })
            
            print(f"📋 Found {len(logs)} logs from Portals router")
            
            if logs:
                for i, log in enumerate(logs[:5]):  # Show first 5
                    print(f"  Log {i+1}: Block {log['blockNumber']}, Tx: {log['transactionHash'].hex()}")
                    
                    # Get transaction details
                    try:
                        tx = w3.eth.get_transaction(log['transactionHash'])
                        print(f"    From: {tx['from']}")
                        print(f"    To: {tx['to']}")
                        print(f"    Value: {w3.from_wei(tx['value'], 'ether')} ETH")
                        
                        # Get transaction receipt for more details
                        receipt = w3.eth.get_transaction_receipt(log['transactionHash'])
                        print(f"    Gas used: {receipt['gasUsed']}")
                        print(f"    Status: {'Success' if receipt['status'] == 1 else 'Failed'}")
                        
                    except Exception as e:
                        print(f"    Error getting tx details: {e}")
                    
                    print()
            else:
                print("  No Portals logs found in this range")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    # Test with a broader search
    print(f"\n🔍 Testing broader search for Portals activity...")
    
    try:
        # Look for any transactions involving the Portals router
        current_block = w3.eth.block_number
        test_block = current_block - 100  # Recent block
        
        print(f"Testing block {test_block}")
        
        block = w3.eth.get_block(test_block, full_transactions=True)
        
        portals_txs = []
        for tx in block.transactions:
            if tx['to'] and tx['to'].lower() == portals_router.lower():
                portals_txs.append(tx)
        
        print(f"Found {len(portals_txs)} transactions involving Portals router in block {test_block}")
        
        for tx in portals_txs[:3]:  # Show first 3
            print(f"  Tx: {tx['hash'].hex()}")
            print(f"  From: {tx['from']}")
            print(f"  Value: {w3.from_wei(tx['value'], 'ether')} ETH")
            print()
            
    except Exception as e:
        print(f"❌ Error in broader search: {e}")

def test_portals_contract():
    """Test direct interaction with Portals contract"""
    
    from dotenv import load_dotenv
    load_dotenv()
    
    alchemy_api_key = os.getenv('ALCHEMY_API_KEY')
    if not alchemy_api_key:
        print("❌ No Alchemy API key found")
        return
    
    w3 = Web3(Web3.HTTPProvider(f"https://eth-mainnet.g.alchemy.com/v2/{alchemy_api_key}"))
    
    if not w3.is_connected():
        print("❌ Failed to connect")
        return
    
    portals_router = "0xbf5A7F3629fB325E2a8453D595AB103465F75E62"
    
    print(f"🔍 Testing Portals contract: {portals_router}")
    
    try:
        # Get contract code
        code = w3.eth.get_code(portals_router)
        if code:
            print(f"✅ Contract has code: {len(code)} bytes")
            
            # Get contract balance
            balance = w3.eth.get_balance(portals_router)
            print(f"💰 Contract balance: {w3.from_wei(balance, 'ether')} ETH")
            
            # Get recent transactions
            current_block = w3.eth.block_number
            print(f"📊 Current block: {current_block}")
            
        else:
            print("❌ No contract code found")
            
    except Exception as e:
        print(f"❌ Error testing contract: {e}")

if __name__ == "__main__":
    print("🧪 Portals Transaction Test Script")
    print("==================================")
    
    print("\n1. Testing specific block ranges...")
    test_portals_blocks()
    
    print("\n2. Testing Portals contract directly...")
    test_portals_contract()
    
    print("\n✅ Testing completed!")
