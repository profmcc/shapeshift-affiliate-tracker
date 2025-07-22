#!/usr/bin/env python3
"""
Fixed ShapeShift Relay Transaction Tracker

Properly tracks ShapeShift transactions on the relay contract with correct volume calculations
and saves them to a database.
"""

import requests
import time
import sqlite3
from datetime import datetime
from typing import Dict, List
from web3 import Web3
import os
import sys

# Add shared directory to path for block tracker
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../shared')))
from block_tracker import get_start_block, set_last_processed_block, init_database as init_block_tracker

# Configuration
ARBITRUM_RPC = f"https://arbitrum-mainnet.infura.io/v3/{os.getenv('INFURA_API_KEY', '208a3474635e4ebe8ee409cef3fbcd40')}"
CMC_API_KEY = "64dfaca3-439f-440d-8540-f11e06840ccc"
RELAY_CONTRACT = "0xBBbfD134E9b44BfB5123898BA36b01dE7ab93d98"
DB_PATH = "shapeshift_relay_transactions.db"
LISTENER_NAME = "relay_listener"
CHAIN = "arbitrum"

def init_database():
    """Initialize the database with relay transactions table"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS relay_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tx_hash TEXT UNIQUE NOT NULL,
            block_number INTEGER NOT NULL,
            timestamp TEXT NOT NULL,
            from_address TEXT NOT NULL,
            volume_usd REAL NOT NULL,
            tokens TEXT NOT NULL,
            raw_data TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()
    print("📁 Database initialized: shapeshift_relay_transactions.db")

def save_transactions_to_db(transactions: List[Dict]):
    """Save transactions to the database"""
    if not transactions:
        return
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    saved_count = 0
    for tx in transactions:
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO relay_transactions 
                (tx_hash, block_number, timestamp, from_address, volume_usd, tokens, raw_data)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                tx['hash'],
                tx['block'],
                tx['timestamp'],
                tx['from'],
                tx['volume_usd'],
                ','.join(tx['tokens']),
                str(tx)
            ))
            if cursor.rowcount > 0:
                saved_count += 1
        except Exception as e:
            print(f"   ❌ Error saving transaction {tx['hash'][:16]}...: {e}")
    
    conn.commit()
    conn.close()
    
    if saved_count > 0:
        print(f"💾 Saved {saved_count} new transactions to database")
    else:
        print("💾 No new transactions to save (all already exist)")

def get_database_stats():
    """Get database statistics"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM relay_transactions")
        total_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT SUM(volume_usd) FROM relay_transactions WHERE volume_usd > 0")
        total_volume = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT COUNT(*) FROM relay_transactions WHERE volume_usd > 0")
        volume_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM relay_transactions")
        time_range = cursor.fetchone()
        
        conn.close()
        
        print(f"\n📊 Database Statistics:")
        print(f"   Total Transactions: {total_count}")
        print(f"   Transactions with Volume: {volume_count}")
        print(f"   Total Volume: ${total_volume:,.2f}")
        if time_range[0] and time_range[1]:
            print(f"   Date Range: {time_range[0]} to {time_range[1]}")
            
    except Exception as e:
        print(f"Error getting database stats: {e}")

def get_real_time_prices() -> Dict[str, float]:
    """Get real-time token prices from CoinMarketCap"""
    print("🔄 Fetching real-time prices...")
    
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
                    price = data['data'][symbol]['quote']['USD']['price']
                    prices[symbol] = price
                    print(f"   {symbol}: ${price:.4f}")
        
        return prices
        
    except Exception as e:
        print(f"   ❌ Price fetch failed: {e}")
        return {}

def parse_transfers_fixed(receipt, tokens) -> List[Dict]:
    """Parse transfers from transaction receipt with improved token detection"""
    transfers = []
    
    for log in receipt['logs']:
        # Check if this is a Transfer event
        if len(log['topics']) >= 3 and log['topics'][0].hex() == '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef':
            token_address = log['address'].lower()
            
            # Get token info
            token_info = tokens.get(token_address)
            
            # Parse amount from data
            data_hex = log['data']
            if data_hex.startswith('0x'):
                data_hex = data_hex[2:]
            amount = int(data_hex, 16) if data_hex else 0
            
            transfers.append({
                'token_address': token_address,
                'token_info': token_info,
                'amount': amount
            })
    
    return transfers

