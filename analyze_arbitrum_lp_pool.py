import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import numpy as np
from web3 import Web3
import requests
import json

# Configuration
DB_PATH = 'arbitrum_weth_fox_events.db'  # You will need to create this DB with event data
PAIR_ADDRESS = '0x5f6ce0ca13b87bd738519545d3e018e70e339c24'
DAO_LP_TOKENS = 4414.3394  # DAO's LP token amount on Arbitrum
INFURA_URL = "https://arbitrum-mainnet.infura.io/v3/208a3474635e4ebe8ee409cef3fbcd40"

# Token addresses (Arbitrum)
WETH_ADDRESS = '0x82af49447d8a07e3bd95bd0d56f35241523fbab1'
FOX_ADDRESS = '0xc770eefad204b5180df6a14ee197d99d808ee52d'

def get_token_price(token_address, block_number=None):
    """Get token price in USD using CoinGecko API"""
    try:
        # Map addresses to CoinGecko IDs
        token_map = {
            WETH_ADDRESS: 'ethereum',
            FOX_ADDRESS: 'shapeshift-fox-token'
        }
        
        if token_address not in token_map:
            return 0
            
        coin_id = token_map[token_address]
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
        response = requests.get(url, timeout=10)
        data = response.json()
        return data[coin_id]['usd']
    except:
        fallback_prices = {
            WETH_ADDRESS: 3500,  # Approximate ETH price
            FOX_ADDRESS: 0.15    # Approximate FOX price
        }
        return fallback_prices.get(token_address, 0)

def get_pool_info():
    """Get current pool information"""
    w3 = Web3(Web3.HTTPProvider(INFURA_URL))
    
    pair_abi = [
        {
            "constant": True,
            "inputs": [],
            "name": "getReserves",
            "outputs": [
                {"name": "_reserve0", "type": "uint112"},
                {"name": "_reserve1", "type": "uint112"},
                {"name": "_blockTimestampLast", "type": "uint32"}
            ],
            "type": "function"
        },
        {
            "constant": True,
            "inputs": [],
            "name": "totalSupply",
            "outputs": [{"name": "", "type": "uint256"}],
            "type": "function"
        }
    ]
    
    # Convert to checksum address
    checksum_address = w3.to_checksum_address(PAIR_ADDRESS)
    contract = w3.eth.contract(address=checksum_address, abi=pair_abi)
    
    try:
        reserves = contract.functions.getReserves().call()
        total_supply = contract.functions.totalSupply().call()
        weth_reserve = reserves[0]
        fox_reserve = reserves[1]
        return {
            'weth_reserve': weth_reserve,
            'fox_reserve': fox_reserve,
            'total_supply': total_supply,
            'block_timestamp': reserves[2]
        }
    except Exception as e:
        print(f"Error getting pool info: {e}")
        return None

