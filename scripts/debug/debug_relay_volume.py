#!/usr/bin/env python3
"""
Debug Relay Volume Calculation Issues

Analyzes a specific relay transaction to understand why volume calculation is failing
"""

import requests
import json
from web3 import Web3
import os

# Configuration
ARBITRUM_RPC = f"https://arbitrum-mainnet.infura.io/v3/{os.getenv('INFURA_API_KEY', '208a3474635e4ebe8ee409cef3fbcd40')}"
CMC_API_KEY = "64dfaca3-439f-440d-8540-f11e06840ccc"
RELAY_CONTRACT = "0xBBbfD134E9b44BfB5123898BA36b01dE7ab93d98"

def get_token_prices():
    """Get real-time token prices"""
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
    headers = {'X-CMC_PRO_API_KEY': CMC_API_KEY}
    params = {'symbol': 'USDC,ETH,USDT,WBTC,UNI,LINK,ARB', 'convert': 'USD'}
    
    try:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        
        prices = {}
        if data['status']['error_code'] == 0:
            for symbol in ['USDC', 'ETH', 'USDT', 'WBTC', 'UNI', 'LINK', 'ARB']:
                if symbol in data['data']:
                    prices[symbol] = data['data'][symbol]['quote']['USD']['price']
        return prices
    except:
        return {}

