#!/usr/bin/env python3
"""
Debug relay transactions to understand volume calculation issues
"""

from web3 import Web3
from price_fetcher import PriceFetcher

# Arbitrum RPC
ARBITRUM_RPC = "https://arb1.arbitrum.io/rpc"
CMC_API_KEY = "64dfaca3-439f-440d-8540-f11e06840ccc"

def debug_relay_transaction():
    """Find and debug a recent relay transaction"""
    
    w3 = Web3(Web3.HTTPProvider(ARBITRUM_RPC))
    price_fetcher = PriceFetcher(CMC_API_KEY)
    tokens = price_fetcher.update_arbitrum_token_prices()
    
    print("🔍 Looking for a recent relay transaction to debug...")
    
    try:
        latest_block = w3.eth.block_number
        relay_contract = "0xBBbfD134E9b44BfB5123898BA36b01dE7ab93d98".lower()
        
        # Find a recent transaction
        for block_num in range(latest_block, latest_block - 100, -1):
            try:
                block = w3.eth.get_block(block_num, full_transactions=True)
                
                for tx in block['transactions']:
                    to_addr = tx['to'].lower() if tx['to'] else ""
                    
                    if to_addr == relay_contract:
                        tx_hash = tx['hash'].hex()
                        print(f"\n🎯 Found relay transaction: {tx_hash}")
                        print(f"   Block: {block_num}")
                        print(f"   From: {tx['from']}")
                        print(f"   Gas: {tx['gas']}")
                        print(f"   Value: {tx['value']} wei")
                        
                        # Get receipt and analyze
                        receipt = w3.eth.get_transaction_receipt(tx_hash)
                        print(f"   Status: {'✅ Success' if receipt['status'] else '❌ Failed'}")
                        print(f"   Gas used: {receipt['gasUsed']}")
                        print(f"   Logs: {len(receipt['logs'])}")
                        
                        # Parse transfers
                        transfers = parse_transfers(receipt)
                        print(f"\n📊 Transfer Analysis:")
                        print(f"   Total transfers: {len(transfers)}")
                        
                        if not transfers:
                            print("   ❌ NO TRANSFERS FOUND - This explains the $0 volume!")
                            print("   Possible reasons:")
                            print("   1. Transaction failed")
                            print("   2. No ERC20 transfers (only ETH)")
                            print("   3. Different log format")
                            
                            # Show all logs to understand what's happening
                            print(f"\n📝 Raw logs analysis:")
                            for i, log in enumerate(receipt['logs']):
                                print(f"   Log {i+1}:")
                                print(f"     Address: {log['address']}")
                                print(f"     Topics: {len(log['topics'])} topics")
                                if log['topics']:
                                    event_sig = log['topics'][0].hex()
                                    print(f"     Event signature: {event_sig}")
                                    if event_sig == "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef":
                                        print(f"     ✅ This IS a Transfer event!")
                                    else:
                                        print(f"     ❌ This is NOT a Transfer event")
                        else:
                            print(f"\n💰 Transfer details:")
                            total_recognized_value = 0
                            
                            for i, transfer in enumerate(transfers):
                                token_addr = transfer['token'].lower()
                                print(f"\n   Transfer {i+1}:")
                                print(f"     Token: {token_addr}")
                                print(f"     From: {transfer['from']}")
                                print(f"     To: {transfer['to']}")
                                print(f"     Amount (raw): {transfer['amount']}")
                                
                                # Check if we recognize this token
                                token_info = tokens.get(token_addr)
                                if token_info:
                                    amount_formatted = transfer['amount'] / (10 ** token_info['decimals'])
                                    usd_value = amount_formatted * token_info['price']
                                    print(f"     ✅ Recognized: {amount_formatted:.6f} {token_info['symbol']} = ${usd_value:.2f}")
                                    
                                    if i == 0:  # First transfer
                                        total_recognized_value = usd_value
                                        print(f"     🎯 This is the FIRST transfer - would be used for volume")
                                else:
                                    print(f"     ❌ Unknown token - not in our dictionary")
                                    print(f"     Need to add this token: {token_addr}")
                            
                            print(f"\n📈 Volume calculation result:")
                            if total_recognized_value > 0:
                                print(f"   Initial transfer value: ${total_recognized_value:.2f}")
                                print(f"   This should NOT show as $0.00!")
                            else:
                                print(f"   ❌ First transfer is unrecognized token")
                                print(f"   This explains why volume = $0.00")
                        
                        return tx_hash
                        
            except Exception as e:
                continue
                
        print("❌ No recent relay transactions found")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

def parse_transfers(receipt):
    """Parse ERC20 transfers from receipt"""
    
    transfers = []
    TRANSFER_SIG = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
    
    for log in receipt['logs']:
        try:
            if log['topics'] and len(log['topics']) >= 3:
                event_sig = log['topics'][0].hex()
                
                if event_sig == TRANSFER_SIG:
                    from_topic = log['topics'][1].hex() if hasattr(log['topics'][1], 'hex') else str(log['topics'][1])
                    to_topic = log['topics'][2].hex() if hasattr(log['topics'][2], 'hex') else str(log['topics'][2])
                    
                    from_addr = "0x" + from_topic[-40:]
                    to_addr = "0x" + to_topic[-40:]
                    
                    data_hex = log['data'].hex() if hasattr(log['data'], 'hex') else str(log['data'])
                    if data_hex.startswith('0x'):
                        data_hex = data_hex[2:]
                        
                    amount = int(data_hex, 16) if data_hex else 0
                    
                    transfers.append({
                        "token": log['address'],
                        "from": from_addr,
                        "to": to_addr,
                        "amount": amount
                    })
                    
        except Exception as e:
            print(f"Error parsing log: {e}")
            continue
            
    return transfers

if __name__ == "__main__":
    debug_relay_transaction() 