def load_burn_events():
    """Load burn events from database"""
    conn = sqlite3.connect(DB_PATH)
    query = """
    SELECT 
        block_number,
        tx_hash,
        sender,
        CAST(amount0 AS REAL) / 1e18 as weth_amount,
        CAST(amount1 AS REAL) / 1e18 as fox_amount,
        to_addr,
        timestamp
    FROM burn 
    ORDER BY block_number ASC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

def calculate_liquidity_impact():
    burns_df = load_burn_events()
    if burns_df.empty:
        print("No burn events found")
        return None
    pool_info = get_pool_info()
    if not pool_info:
        print("Could not get current pool info")
        return None
    weth_price = get_token_price(WETH_ADDRESS)
    fox_price = get_token_price(FOX_ADDRESS)
    current_weth_usd = (pool_info['weth_reserve'] / 1e18) * weth_price
    current_fox_usd = (pool_info['fox_reserve'] / 1e18) * fox_price
    current_total_usd = current_weth_usd + current_fox_usd
    print(f"Current pool reserves:")
    print(f"  WETH: {pool_info['weth_reserve'] / 1e18:.2f} (${current_weth_usd:,.2f})")
    print(f"  FOX: {pool_info['fox_reserve'] / 1e18:,.2f} (${current_fox_usd:,.2f})")
    print(f"  Total: ${current_total_usd:,.2f}")
    burns_df['weth_usd'] = burns_df['weth_amount'] * weth_price
    burns_df['fox_usd'] = burns_df['fox_amount'] * fox_price
    burns_df['total_usd'] = burns_df['weth_usd'] + burns_df['fox_usd']
    burns_df['cumulative_usd'] = burns_df['total_usd'].cumsum()
    total_removed_usd = burns_df['total_usd'].sum()
    original_total_usd = current_total_usd + total_removed_usd
    print(f"\nLiquidity analysis:")
    print(f"  Total removed: ${total_removed_usd:,.2f}")
    print(f"  Original total: ${original_total_usd:,.2f}")
    print(f"  Current total: ${current_total_usd:,.2f}")
    print(f"  Reduction: {total_removed_usd/original_total_usd*100:.1f}%")
    return burns_df, current_total_usd, original_total_usd

def calculate_dao_ownership():
    pool_info = get_pool_info()
    if not pool_info:
        return None
    total_supply = pool_info['total_supply'] / 1e18
    dao_percentage = (DAO_LP_TOKENS / total_supply) * 100
    weth_price = get_token_price(WETH_ADDRESS)
    fox_price = get_token_price(FOX_ADDRESS)
    current_weth_usd = (pool_info['weth_reserve'] / 1e18) * weth_price
    current_fox_usd = (pool_info['fox_reserve'] / 1e18) * fox_price
    current_total_usd = current_weth_usd + current_fox_usd
    dao_usd_value = current_total_usd * (dao_percentage / 100)
    print(f"\nDAO Ownership:")
    print(f"  DAO LP tokens: {DAO_LP_TOKENS:,.2f}")
    print(f"  Total LP supply: {total_supply:,.2f}")
    print(f"  DAO percentage: {dao_percentage:.2f}%")
    print(f"  DAO USD value: ${dao_usd_value:,.2f}")
    return dao_percentage, dao_usd_value

def create_visualizations():
    # Get current pool info and DAO ownership even if no burns
    pool_info = get_pool_info()
    if not pool_info:
        print("Could not get current pool info")
        return
    
    dao_percentage, dao_usd_value = calculate_dao_ownership()
    
    # Try to get burn events, but handle case where none exist
    result = calculate_liquidity_impact()
    if result:
        burns_df, current_total_usd, original_total_usd = result
        total_removed_usd = burns_df['total_usd'].sum()
    else:
        # No burns, use current pool info
        weth_price = get_token_price(WETH_ADDRESS)
        fox_price = get_token_price(FOX_ADDRESS)
        current_total_usd = (pool_info['weth_reserve'] / 1e18) * weth_price + (pool_info['fox_reserve'] / 1e18) * fox_price
        total_removed_usd = 0
        original_total_usd = current_total_usd
        burns_df = pd.DataFrame()  # Empty dataframe
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Arbitrum WETH/FOX LP Pool Analysis', fontsize=16, fontweight='bold')
    
    # 1. Liquidity removals over time
    if not burns_df.empty:
        ax1.plot(burns_df['timestamp'], burns_df['total_usd'], 'ro-', markersize=6, linewidth=2)
        ax1.set_title('Liquidity Removals Over Time', fontweight='bold')
        ax1.set_ylabel('USD Value Removed')
        ax1.set_xlabel('Date')
        ax1.grid(True, alpha=0.3)
        ax1.tick_params(axis='x', rotation=45)
        ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
    else:
        ax1.text(0.5, 0.5, 'No Liquidity Removals\nFound in Recent History', 
                ha='center', va='center', transform=ax1.transAxes, fontsize=14)
        ax1.set_title('Liquidity Removals Over Time', fontweight='bold')
    
    # 2. Cumulative liquidity removed
    if not burns_df.empty:
        ax2.plot(burns_df['timestamp'], burns_df['cumulative_usd'], 'b-', linewidth=3)
        ax2.axhline(y=total_removed_usd, color='red', linestyle='--', alpha=0.7, label=f'Total: ${total_removed_usd:,.0f}')
        ax2.set_title('Cumulative Liquidity Removed', fontweight='bold')
        ax2.set_ylabel('Cumulative USD Value')
        ax2.set_xlabel('Date')
        ax2.grid(True, alpha=0.3)
        ax2.legend()
        ax2.tick_params(axis='x', rotation=45)
        ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
    else:
        ax2.text(0.5, 0.5, 'No Cumulative Removals\n(No burns found)', 
                ha='center', va='center', transform=ax2.transAxes, fontsize=14)
        ax2.set_title('Cumulative Liquidity Removed', fontweight='bold')
    # 3. Pool liquidity comparison
    if total_removed_usd > 0:
        labels = ['Current Pool', 'Removed Liquidity']
        sizes = [current_total_usd, total_removed_usd]
        colors = ['lightblue', 'lightcoral']
        ax3.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
        ax3.set_title('Pool Liquidity Distribution', fontweight='bold')
    else:
        labels = ['Current Pool']
        sizes = [current_total_usd]
        colors = ['lightblue']
        ax3.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
        ax3.set_title('Current Pool Liquidity', fontweight='bold')
    dao_ownership_data = [dao_percentage, 100 - dao_percentage]
    dao_labels = ['DAO Ownership', 'Other Holders']
    dao_colors = ['gold', 'lightgray']
    bars = ax4.bar(dao_labels, dao_ownership_data, color=dao_colors)
    ax4.set_title('DAO LP Token Ownership', fontweight='bold')
    ax4.set_ylabel('Percentage (%)')
    ax4.set_ylim(0, 100)
    for bar, value in zip(bars, dao_ownership_data):
        height = bar.get_height()
        ax4.text(bar.get_x() + bar.get_width()/2., height + 1,
                f'{value:.1f}%', ha='center', va='bottom', fontweight='bold')
    if total_removed_usd > 0:
        metrics_text = f"""
