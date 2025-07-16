#!/usr/bin/env python3
"""
ShapeShift FOX Pool Analyzer
Analyzes all FOX pools across different chains and calculates total USD values.
"""

import os
import sqlite3
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from web3 import Web3
import requests
from eth_abi import decode
import logging
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
DB_PATH = 'fox_pools_analysis.db'

# FOX token address
FOX_TOKEN = '0xc770EEfAd204B5180dF6a14Ee197D99d808ee52d'

# All FOX pools with their details
FOX_POOLS = {
    # Arbitrum
    'arbitrum': {
        'rpc': 'https://arb1.arbitrum.io/rpc',
        'pools': [
            {
                'address': '0x5f6ce0ca13b87bd738519545d3e018e70e339c24',
                'name': 'WETH/FOX V2',
                'total_usd': 117966.027662768,
                'fox_balance': 2674852.29310537,
                'other_balance': 22.587717462,
                'chain_id': 42161
            },
            {
                'address': '0x76d4d1eaa0c4b3645e75c46e573c1d4f75e9041e',
                'name': 'WETH/FOX V3',
                'total_usd': 29574.048272938,
                'fox_balance': 1061271.70578409,
                'other_balance': 2.03303994,
                'chain_id': 42161
            }
        ]
    },
    # Ethereum
    'ethereum': {
        'rpc': 'https://eth.llamarpc.com',
        'pools': [
            {
                'address': '0xad0e10df5dcdf21396b9d64715aadaf543f8b376',
                'name': 'GIV/FOX',
                'total_usd': 0.000544369598,
                'fox_balance': 0.001849,
                'other_balance': 0.080447,
                'chain_id': 1
            },
            {
                'address': '0x470e8de2ebaef52014a47cb5e6af86884947f08c',
                'name': 'WETH/FOX',
                'total_usd': 3060022.47229936,
                'fox_balance': 67483795.582372,
                'other_balance': 603.025796238,
                'chain_id': 1
            }
        ]
    },
    # Gnosis
    'gnosis': {
        'rpc': 'https://rpc.gnosischain.com',
        'pools': [
            {
                'address': '0x75594f01da2e4231e16e67f841c307c4df2313d1',
                'name': 'GIV/FOX',
                'total_usd': 102.200770336,
                'fox_balance': 2331.940359486,
                'other_balance': 27934.545962764,
                'chain_id': 100
            },
            {
                'address': '0xc22313fd39f7d4d73a89558f9e8e444c86464bac',
                'name': 'wxDAI/FOX',
                'total_usd': 56700.699068726,
                'fox_balance': 1232278.01709655,
                'other_balance': 28525.598497296,
                'chain_id': 100
            },
            {
                'address': '0x8a0bee989c591142414ad67fb604539d917889df',
                'name': 'HNY/FOX',
                'total_usd': 6839.163901991,
                'fox_balance': 148869.898694018,
                'other_balance': 2012.803498026,
                'chain_id': 100
            }
        ]
    },
    # Polygon
    'polygon': {
        'rpc': 'https://polygon-rpc.com',
        'pools': [
            {
                'address': '0x93ef615f1ddd27d0e141ad7192623a5c45e8f200',
                'name': 'WETH/FOX',
                'total_usd': 83484.628841133,
                'fox_balance': 1815610.43843394,
                'other_balance': 16.681529829,
                'chain_id': 137
            }
        ]
    }
}

# Event signatures for different pool types
EVENT_SIGNATURES = {
    'uniswap_v2': {
        'sync': '0x1c411e9a96e071241c2f21f7726b17ae89e3cab4c78be50e062b03a9fffbbad1'
    },
    'uniswap_v3': {
        'increase_liquidity': '0x3067048beee31b25b2f1681f88dac838c8bba36af25bfb2b7cf7473a5847e35f',
        'decrease_liquidity': '0x26f6a048ee9138f2c0ce266f322cb99228e8d619ae2bff30c67f8dcf9d2377b4',
        'collect': '0x40d0efd1a53d60ecbf40971b9d9e18502887ace780a0564668d6d65605f3c5de'
    }
}