def debug_specific_transaction():
    """Debug a specific recent transaction"""
    
    w3 = Web3(Web3.HTTPProvider(ARBITRUM_RPC))
    token_prices = get_token_prices()
    
    print("🔍 Looking for a recent relay transaction to debug...")
    
    # Token dictionary
    tokens = {
        "0xaf88d065e77c8cc2239327c5edb3a432268e5831": {"symbol": "USDC", "decimals": 6, "price": token_prices.get('USDC', 1.0)},
        "0x82af49447d8a07e3bd95bd0d56f35241523fbab1": {"symbol": "WETH", "decimals": 18, "price": token_prices.get('ETH', 3400)},
        "0xfd086bc7cd5c481dcc9c85ebe478a1c0b69fcbb9": {"symbol": "USDT", "decimals": 6, "price": token_prices.get('USDT', 1.0)},
        "0xff970a61a04b1ca14834a43f5de4533ebddb5cc8": {"symbol": "USDC.e", "decimals": 6, "price": token_prices.get('USDC', 1.0)},
        "0x2f2a2543b76a4166549f7aab2e75bef0aefc5b0f": {"symbol": "WBTC", "decimals": 8, "price": token_prices.get('WBTC', 65000)},
        "0xfa7f8980b0f1e64a2062791cc3b0871572f1f7f0": {"symbol": "UNI", "decimals": 18, "price": token_prices.get('UNI', 8)},
        "0xf97f4df75117a78c1a5a0dbb814af92458539fb4": {"symbol": "LINK", "decimals": 18, "price": token_prices.get('LINK', 15)},
        "0x912ce59144191c1204e64559fe8253a0e49e6548": {"symbol": "ARB", "decimals": 18, "price": token_prices.get('ARB', 0.8)},
    }
    
    try:
        latest_block = w3.eth.block_number
        print(f"Latest block: {latest_block}")
        
        # Find a recent relay transaction
        for block_num in range(latest_block, latest_block - 50, -1):
            try:
                block = w3.eth.get_block(block_num, full_transactions=True)
                
                for tx in block['transactions']:
                    if tx['to'] and tx['to'].lower() == RELAY_CONTRACT.lower():
                        tx_hash = tx['hash'].hex()
                        print(f"\n🎯 Found relay transaction: {tx_hash}")
                        print(f"   Block: {block_num}")
                        print(f"   From: {tx['from']}")
                        print(f"   Gas: {tx['gas']}")
                        print(f"   Value: {tx['value']} wei")
                        
                        # Get receipt
                        receipt = w3.eth.get_transaction_receipt(tx_hash)
                        print(f"   Status: {'✅ Success' if receipt['status'] else '❌ Failed'}")
                        print(f"   Gas used: {receipt['gasUsed']}")
                        print(f"   Total logs: {len(receipt['logs'])}")
                        
                        # Parse transfers step by step
                        transfers = []
                        TRANSFER_SIG = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
                        
                        print(f"\n📊 Analyzing logs for Transfer events:")
                        
                        for i, log in enumerate(receipt['logs']):
                            print(f"\n   Log {i+1}:")
                            print(f"     Address: {log['address']}")
                            print(f"     Topics: {len(log['topics'])}")
                            
                            if len(log['topics']) >= 3:
                                # Get first topic (event signature)
                                topic0 = log['topics'][0]
                                if hasattr(topic0, 'hex'):
                                    topic0_hex = topic0.hex()
                                else:
                                    topic0_hex = str(topic0)
                                
                                print(f"     Event sig: {topic0_hex}")
                                
                                if topic0_hex == TRANSFER_SIG:
                                    print(f"     ✅ This IS a Transfer event!")
                                    
                                    # Parse the transfer
                                    try:
                                        from_topic = log['topics'][1]
                                        to_topic = log['topics'][2]
                                        
                                        if hasattr(from_topic, 'hex'):
                                            from_hex = from_topic.hex()
                                        else:
                                            from_hex = str(from_topic)
                                            
                                        if hasattr(to_topic, 'hex'):
                                            to_hex = to_topic.hex()
                                        else:
                                            to_hex = str(to_topic)
                                        
                                        from_addr = "0x" + from_hex[-40:]
                                        to_addr = "0x" + to_hex[-40:]
                                        
                                        # Parse amount
                                        data = log['data']
                                        if hasattr(data, 'hex'):
                                            data_hex = data.hex()
                                        else:
                                            data_hex = str(data)
                                        
                                        if data_hex.startswith('0x'):
                                            data_hex = data_hex[2:]
                                        
                                        amount = int(data_hex, 16) if data_hex else 0
                                        
                                        # Check if we know this token
                                        token_addr = log['address'].lower()
                                        token_info = tokens.get(token_addr)
                                        
                                        print(f"     Token: {log['address']}")
                                        print(f"     From: {from_addr}")
                                        print(f"     To: {to_addr}")
                                        print(f"     Amount (raw): {amount}")
                                        
                                        if token_info:
                                            formatted_amount = amount / (10 ** token_info['decimals'])
                                            usd_value = formatted_amount * token_info['price']
                                            print(f"     ✅ Recognized: {formatted_amount:.6f} {token_info['symbol']} = ${usd_value:.2f}")
                                        else:
                                            print(f"     ❌ Unknown token: {token_addr}")
                                            print(f"     ❌ This token is NOT in our dictionary!")
                                        
                                        transfers.append({
                                            "token": log['address'],
                                            "from": from_addr,
                                            "to": to_addr,
                                            "amount": amount,
                                            "token_info": token_info
                                        })
                                        
                                    except Exception as e:
                                        print(f"     ❌ Error parsing transfer: {e}")
                                else:
                                    print(f"     ❌ Not a Transfer event")
                            else:
                                print(f"     ❌ Not enough topics for Transfer event")
                        
                        print(f"\n💰 Transfer Summary:")
                        print(f"   Total transfers found: {len(transfers)}")
                        
                        if not transfers:
                            print(f"   ❌ NO TRANSFERS FOUND!")
                            print(f"   This explains why volume = $0.00")
                        else:
                            print(f"   ✅ Found {len(transfers)} transfers")
                            
                            # Calculate volume from first transfer
                            first_transfer = transfers[0]
                            if first_transfer['token_info']:
                                token_info = first_transfer['token_info']
                                amount = first_transfer['amount'] / (10 ** token_info['decimals'])
                                usd_value = amount * token_info['price']
                                print(f"   🎯 First transfer volume: ${usd_value:.2f}")
                            else:
                                print(f"   ❌ First transfer is unknown token")
                                print(f"   Missing token: {first_transfer['token']}")
                        
                        return tx_hash
                        
            except Exception as e:
                continue
        
        print("❌ No recent relay transactions found")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_specific_transaction() 