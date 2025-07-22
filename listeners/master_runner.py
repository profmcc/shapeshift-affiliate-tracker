#!/usr/bin/env python3
"""
ShapeShift Affiliate Fee Master Runner
Executes all protocol listeners and consolidates data into a comprehensive database.
"""

import os
import sys
import sqlite3
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional
import argparse

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import all listeners
try:
    import relay_listener
    from portals_listener import PortalsListener
    from chainflip_listener import ChainflipBrokerListener
    from thorchain_listener import THORChainListener
    from cowswap_listener import CowSwapListener
    from zerox_listener import ZeroXListener
except ImportError as e:
    print(f"❌ Error importing listeners: {e}")
    print("Make sure all listener files are in the listeners/ directory")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MasterRunner:
    def __init__(self):
        self.comprehensive_db_path = "databases/comprehensive_affiliate.db"
        self.init_comprehensive_database()
        
        # Initialize all listeners
        self.listeners = {
            'portals': PortalsListener(db_path="databases/portals_transactions.db"),
            'chainflip': ChainflipBrokerListener(),
            'thorchain': THORChainListener(db_path="databases/thorchain_transactions.db"),
            'cowswap': CowSwapListener(db_path="databases/cowswap_transactions.db"),
            'zerox': ZeroXListener(db_path="databases/zerox_transactions.db")
        }

    def init_comprehensive_database(self):
        """Initialize the comprehensive database that combines all protocols"""
        os.makedirs(os.path.dirname(self.comprehensive_db_path), exist_ok=True)
        conn = sqlite3.connect(self.comprehensive_db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS comprehensive_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                protocol TEXT NOT NULL,
                chain TEXT NOT NULL,
                tx_hash TEXT NOT NULL,
                block_number INTEGER,
                timestamp INTEGER NOT NULL,
                from_asset TEXT,
                to_asset TEXT,
                from_amount REAL,
                to_amount REAL,
                from_amount_usd REAL,
                to_amount_usd REAL,
                volume_usd REAL,
                affiliate_fee_amount REAL,
                affiliate_fee_usd REAL,
                affiliate_fee_asset TEXT,
                affiliate_address TEXT,
                sender_address TEXT,
                recipient_address TEXT,
                event_type TEXT,
                raw_data TEXT,
                created_at INTEGER DEFAULT (strftime('%s', 'now')),
                UNIQUE(protocol, tx_hash, chain)
            )
        ''')
        
        # Create indexes for performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_protocol ON comprehensive_transactions(protocol)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_chain ON comprehensive_transactions(chain)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON comprehensive_transactions(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tx_hash ON comprehensive_transactions(tx_hash)')
        
        conn.commit()
        conn.close()
        logger.info(f"✅ Comprehensive database initialized: {self.comprehensive_db_path}")

    def run_all_listeners(self, blocks_to_scan: int = 2000, limit: int = 100):
        """Run all protocol listeners"""
        logger.info("🚀 Starting Master Runner - All Protocol Listeners")
        
        results = {}
        start_time = time.time()
        
        # Run relay listener first (module-based)
        logger.info(f"\n{'='*60}")
        logger.info(f"🔍 Running RELAY listener...")
        logger.info(f"{'='*60}")
        
        try:
            protocol_start = time.time()
            relay_listener.init_database()
            transactions = relay_listener.find_last_20_shapeshift_transactions()
            relay_listener.save_transactions_to_db(transactions)
            protocol_time = time.time() - protocol_start
            results['relay'] = {
                'status': 'success',
                'time': protocol_time,
                'error': None
            }
            logger.info(f"✅ RELAY completed in {protocol_time:.2f}s")
        except Exception as e:
            protocol_time = time.time() - protocol_start
            results['relay'] = {
                'status': 'error',
                'time': protocol_time,
                'error': str(e)
            }
            logger.error(f"❌ RELAY failed: {e}")
        
        # Run class-based listeners
        for protocol, listener in self.listeners.items():
            logger.info(f"\n{'='*60}")
            logger.info(f"🔍 Running {protocol.upper()} listener...")
            logger.info(f"{'='*60}")
            
            try:
                protocol_start = time.time()
                
                if protocol in ['thorchain', 'chainflip']:
                    # API-based listeners use limit
                    listener.run_listener(limit)
                else:
                    # Blockchain listeners use blocks_to_scan
                    listener.run_listener(blocks_to_scan)
                
                protocol_time = time.time() - protocol_start
                results[protocol] = {
                    'status': 'success',
                    'time': protocol_time,
                    'error': None
                }
                logger.info(f"✅ {protocol.upper()} completed in {protocol_time:.2f}s")
                
            except Exception as e:
                protocol_time = time.time() - protocol_start
                results[protocol] = {
                    'status': 'error',
                    'time': protocol_time,
                    'error': str(e)
                }
                logger.error(f"❌ {protocol.upper()} failed: {e}")
                
        total_time = time.time() - start_time
        
        # Print summary
        self.print_execution_summary(results, total_time)
        
        return results

    def consolidate_databases(self):
        """Consolidate all protocol databases into comprehensive database"""
        logger.info("\n🔄 Consolidating databases...")
        
        # Database mapping and consolidation logic
        consolidation_map = {
            'relay': {
                'source_db': 'databases/relay_transactions.db',
                'source_table': 'relay_transactions',
                'protocol': 'Relay'
            },
            'portals': {
                'source_db': 'databases/portals_transactions.db',
                'source_table': 'portals_transactions',
                'protocol': 'Portals'
            },
            'chainflip': {
                'source_db': 'databases/chainflip_transactions.db',
                'source_table': 'transactions',  # Chainflip uses different table name
                'protocol': 'Chainflip'
            },
            'thorchain': {
                'source_db': 'databases/thorchain_transactions.db',
                'source_table': 'thorchain_transactions',
                'protocol': 'THORChain'
            },
            'cowswap': {
                'source_db': 'databases/cowswap_transactions.db',
                'source_table': 'cowswap_transactions',
                'protocol': 'CowSwap'
            },
            'zerox': {
                'source_db': 'databases/zerox_transactions.db',
                'source_table': 'zerox_transactions',
                'protocol': '0x Protocol'
            }
        }
        
        comp_conn = sqlite3.connect(self.comprehensive_db_path)
        comp_cursor = comp_conn.cursor()
        
        total_consolidated = 0
        
        for protocol_key, config in consolidation_map.items():
            if not os.path.exists(config['source_db']):
                logger.warning(f"⚠️ {config['protocol']} database not found: {config['source_db']}")
                continue
                
            try:
                # Connect to source database
                source_conn = sqlite3.connect(config['source_db'])
                source_cursor = source_conn.cursor()
                
                # Check if table exists
                source_cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{config['source_table']}'")
                if not source_cursor.fetchone():
                    logger.warning(f"⚠️ Table {config['source_table']} not found in {config['protocol']} database")
                    source_conn.close()
                    continue
                
                # Get all transactions from source
                source_cursor.execute(f"SELECT * FROM {config['source_table']}")
                rows = source_cursor.fetchall()
                
                # Get column names
                source_cursor.execute(f"PRAGMA table_info({config['source_table']})")
                columns = [row[1] for row in source_cursor.fetchall()]
                
                # Map to comprehensive schema
                for row in rows:
                    row_dict = dict(zip(columns, row))
                    consolidated_row = self.map_to_comprehensive_schema(row_dict, config['protocol'])
                    
                    if consolidated_row:
                        comp_cursor.execute('''
                            INSERT OR IGNORE INTO comprehensive_transactions 
                            (protocol, chain, tx_hash, block_number, timestamp, from_asset, to_asset,
                             from_amount, to_amount, from_amount_usd, to_amount_usd, volume_usd,
                             affiliate_fee_amount, affiliate_fee_usd, affiliate_fee_asset, affiliate_address,
                             sender_address, recipient_address, event_type, raw_data)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            consolidated_row['protocol'], consolidated_row['chain'], consolidated_row['tx_hash'],
                            consolidated_row['block_number'], consolidated_row['timestamp'], consolidated_row['from_asset'],
                            consolidated_row['to_asset'], consolidated_row['from_amount'], consolidated_row['to_amount'],
                            consolidated_row['from_amount_usd'], consolidated_row['to_amount_usd'], consolidated_row['volume_usd'],
                            consolidated_row['affiliate_fee_amount'], consolidated_row['affiliate_fee_usd'],
                            consolidated_row['affiliate_fee_asset'], consolidated_row['affiliate_address'],
                            consolidated_row['sender_address'], consolidated_row['recipient_address'],
                            consolidated_row['event_type'], consolidated_row['raw_data']
                        ))
                        total_consolidated += 1
                
                source_conn.close()
                logger.info(f"✅ Consolidated {len(rows)} {config['protocol']} transactions")
                
            except Exception as e:
                logger.error(f"❌ Error consolidating {config['protocol']}: {e}")
                
        comp_conn.commit()
        comp_conn.close()
        
        logger.info(f"💾 Total consolidated transactions: {total_consolidated}")

    def map_to_comprehensive_schema(self, row_dict: Dict, protocol: str) -> Optional[Dict]:
        """Map protocol-specific row to comprehensive schema"""
        try:
            # Base mapping - adapt based on actual column names in each protocol
            mapped = {
                'protocol': protocol,
                'chain': row_dict.get('chain', 'unknown'),
                'tx_hash': row_dict.get('tx_hash', row_dict.get('transaction_hash', '')),
                'block_number': row_dict.get('block_number', 0),
                'timestamp': row_dict.get('timestamp', row_dict.get('block_timestamp', 0)),
                'from_asset': row_dict.get('from_asset', row_dict.get('input_token', row_dict.get('sell_token', ''))),
                'to_asset': row_dict.get('to_asset', row_dict.get('output_token', row_dict.get('buy_token', ''))),
                'from_amount': self.safe_float(row_dict.get('from_amount', row_dict.get('input_amount', 0))),
                'to_amount': self.safe_float(row_dict.get('to_amount', row_dict.get('output_amount', 0))),
                'from_amount_usd': self.safe_float(row_dict.get('from_amount_usd', 0)),
                'to_amount_usd': self.safe_float(row_dict.get('to_amount_usd', 0)),
                'volume_usd': self.safe_float(row_dict.get('volume_usd', 0)),
                'affiliate_fee_amount': self.safe_float(row_dict.get('affiliate_fee_amount', 0)),
                'affiliate_fee_usd': self.safe_float(row_dict.get('affiliate_fee_usd', 0)),
                'affiliate_fee_asset': row_dict.get('affiliate_fee_asset', ''),
                'affiliate_address': row_dict.get('affiliate_address', row_dict.get('partner', '')),
                'sender_address': row_dict.get('sender', row_dict.get('from_address', '')),
                'recipient_address': row_dict.get('recipient', row_dict.get('to_address', '')),
                'event_type': row_dict.get('event_type', 'transaction'),
                'raw_data': str(row_dict)
            }
            
            return mapped
            
        except Exception as e:
            logger.error(f"Error mapping row for {protocol}: {e}")
            return None

    def safe_float(self, value) -> float:
        """Safely convert value to float"""
        try:
            if isinstance(value, str):
                # Handle string representations of large numbers
                if value.isdigit():
                    return float(value)
                return float(value) if value else 0.0
            return float(value) if value else 0.0
        except:
            return 0.0

    def print_execution_summary(self, results: Dict, total_time: float):
        """Print execution summary"""
        logger.info(f"\n{'='*80}")
        logger.info("📊 MASTER RUNNER EXECUTION SUMMARY")
        logger.info(f"{'='*80}")
        
        successful = sum(1 for r in results.values() if r['status'] == 'success')
        failed = len(results) - successful
        
        logger.info(f"⏱️  Total Execution Time: {total_time:.2f}s")
        logger.info(f"✅ Successful Listeners: {successful}/{len(results)}")
        logger.info(f"❌ Failed Listeners: {failed}")
        
        logger.info(f"\n📋 Individual Results:")
        for protocol, result in results.items():
            status_emoji = "✅" if result['status'] == 'success' else "❌"
            logger.info(f"   {status_emoji} {protocol.upper()}: {result['time']:.2f}s")
            if result['error']:
                logger.info(f"      Error: {result['error']}")

    def get_comprehensive_stats(self):
        """Get comprehensive database statistics"""
        conn = sqlite3.connect(self.comprehensive_db_path)
        cursor = conn.cursor()
        
        logger.info(f"\n{'='*80}")
        logger.info("📊 COMPREHENSIVE DATABASE STATISTICS")
        logger.info(f"{'='*80}")
        
        # Total transactions
        cursor.execute("SELECT COUNT(*) FROM comprehensive_transactions")
        total_tx = cursor.fetchone()[0]
        logger.info(f"📈 Total Transactions: {total_tx:,}")
        
        # By protocol
        cursor.execute("SELECT protocol, COUNT(*) FROM comprehensive_transactions GROUP BY protocol ORDER BY COUNT(*) DESC")
        protocol_stats = cursor.fetchall()
        logger.info(f"\n📊 Transactions by Protocol:")
        for protocol, count in protocol_stats:
            logger.info(f"   {protocol}: {count:,}")
        
        # By chain
        cursor.execute("SELECT chain, COUNT(*) FROM comprehensive_transactions GROUP BY chain ORDER BY COUNT(*) DESC")
        chain_stats = cursor.fetchall()
        logger.info(f"\n🔗 Transactions by Chain:")
        for chain, count in chain_stats:
            logger.info(f"   {chain}: {count:,}")
        
        # Financial stats
        cursor.execute("SELECT SUM(affiliate_fee_usd), SUM(volume_usd) FROM comprehensive_transactions")
        total_fees, total_volume = cursor.fetchone()
        total_fees = total_fees or 0
        total_volume = total_volume or 0
        
        logger.info(f"\n💰 Financial Summary:")
        logger.info(f"   Total Affiliate Fees: ${total_fees:,.2f}")
        logger.info(f"   Total Volume: ${total_volume:,.2f}")
        
        conn.close()

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='ShapeShift Affiliate Fee Master Runner')
    parser.add_argument('--blocks', type=int, default=2000, help='Number of blocks to scan for blockchain listeners')
    parser.add_argument('--limit', type=int, default=100, help='Number of records to fetch for API listeners')
    parser.add_argument('--skip-consolidation', action='store_true', help='Skip database consolidation')
    parser.add_argument('--consolidate-only', action='store_true', help='Only run database consolidation')
    parser.add_argument('--stats-only', action='store_true', help='Only show comprehensive statistics')
    
    args = parser.parse_args()
    
    runner = MasterRunner()
    
    if args.stats_only:
        runner.get_comprehensive_stats()
        return
    
    if not args.consolidate_only:
        # Run all listeners
        results = runner.run_all_listeners(args.blocks, args.limit)
    
    if not args.skip_consolidation:
        # Consolidate databases
        runner.consolidate_databases()
    
    # Show final statistics
    runner.get_comprehensive_stats()

if __name__ == "__main__":
    main() 