def setup_database():
    """Create the database and tables for FOX pool analysis"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # FOX pool summary table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fox_pool_summary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chain_name TEXT,
            pool_address TEXT,
            pool_name TEXT,
            total_usd_value REAL,
            fox_balance REAL,
            other_balance REAL,
            chain_id INTEGER,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # FOX LP activity table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fox_lp_activity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chain_name TEXT,
            pool_address TEXT,
            pool_name TEXT,
            period TEXT,
            total_adds REAL,
            total_removes REAL,
            net_change REAL,
            unique_lps INTEGER,
            start_date TEXT,
            end_date TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Chain summary table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chain_summary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chain_name TEXT,
            total_usd_value REAL,
            total_fox_balance REAL,
            pool_count INTEGER,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("FOX pool analysis database setup complete")

def populate_pool_data():
    """Populate the database with the provided FOX pool data"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    for chain_name, chain_data in FOX_POOLS.items():
        for pool in chain_data['pools']:
            cursor.execute('''
                INSERT OR REPLACE INTO fox_pool_summary
                (chain_name, pool_address, pool_name, total_usd_value, fox_balance, 
                 other_balance, chain_id, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                chain_name, pool['address'], pool['name'], pool['total_usd'],
                pool['fox_balance'], pool['other_balance'], pool['chain_id'], datetime.now()
            ))
    
    conn.commit()
    conn.close()
    logger.info("FOX pool data populated")

def calculate_chain_totals():
    """Calculate total USD values for each chain"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    for chain_name, chain_data in FOX_POOLS.items():
        total_usd = sum(pool['total_usd'] for pool in chain_data['pools'])
        total_fox = sum(pool['fox_balance'] for pool in chain_data['pools'])
        pool_count = len(chain_data['pools'])
        
        cursor.execute('''
            INSERT OR REPLACE INTO chain_summary
            (chain_name, total_usd_value, total_fox_balance, pool_count, last_updated)
            VALUES (?, ?, ?, ?, ?)
        ''', (chain_name, total_usd, total_fox, pool_count, datetime.now()))
    
    conn.commit()
    conn.close()
    logger.info("Chain totals calculated")

def create_activity_analysis():
    """Create activity analysis for different time periods"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    periods = [
        (3, "3_days"),
        (7, "7_days"),
        (14, "14_days"),
        (30, "30_days"),
        (90, "90_days")
    ]
    
    for chain_name, chain_data in FOX_POOLS.items():
        for pool in chain_data['pools']:
            for days, period_name in periods:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=days)
                
                # For now, we'll use placeholder data since we don't have historical events
                # In a real implementation, you'd query actual LP events
                total_adds = 0
                total_removes = 0
                net_change = 0
                unique_lps = 0
                
                cursor.execute('''
                    INSERT OR REPLACE INTO fox_lp_activity
                    (chain_name, pool_address, pool_name, period, total_adds, total_removes,
                     net_change, unique_lps, start_date, end_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    chain_name, pool['address'], pool['name'], period_name,
                    total_adds, total_removes, net_change, unique_lps,
                    start_date.isoformat(), end_date.isoformat()
                ))
    
    conn.commit()
    conn.close()
    logger.info("Activity analysis created")

def display_results():
    """Display comprehensive FOX pool analysis results"""
    conn = sqlite3.connect(DB_PATH)
    
    print("\n" + "="*100)
    print("FOX POOL ANALYSIS - TOTAL USD VALUES BY CHAIN")
    print("="*100)
    
    # Chain summary
    df_chain = pd.read_sql_query('''
        SELECT chain_name, total_usd_value, total_fox_balance, pool_count
        FROM chain_summary
        ORDER BY total_usd_value DESC
    ''', conn)
    
    if not df_chain.empty:
        print(df_chain.to_string(index=False, float_format='%.2f'))
    else:
        print("No chain data available")
    
    print("\n" + "="*100)
    print("FOX POOL DETAILS BY CHAIN")
    print("="*100)
    
    # Pool details
    df_pools = pd.read_sql_query('''
        SELECT chain_name, pool_name, total_usd_value, fox_balance, other_balance
        FROM fox_pool_summary
        ORDER BY chain_name, total_usd_value DESC
    ''', conn)
    
    if not df_pools.empty:
        print(df_pools.to_string(index=False, float_format='%.2f'))
    else:
        print("No pool data available")
    
    print("\n" + "="*100)
    print("FOX LP ACTIVITY ANALYSIS (Last 3, 7, 14, 30, 90 Days)")
    print("="*100)
    
    # Activity analysis
    df_activity = pd.read_sql_query('''
        SELECT chain_name, pool_name, period, total_adds, total_removes, net_change, unique_lps
        FROM fox_lp_activity
        ORDER BY chain_name, pool_name, period
    ''', conn)
    
    if not df_activity.empty:
        print(df_activity.to_string(index=False, float_format='%.2f'))
    else:
        print("No activity data available")
    
    # Calculate grand totals
    total_usd = df_chain['total_usd_value'].sum() if not df_chain.empty else 0
    total_fox = df_chain['total_fox_balance'].sum() if not df_chain.empty else 0
    total_pools = df_chain['pool_count'].sum() if not df_chain.empty else 0
    
    print("\n" + "="*100)
    print("GRAND TOTALS")
    print("="*100)
    print(f"Total USD Value Across All Chains: ${total_usd:,.2f}")
    print(f"Total FOX Balance Across All Chains: {total_fox:,.2f} FOX")
    print(f"Total Number of Pools: {total_pools}")
    
    conn.close()

def main():
    """Main function to run the FOX pool analyzer"""
    logger.info("Starting FOX pool analyzer")
    
    setup_database()
    populate_pool_data()
    calculate_chain_totals()
    create_activity_analysis()
    display_results()
    
    logger.info("FOX pool analysis complete!")

if __name__ == "__main__":
    main() 