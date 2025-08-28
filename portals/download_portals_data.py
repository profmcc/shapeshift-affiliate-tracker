#!/usr/bin/env python3
"""
Download Portals transaction data and run the listener to capture more transactions
"""

from portals_listener import CSVPortalsListener
from web3 import Web3
import os
import csv

def download_portals_data():
    """Download Portals transaction data"""
    
    print("📥 Downloading Portals Transaction Data")
    print("=======================================")
    
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
        
        # Also include the known ShapeShift transaction
        known_shapeshift_tx = "0xb6192470f067e11a599ac6af7fbaebdf192a8724fe555050ab327df67ecb4a53"
        
        all_transactions = recent_transactions + [known_shapeshift_tx]
        
        # Create CSV file for downloaded data
        csv_filename = "portals_transactions_downloaded.csv"
        csv_fields = [
            'tx_hash', 'block_number', 'from_address', 'to_address', 'value_eth', 
            'gas_price_gwei', 'gas_used', 'status', 'logs_count', 'portal_events',
            'shapeshift_partner', 'input_token', 'input_amount', 'output_token', 
            'output_amount', 'etherscan_url'
        ]
        
        with open(csv_filename, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=csv_fields)
            writer.writeheader()
            
            for i, tx_hash in enumerate(all_transactions):
                print(f"\n🔍 Downloading Transaction {i+1}: {tx_hash}")
                
                try:
                    # Get transaction details
                    tx = w3.eth.get_transaction(tx_hash)
                    receipt = w3.eth.get_transaction_receipt(tx_hash)
                    
                    # Check for Portal events
                    portal_events = []
                    shapeshift_partner = False
                    input_token = ""
                    input_amount = ""
                    output_token = ""
                    output_amount = ""
                    
                    for log in receipt['logs']:
                        if log['address'].lower() == "0xbf5A7F3629fB325E2a8453D595AB103465F75E62".lower():
                            if log['topics'] and len(log['topics']) > 0:
                                if log['topics'][0].hex() == "0x5915121ae705c6baa1bd6698f437ff30eb4b7dbd20e1f7d83c2f1a8be09a1f03":
                                    portal_events.append(log)
                                    
                                    # Check if ShapeShift is the partner
                                    if len(log['topics']) > 3:
                                        partner = "0x" + log['topics'][3].hex()[-40:]
                                        if partner.lower() == "0x90A48D5CF7343B08dA12E067680B4C6dbfE551Be".lower():
                                            shapeshift_partner = True
                                    
                                    # Try to decode the data
                                    if log['data'] and len(log['data']) > 2:
                                        try:
                                            from eth_abi import decode
                                            decoded = decode(
                                                ["address", "uint256", "address", "uint256", "address"],
                                                bytes.fromhex(log['data'][2:])
                                            )
                                            input_token = decoded[0]
                                            input_amount = str(decoded[1])
                                            output_token = decoded[2]
                                            output_amount = str(decoded[3])
                                        except:
                                            pass
                    
                    # Write to CSV
                    row = {
                        'tx_hash': tx_hash,
                        'block_number': receipt['blockNumber'],
                        'from_address': tx['from'],
                        'to_address': tx['to'],
                        'value_eth': str(w3.from_wei(tx['value'], 'ether')),
                        'gas_price_gwei': str(w3.from_wei(tx['gasPrice'], 'gwei')),
                        'gas_used': receipt['gasUsed'],
                        'status': 'Success' if receipt['status'] == 1 else 'Failed',
                        'logs_count': len(receipt['logs']),
                        'portal_events': len(portal_events),
                        'shapeshift_partner': 'Yes' if shapeshift_partner else 'No',
                        'input_token': input_token,
                        'input_amount': input_amount,
                        'output_token': output_token,
                        'output_amount': output_amount,
                        'etherscan_url': f"https://etherscan.io/tx/{tx_hash}"
                    }
                    
                    writer.writerow(row)
                    
                    print(f"   ✅ Downloaded: Block {receipt['blockNumber']}, Status: {row['status']}")
                    print(f"   📊 Portal Events: {len(portal_events)}")
                    print(f"   🎯 ShapeShift Partner: {'Yes' if shapeshift_partner else 'No'}")
                    
                except Exception as e:
                    print(f"   ❌ Error downloading transaction: {e}")
        
        print(f"\n📁 Data saved to: {csv_filename}")
        
        # Summary
        print(f"\n📊 Download Summary:")
        print(f"   🔍 Downloaded {len(all_transactions)} transactions")
        print(f"   📋 Data saved to CSV for analysis")
        print(f"   🎯 Looking for ShapeShift partnerships in Portal events")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def run_portals_listener():
    """Run the Portals listener to capture more transactions"""
    
    print(f"\n🚀 Running Portals Listener")
    print(f"============================")
    
    try:
        # Run the listener with a reasonable block range
        listener = CSVPortalsListener()
        
        print(f"🔍 Running listener with max_blocks=100...")
        listener.run(max_blocks=100)
        
        print(f"✅ Listener completed successfully!")
        
        # Check what was captured
        csv_dir = "csv_data"
        if os.path.exists(f"{csv_dir}/portals_transactions.csv"):
            with open(f"{csv_dir}/portals_transactions.csv", 'r') as f:
                lines = f.readlines()
                print(f"📋 Captured {len(lines)-1} transactions (excluding header)")
        
    except Exception as e:
        print(f"❌ Error running listener: {e}")

if __name__ == "__main__":
    download_portals_data()
    run_portals_listener()