Key Metrics:
• Total Removed: ${total_removed_usd:,.0f}
• Current Pool: ${current_total_usd:,.0f}
• DAO Value: ${dao_usd_value:,.0f}
• DAO %: {dao_percentage:.2f}%
• Reduction: {total_removed_usd/original_total_usd*100:.1f}%
        """
    else:
        metrics_text = f"""
Key Metrics:
• Total Removed: $0 (No burns found)
• Current Pool: ${current_total_usd:,.0f}
• DAO Value: ${dao_usd_value:,.0f}
• DAO %: {dao_percentage:.2f}%
• Reduction: 0% (No liquidity removed)
        """
    fig.text(0.02, 0.02, metrics_text, fontsize=10, 
             bbox=dict(boxstyle="round,pad=0.5", facecolor="lightyellow", alpha=0.8))
    plt.tight_layout()
    plt.savefig('arbitrum_weth_fox_lp_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()
    print("\n" + "="*80)
    print("DETAILED BURN EVENTS ANALYSIS")
    print("="*80)
    if not burns_df.empty:
        for idx, row in burns_df.iterrows():
            print(f"Burn #{idx+1} - {row['timestamp'].strftime('%Y-%m-%d %H:%M')}")
            print(f"  WETH: {row['weth_amount']:.4f} (${row['weth_usd']:,.2f})")
            print(f"  FOX: {row['fox_amount']:,.2f} (${row['fox_usd']:,.2f})")
            print(f"  Total: ${row['total_usd']:,.2f}")
            print(f"  Cumulative: ${row['cumulative_usd']:,.2f}")
            print(f"  TX: {row['tx_hash']}")
            print("-" * 60)
    else:
        print("No burn events found in the analyzed time period.")
        print("This could mean:")
        print("  - No liquidity has been removed recently")
        print("  - The pool is relatively new")
        print("  - All liquidity removals occurred outside the analyzed range")

if __name__ == "__main__":
    create_visualizations() 