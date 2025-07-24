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
import itertools
import argparse

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

BATCH_MODE = True  # Set to True to use batch log fetching
TRANSFER_EVENT_SIG = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'

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

def scan_blocks_for_shapeshift_transactions(start_block: int, end_block: int, max_count: int = None, batch_size: int = 1000) -> List[Dict]:
    """Scan forward in batches until max_count transactions are found or end_block is reached."""
    w3 = Web3(Web3.HTTPProvider(ARBITRUM_RPC))
    found_transactions = []
    current_block = start_block
    while current_block <= end_block:
        batch_end = min(current_block + batch_size - 1, end_block)
        try:
            # Get UTC times for batch
            try:
                start_ts = w3.eth.get_block(current_block)['timestamp']
                end_ts = w3.eth.get_block(batch_end)['timestamp']
                start_dt = datetime.utcfromtimestamp(start_ts).strftime('%Y-%m-%d %H:%M:%S')
                end_dt = datetime.utcfromtimestamp(end_ts).strftime('%Y-%m-%d %H:%M:%S')
            except Exception:
                start_dt = end_dt = 'N/A'
            logs = w3.eth.get_logs({
                'fromBlock': current_block,
                'toBlock': batch_end,
                'address': RELAY_CONTRACT,
                'topics': [TRANSFER_EVENT_SIG]
            })
            print(f"   📦 Fetched {len(logs)} logs in batch mode for blocks {current_block} to {batch_end} ({start_dt} UTC to {end_dt} UTC).")
            logs_by_tx = {}
            for log in logs:
                tx_hash = log['transactionHash'].hex()
                logs_by_tx.setdefault(tx_hash, []).append(log)
            for tx_hash, tx_logs in logs_by_tx.items():
                try:
                    receipt = w3.eth.get_transaction_receipt(tx_hash)
                    block = w3.eth.get_block(receipt['blockNumber'])
                    transfers = []
                    for log in tx_logs:
                        token_address = log['address'].lower()
                        token_info = tokens.get(token_address)
                        data_hex = log['data']
                        if data_hex.startswith('0x'):
                            data_hex = data_hex[2:]
                        amount = int(data_hex, 16) if data_hex else 0
                        transfers.append({
                            'token_address': token_address,
                            'token_info': token_info,
                            'amount': amount
                        })
                    # Calculate volume
                    volume_usd = 0
                    tokens_involved = []
                    if transfers:
                        first_transfer = transfers[0]
                        if first_transfer['token_info']:
                            token_info = first_transfer['token_info']
                            amount = first_transfer['amount'] / (10 ** token_info['decimals'])
                            volume_usd = amount * token_info['price']
                        for transfer in transfers:
                            if transfer['token_info']:
                                tokens_involved.append(transfer['token_info']['symbol'])
                    timestamp = block['timestamp']
                    readable_time = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(timestamp))
                    tx = w3.eth.get_transaction(tx_hash)
                    tx_info = {
                        'hash': tx_hash,
                        'block': receipt['blockNumber'],
                        'timestamp': readable_time,
                        'from': tx['from'],
                        'volume_usd': volume_usd,
                        'tokens': list(set(tokens_involved)),
                        'transfer_count': len(transfers)
                    }
                    found_transactions.append(tx_info)
                    volume_str = f"${volume_usd:.2f}" if volume_usd > 0 else "NO VOLUME"
                    print(f"   ✅ Found #{len(found_transactions)}: {tx_hash[:10]}... {volume_str}")
                except Exception as e:
                    print(f"   ❌ Error processing tx {tx_hash}: {e}")
                if max_count and len(found_transactions) >= max_count:
                    print(f"Reached max count of {max_count} transactions.")
                    return found_transactions
        except Exception as e:
            print(f"Error fetching logs for blocks {current_block}-{batch_end}: {e}")
        current_block = batch_end + 1
    return found_transactions

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

def get_block_by_timestamp(w3, target_ts: int) -> int:
    latest = w3.eth.block_number
    earliest = 1
    while earliest < latest:
        mid = (earliest + latest) // 2
        block = w3.eth.get_block(mid)
        if block['timestamp'] < target_ts:
            earliest = mid + 1
        else:
            latest = mid
    return earliest

def main():
    # Initialize databases
    init_database()
    init_block_tracker()
    parser = argparse.ArgumentParser(description='ShapeShift Relay Listener')
    parser.add_argument('--start-date', type=str, help="Start UTC date (e.g. '2024-07-13 00:00:00')")
    parser.add_argument('--end-date', type=str, help="End UTC date (e.g. '2024-07-14 00:00:00')")
    parser.add_argument('--count', type=int, help="Stop after finding this many ShapeShift transactions")
    args = parser.parse_args()
    w3 = Web3(Web3.HTTPProvider(ARBITRUM_RPC))
    # Determine start_block and end_block
    if args.start_date:
        start_ts = int(datetime.strptime(args.start_date, "%Y-%m-%d %H:%M:%S").timestamp())
        start_block = get_block_by_timestamp(w3, start_ts)
        if args.end_date:
            end_ts = int(datetime.strptime(args.end_date, "%Y-%m-%d %H:%M:%S").timestamp())
            end_block = get_block_by_timestamp(w3, end_ts)
        else:
            end_block = w3.eth.block_number
        print(f"🚀 Starting relay listener scan from block {start_block:,} to {end_block:,} (from {args.start_date} to {args.end_date or 'latest'} UTC)")
    else:
        start_block = get_start_block(LISTENER_NAME, CHAIN)
        end_block = w3.eth.block_number
        print(f"🚀 Starting relay listener scan from block {start_block:,} to {end_block:,}")
    # Scan for transactions
    transactions = scan_blocks_for_shapeshift_transactions(start_block, end_block, max_count=args.count)
    # Save transactions and update block tracking
    save_transactions_to_db(transactions)
    set_last_processed_block(LISTENER_NAME, CHAIN, end_block)
    # Display results
    display_results(transactions)
    get_database_stats()

if __name__ == "__main__":
    main() 