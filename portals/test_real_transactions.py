#!/usr/bin/env python3
"""
Test script to process real Portals transactions and extract detailed information
"""

from portals_listener import CSVPortalsListener
import os

def test_real_transactions():
    """Test the portals listener with real Portals transactions"""
    
    print("🧪 Testing Portals Listener with Real Transactions")
    print("==================================================")
    
    # Initialize the listener
    listener = CSVPortalsListener()
    
    # Test with the real transactions we found
    real_transactions = [
        {
            "name": "Real Portals Transaction 1",
            "tx_hash": "0x0840bba848e991cdcfbf2b71b8e1cb94fb72d6343ad4bb182f7ee1c48612221d",
            "block": 22774492,
            "chain": "ethereum"
        },
        {
            "name": "Real Portals Transaction 2", 
            "tx_hash": "0x25510d5b5599ece7c7517604171fee476773bb35691fb57a85bb836f2d7fa79c",
            "block": 23230059,
            "chain": "ethereum"
        }
    ]
    
    for tx_info in real_transactions:
        print(f"\n🔍 Testing: {tx_info['name']}")
        print(f"   Transaction: {tx_info['tx_hash']}")
        print(f"   Block: {tx_info['block']}")
        print(f"   Chain: {tx_info['chain']}")
        
        try:
            # Get the transaction details from the blockchain
            w3 = listener.chains[tx_info['chain']]['w3']
            
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
            
            # Analyze logs for token transfers
            print(f"   🔍 Log Analysis:")
            for i, log in enumerate(receipt['logs']):
                print(f"     Log {i+1}:")
                print(f"       Address: {log['address']}")
                print(f"       Topics: {len(log['topics'])}")
                if log['topics']:
                    print(f"       Topic 0: {log['topics'][0].hex()}")
                
                # Check if this is an ERC-20 transfer
                if log['topics'] and len(log['topics']) > 0:
                    # ERC-20 Transfer event signature
                    transfer_signature = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
                    if log['topics'][0].hex() == transfer_signature:
                        print(f"       ✅ ERC-20 Transfer detected!")
                        
                        try:
                            # Decode the transfer event
                            from eth_abi import decode
                            decoded = decode(
                                ["address", "address", "uint256"],
                                bytes.fromhex(log['data'][2:])  # Remove '0x' prefix
                            )
                            from_addr, to_addr, value = decoded
                            print(f"         From: {from_addr}")
                            print(f"         To: {to_addr}")
                            print(f"         Value: {value}")
                            
                            # Try to get token symbol
                            try:
                                token_contract = w3.eth.contract(
                                    address=log['address'],
                                    abi=[{"constant": True, "inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "type": "function"}]
                                )
                                symbol = token_contract.functions.symbol().call()
                                print(f"         Token: {symbol} ({log['address']})")
                            except:
                                print(f"         Token: Unknown ({log['address']})")
                                
                        except Exception as e:
                            print(f"         ❌ Error decoding: {e}")
                
                print()
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # Test CSV processing
    print("\n📊 Testing CSV Processing")
    print("=========================")
    
    try:
        # Process a small block range to test the full pipeline
        print("Processing recent blocks to test CSV creation...")
        
        # Reset block tracker to test recent blocks
        import os
        block_tracker_file = os.path.join(listener.csv_dir, "portals_block_tracker.csv")
        if os.path.exists(block_tracker_file):
            os.remove(block_tracker_file)
            print("Reset block tracker")
        
        # Process recent blocks
        total_transactions = listener.run(max_blocks=50)
        
        print(f"✅ Processed {total_transactions} transactions")
        
        # Check CSV files
        transactions_file = os.path.join(listener.csv_dir, "portals_transactions.csv")
        if os.path.exists(transactions_file):
            with open(transactions_file, 'r') as f:
                lines = f.readlines()
                print(f"📁 Transactions CSV: {len(lines)} lines")
                if len(lines) > 1:
                    print("📋 Data rows: {len(lines) - 1}")
        
        block_tracker_file = os.path.join(listener.csv_dir, "portals_block_tracker.csv")
        if os.path.exists(block_tracker_file):
            with open(block_tracker_file, 'r') as f:
                lines = f.readlines()
                print(f"📁 Block Tracker CSV: {len(lines)} lines")
                if len(lines) > 1:
                    print("📋 Block tracking data:")
                    for line in lines[1:]:  # Skip header
                        parts = line.strip().split(',')
                        if len(parts) >= 4:
                            print(f"   {parts[0]}: Block {parts[1]}, Status: {parts[3]}")
        
    except Exception as e:
        print(f"❌ Error testing CSV processing: {e}")
    
    print("\n✅ Testing completed!")

if __name__ == "__main__":
    test_real_transactions()