def scan_blocks_for_shapeshift_transactions(start_block: int, end_block: int) -> List[Dict]:
    """Scan a range of blocks for ShapeShift relay transactions"""
    print(f"🔍 Scanning blocks {start_block:,} to {end_block:,} for ShapeShift relay transactions...")
    
    w3 = Web3(Web3.HTTPProvider(ARBITRUM_RPC))
    tokens = get_real_time_prices()
    
    found_transactions = []
    processed_blocks = 0
    
    try:
        for block_num in range(start_block, end_block + 1):
            try:
                block = w3.eth.get_block(block_num, full_transactions=True)
                processed_blocks += 1
                
                if processed_blocks % 100 == 0:
                    print(f"   📦 Processed {processed_blocks} blocks...")
                
                for tx in block['transactions']:
                    # Check if transaction involves the relay contract
                    if tx['to'] and tx['to'].lower() == RELAY_CONTRACT.lower():
                        try:
                            receipt = w3.eth.get_transaction_receipt(tx['hash'])
                            
                            # Parse transfers
                            transfers = parse_transfers_fixed(receipt, tokens)
                            
                            if transfers:
                                # Calculate volume
                                volume_usd = 0
                                tokens_involved = []
                                
                                if transfers:
                                    first_transfer = transfers[0]
                                    if first_transfer['token_info']:
                                        token_info = first_transfer['token_info']
                                        amount = first_transfer['amount'] / (10 ** token_info['decimals'])
                                        volume_usd = amount * token_info['price']
                                    
                                    # Collect all token symbols
                                    for transfer in transfers:
                                        if transfer['token_info']:
                                            tokens_involved.append(transfer['token_info']['symbol'])
                                
                                # Get timestamp
                                timestamp = block['timestamp']
                                readable_time = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(timestamp))
                                
                                tx_info = {
                                    'hash': tx['hash'].hex(),
                                    'block': block_num,
                                    'timestamp': readable_time,
                                    'from': tx['from'],
                                    'volume_usd': volume_usd,
                                    'tokens': list(set(tokens_involved)),
                                    'transfer_count': len(transfers)
                                }
                                
                                found_transactions.append(tx_info)
                                
                                volume_str = f"${volume_usd:.2f}" if volume_usd > 0 else "NO VOLUME"
                                print(f"   ✅ Found #{len(found_transactions)}: {tx['hash'].hex()[:10]}... {volume_str}")
                                
                        except Exception as e:
                            continue
                            
            except Exception as e:
                continue
                
            time.sleep(0.01)  # Rate limiting
            
        return found_transactions
        
    except Exception as e:
        print(f"Error: {e}")
        return []

def display_results(transactions: List[Dict]):
    """Display results in a formatted table"""
    
    if not transactions:
        print("❌ No transactions found")
        return
        
    print(f"\n🎯 Found {len(transactions)} ShapeShift Relay Transactions:")
    print("=" * 80)
    
    total_volume = 0
    volume_count = 0
    
    for i, tx in enumerate(transactions, 1):
        tokens_str = ','.join(tx['tokens'][:4]) if tx['tokens'] else 'Unknown'
        from_short = tx['from'][:6] + "..." + tx['from'][-4:]
        
        volume_str = f"${tx['volume_usd']:.2f}" if tx['volume_usd'] > 0 else "NO VOLUME"
        
        print(f"\n#{i}: {tx['hash']}")
        print(f"   Block: {tx['block']}")
        print(f"   Time: {tx['timestamp']}")
        print(f"   Volume: {volume_str}")
        print(f"   Tokens: {tokens_str}")
        print(f"   From: {from_short}")
        print(f"   Arbiscan: https://arbiscan.io/tx/{tx['hash']}")
        
        if tx['volume_usd'] > 0:
            total_volume += tx['volume_usd']
            volume_count += 1
    
    print("=" * 80)
    print(f"Total Volume: ${total_volume:,.2f} ({volume_count} transactions with volume)")
    if volume_count > 0:
        print(f"Average Volume: ${total_volume/volume_count:.2f}")
    
    # Show issues
    no_volume_count = len(transactions) - volume_count
    if no_volume_count > 0:
        print(f"\n⚠️  {no_volume_count} transactions show NO VOLUME")
        print("   Likely causes: Unknown tokens not in our price dictionary")

def main():
    # Initialize databases
    init_database()
    init_block_tracker()
    
    # Get start block from tracking system
    start_block = get_start_block(LISTENER_NAME, CHAIN)
    w3 = Web3(Web3.HTTPProvider(ARBITRUM_RPC))
    end_block = w3.eth.block_number
    
    print(f"🚀 Starting relay listener scan from block {start_block:,} to {end_block:,}")
    
    # Scan for transactions
    transactions = scan_blocks_for_shapeshift_transactions(start_block, end_block)
    
    # Save transactions and update block tracking
    save_transactions_to_db(transactions)
    set_last_processed_block(LISTENER_NAME, CHAIN, end_block)
    
    # Display results
    display_results(transactions)
    get_database_stats()

if __name__ == "__main__":
    main() 