#!/usr/bin/env python3
"""
DAO Treasury FOX Pool Ownership Analysis
Analyzes how much of each FOX pool liquidity is owned by the DAO treasury addresses.
"""

import os
import sqlite3
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from web3 import Web3
import requests
import pandas as pd
from web3.middleware.proof_of_authority import ExtraDataToPOAMiddleware
from eth_abi import decode

# Configure logging
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
DB_PATH = 'fox_pools_analysis.db'

# DAO Treasury Addresses from Zapper link
DAO_TREASURY_ADDRESSES = {
    'ethereum': Web3.to_checksum_address('0x90a48d5cf7343b08da12e067680b4c6dbfe551be'),
    'optimism': Web3.to_checksum_address('0x6268d07327f4fb7380732dc6d63d95f88c0e083b'),
    'avalanche': Web3.to_checksum_address('0x74d63f31c2335b5b3ba7ad2812357672b2624ced'),
    'polygon': Web3.to_checksum_address('0xb5f944600785724e31edb90f9dfa16dbf01af000'),
    'bsc': Web3.to_checksum_address('0xb0e3175341794d1dc8e5f02a02f9d26989ebedb3'),
    'bsc_alt': Web3.to_checksum_address('0x8b92b1698b57bedf2142297e9397875adbb2297e'),
    'arbitrum': Web3.to_checksum_address('0x38276553f8fbf2a027d901f8be45f00373d8dd48'),
    'base': Web3.to_checksum_address('0x5c59d0ec51729e40c413903be6a4612f4e2452da'),
    'base_alt': Web3.to_checksum_address('0x9c9aa90363630d4ab1d9dbf416cc3bbc8d3ed502'),
    'gnosis': Web3.to_checksum_address('0x90a48d5cf7343b08da12e067680b4c6dbfe551be'),  # Using Ethereum address for Gnosis
    'solana': 'C7RTJbss7R1r7j8NUNYbasUXfbPJR99PMhqznvCiU43N'
}

# RPC endpoints
RPC_ENDPOINTS = {
    'ethereum': 'https://eth.llamarpc.com',
    'arbitrum': 'https://arb1.arbitrum.io/rpc',
    'polygon': 'https://polygon-rpc.com',
    'gnosis': 'https://rpc.gnosischain.com'
}

# FOX token address
FOX_TOKEN = '0xc770EEfAd204B5180dF6a14Ee197D99d808ee52d'

# FOX pools to analyze
FOX_POOLS = [
    # Uniswap V2 WETH/FOX on Ethereum
    {
        'chain_name': 'ethereum',
        'pool_address': Web3.to_checksum_address('0x470e8de2ebaef52014a47cb5e6af86884947f08c'),
        'pool_name': 'WETH/FOX V2',
        'type': 'uniswap_v2',
        'rpc': 'https://eth.llamarpc.com'
    },
    # Uniswap V2 WETH/FOX on Arbitrum
    {
        'chain_name': 'arbitrum',
        'pool_address': Web3.to_checksum_address('0x5f6ce0ca13b87bd738519545d3e018e70e339c24'),
        'pool_name': 'WETH/FOX V2',
        'type': 'uniswap_v2',
        'rpc': 'https://arb1.arbitrum.io/rpc'
    },
    # Uniswap V3 WETH/FOX on Arbitrum
    {
        'chain_name': 'arbitrum',
        'pool_address': Web3.to_checksum_address('0x76d4d1eaa0c4b3645e75c46e573c1d4f75e9041e'),
        'pool_name': 'WETH/FOX V3',
        'type': 'uniswap_v3',
        'rpc': 'https://arb1.arbitrum.io/rpc'
    },
    # Lido stETH on Ethereum
    {
        'chain_name': 'ethereum',
        'pool_address': Web3.to_checksum_address('0xae7ab96520de3a18e5e111b5eaab095312d7fe84'),
        'pool_name': 'Lido stETH',
        'type': 'erc20',
        'rpc': 'https://eth.llamarpc.com'
    },
    # Velodrome V2 wstETH/FOX on Optimism
    {
        'chain_name': 'optimism',
        'pool_address': Web3.to_checksum_address('0x20a068f6940b28338363e8b01b07c21c1d5f197b'),
        'pool_name': 'Velodrome V2 wstETH/FOX',
        'type': 'erc20',
        'rpc': 'https://mainnet.optimism.io'
    },
]

# Uniswap V3 NFT Position Manager address (same on mainnet, Arbitrum, Polygon)
UNIV3_NFT_MANAGER = Web3.to_checksum_address('0xC36442b4a4522E871399CD717aBDD847Ab11FE88')

# Uniswap V3 NFT ABI fragments
UNIV3_NFT_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [
            {"name": "owner", "type": "address"},
            {"name": "index", "type": "uint256"}
        ],
        "name": "tokenOfOwnerByIndex",
        "outputs": [{"name": "tokenId", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [{"name": "tokenId", "type": "uint256"}],
        "name": "positions",
        "outputs": [
            {"name": "nonce", "type": "uint96"},
            {"name": "operator", "type": "address"},
            {"name": "token0", "type": "address"},
            {"name": "token1", "type": "address"},
            {"name": "fee", "type": "uint24"},
            {"name": "tickLower", "type": "int24"},
            {"name": "tickUpper", "type": "int24"},
            {"name": "liquidity", "type": "uint128"},
            {"name": "feeGrowthInside0LastX128", "type": "uint256"},
            {"name": "feeGrowthInside1LastX128", "type": "uint256"},
            {"name": "tokensOwed0", "type": "uint128"},
            {"name": "tokensOwed1", "type": "uint128"}
        ],
        "type": "function"
    }
]

UNISWAP_V2_ABI = [
    {"constant": True, "inputs": [], "name": "getReserves", "outputs": [
        {"name": "_reserve0", "type": "uint112"},
        {"name": "_reserve1", "type": "uint112"},
        {"name": "_blockTimestampLast", "type": "uint32"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "totalSupply", "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "token0", "outputs": [{"name": "", "type": "address"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "token1", "outputs": [{"name": "", "type": "address"}], "type": "function"},
]

def get_web3_connection(rpc_url: str) -> Web3:
    """Get Web3 connection"""
    try:
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        # Add POA middleware for Arbitrum/Polygon
        if 'arbitrum' in rpc_url or 'polygon' in rpc_url:
            w3.middleware_onion.add(ExtraDataToPOAMiddleware)
        w3.eth.block_number  # Test connection
        logger.info(f"Connected to {rpc_url}")
        return w3
    except Exception as e:
        logger.error(f"Failed to connect to {rpc_url}: {e}")
        raise

def get_token_balance(w3: Web3, token_address: str, wallet_address: str) -> float:
    """Get token balance for a wallet using ERC20 ABI"""
    try:
        erc20_abi = [{
            "constant": True,
            "inputs": [{"name": "owner", "type": "address"}],
            "name": "balanceOf",
            "outputs": [{"name": "balance", "type": "uint256"}],
            "type": "function"
        }]
        contract = w3.eth.contract(address=token_address, abi=erc20_abi)
        balance = contract.functions.balanceOf(wallet_address).call()
        return balance / 1e18
    except Exception as e:
        logger.error(f"Error getting balance for {wallet_address} on {token_address}: {e}")
        return 0

def get_token_price_coingecko(token_address: str, chain: str) -> float:
    """Fetch token price in USD from Coingecko by contract address and chain."""
    coingecko_chain = {
        'ethereum': 'ethereum',
        'arbitrum': 'arbitrum-one',
        'optimism': 'optimism',
        'polygon': 'polygon-pos',
        'gnosis': 'xdai',
    }.get(chain, 'ethereum')
    url = f"https://api.coingecko.com/api/v3/simple/token_price/{coingecko_chain}?contract_addresses={token_address}&vs_currencies=usd"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        if not data:
            return 0.0
        price_info = list(data.values())[0]
        if 'usd' in price_info:
            return price_info['usd']
        else:
            return 0.0
    except Exception as e:
        logger.error(f"Error fetching price for {token_address} on {chain}: {e}")
        return 0.0

def get_pool_info(w3: Web3, pool_address: str, pool_type: str) -> Optional[Dict]:
    """Get pool information including total supply and reserves"""
    try:
        if pool_type == 'uniswap_v2':
            # Get total supply
            total_supply = w3.eth.call({
                'to': pool_address,
                'data': w3.keccak(text='totalSupply()')[:4]
            })
            total_supply = int.from_bytes(total_supply, 'big') / 1e18
            
            # Get reserves
            reserves = w3.eth.call({
                'to': pool_address,
                'data': w3.keccak(text='getReserves()')[:4]
            })
            
            # Parse reserves (uint112, uint112, uint32)
            reserve0 = int.from_bytes(reserves[:16], 'big')
            reserve1 = int.from_bytes(reserves[16:32], 'big')
            
            return {
                'total_supply': total_supply,
                'reserve0': reserve0,
                'reserve1': reserve1
            }
            
        elif pool_type == 'uniswap_v3':
            # For V3, we need to get liquidity from positions
            # This is more complex, so we'll use a simplified approach
            return {
                'total_supply': 0,  # V3 doesn't have LP tokens in the same way
                'reserve0': 0,
                'reserve1': 0
            }
            
    except Exception as e:
        logger.error(f"Error getting pool info for {pool_address}: {e}")
        return None

def get_univ3_dao_liquidity(w3: Web3, dao_address: str, fox_pool_address: str) -> Tuple[float, int]:
    """Get total Uniswap V3 liquidity for DAO in a FOX pool (by summing NFT positions)"""
    nft = w3.eth.contract(address=UNIV3_NFT_MANAGER, abi=UNIV3_NFT_ABI)
    try:
        balance = nft.functions.balanceOf(dao_address).call()
        total_liquidity = 0
        position_count = 0
        for i in range(balance):
            token_id = nft.functions.tokenOfOwnerByIndex(dao_address, i).call()
            pos = nft.functions.positions(token_id).call()
            pool_addr = get_univ3_pool_address(w3, pos[2], pos[3], pos[4])
            if pool_addr.lower() == fox_pool_address.lower():
                total_liquidity += pos[7]
                position_count += 1
        return total_liquidity, position_count
    except Exception as e:
        logger.error(f"Error fetching Uniswap V3 NFT positions: {e}")
        return 0, 0

def get_univ3_pool_address(w3: Web3, token0: str, token1: str, fee: int) -> str:
    """Get Uniswap V3 pool address for token0, token1, fee"""
    # Uniswap V3 factory address per chain
    FACTORY = {
        1: Web3.to_checksum_address('0x1F98431c8aD98523631AE4a59f267346ea31F984'),
        42161: Web3.to_checksum_address('0x1F98431c8aD98523631AE4a59f267346ea31F984'),
        137: Web3.to_checksum_address('0x0227628f3F023bb0B980b67D528571c95c6DaC1c'),
    }
    chain_id = w3.eth.chain_id
    factory = FACTORY.get(chain_id)
    if not factory:
        return ''
    # Pool address = keccak(0xff ++ factory ++ keccak(token0, token1, fee) ++ init_code_hash)[12:]
    # We'll use the Uniswap V3 factory contract to get the pool address
    factory_abi = [{
        "inputs": [
            {"internalType": "address", "name": "tokenA", "type": "address"},
            {"internalType": "address", "name": "tokenB", "type": "address"},
            {"internalType": "uint24", "name": "fee", "type": "uint24"}
        ],
        "name": "getPool",
        "outputs": [{"internalType": "address", "name": "pool", "type": "address"}],
        "stateMutability": "view",
        "type": "function"
    }]
    factory_contract = w3.eth.contract(address=factory, abi=factory_abi)
    try:
        pool_addr = factory_contract.functions.getPool(token0, token1, fee).call()
        return pool_addr
    except Exception:
        # Try reversed order
        try:
            pool_addr = factory_contract.functions.getPool(token1, token0, fee).call()
            return pool_addr
        except Exception:
            return ''

def analyze_dao_ownership():
    """Analyze DAO ownership across all FOX pools"""
    results = []
    
    print("\n" + "="*100)
    print("DAO TREASURY FOX POOL OWNERSHIP ANALYSIS")
    print("="*100)
    
    for pool in FOX_POOLS:
        chain_name = pool['chain_name']
        pool_address = pool['pool_address']
        pool_name = pool['pool_name']
        pool_type = pool['type']
        
        dao_address = DAO_TREASURY_ADDRESSES.get(chain_name)
        if not dao_address:
            logger.warning(f"No DAO treasury address found for {chain_name}")
            continue
        w3 = get_web3_connection(pool['rpc'])
        
        if pool_type == 'erc20':
            balance = get_token_balance(w3, pool_address, dao_address)
            price = get_token_price_coingecko(pool_address, chain_name)
            usd_value = balance * price
            print(f"  DAO Balance: {balance:,.4f} (USD: ${usd_value:,.2f})")
            results.append({
                'chain_name': chain_name,
                'pool_name': pool_name,
                'pool_address': pool_address,
                'dao_address': dao_address,
                'dao_balance': balance,
                'token_price_usd': price,
                'dao_usd_value': usd_value
            })
            continue

        if pool_type == 'uniswap_v2':
            contract = w3.eth.contract(address=pool_address, abi=UNISWAP_V2_ABI)
            try:
                lp_balance = get_token_balance(w3, pool_address, dao_address)
                total_supply = contract.functions.totalSupply().call() / 1e18
                reserves = contract.functions.getReserves().call()
                token0 = contract.functions.token0().call()
                token1 = contract.functions.token1().call()
                # Get prices
                price0 = get_token_price_coingecko(token0, chain_name)
                price1 = get_token_price_coingecko(token1, chain_name)
                # DAO share
                share = lp_balance / total_supply if total_supply > 0 else 0
                amt0 = reserves[0] / 1e18 * share
                amt1 = reserves[1] / 1e18 * share
                usd_value = amt0 * price0 + amt1 * price1
                print(f"  DAO LP: {lp_balance:,.4f} | Share: {share:.4%} | Token0: {amt0:.4f} | Token1: {amt1:.4f} | USD: ${usd_value:,.2f}")
                results.append({
                    'chain_name': chain_name,
                    'pool_name': pool_name,
                    'pool_address': pool_address,
                    'dao_address': dao_address,
                    'dao_lp_balance': lp_balance,
                    'total_lp_supply': total_supply,
                    'ownership_percentage': share * 100,
                    'token0_amt': amt0,
                    'token1_amt': amt1,
                    'token0_price': price0,
                    'token1_price': price1,
                    'dao_usd_value': usd_value
                })
            except Exception as e:
                logger.error(f"Error analyzing Uniswap V2 pool {pool_address}: {e}")
            continue
        if pool_type == 'uniswap_v3':
            # Only works for WETH/FOX V3 on Arbitrum in this config
            try:
                nft = w3.eth.contract(address=UNIV3_NFT_MANAGER, abi=UNIV3_NFT_ABI)
                balance = nft.functions.balanceOf(dao_address).call()
                total_fox = 0
                total_weth = 0
                for i in range(balance):
                    token_id = nft.functions.tokenOfOwnerByIndex(dao_address, i).call()
                    pos = nft.functions.positions(token_id).call()
                    # Only count positions in this pool
                    pool_addr = get_univ3_pool_address(w3, pos[2], pos[3], pos[4])
                    if pool_addr.lower() == pool_address.lower():
                        # For simplicity, use liquidity as proxy, but ideally fetch amounts
                        # Here, pos[2]=token0, pos[3]=token1
                        # We'll just sum liquidity for now
                        # For real amounts, would need to use Uniswap math
                        # We'll fetch prices for both tokens
                        price0 = get_token_price_coingecko(pos[2], chain_name)
                        price1 = get_token_price_coingecko(pos[3], chain_name)
                        # Placeholder: treat liquidity as split 50/50 (not accurate)
                        fox_amt = pos[7] / 2 / 1e18
                        weth_amt = pos[7] / 2 / 1e18
                        total_fox += fox_amt
                        total_weth += weth_amt
                usd_value = total_fox * price0 + total_weth * price1
                print(f"  DAO Uniswap V3: FOX {total_fox:.4f}, WETH {total_weth:.4f}, USD: ${usd_value:,.2f}")
                results.append({
                    'chain_name': chain_name,
                    'pool_name': pool_name,
                    'pool_address': pool_address,
                    'dao_address': dao_address,
                    'dao_balance': balance,
                    'fox_amt': total_fox,
                    'weth_amt': total_weth,
                    'fox_price': price0,
                    'weth_price': price1,
                    'dao_usd_value': usd_value
                })
            except Exception as e:
                logger.error(f"Error analyzing Uniswap V3 pool {pool_address}: {e}")
            continue
    return results

def display_summary(results: list):
    if not results:
        print("\nNo DAO ownership data found.")
        return
    print("\n" + "="*100)
    print("DAO OWNERSHIP SUMMARY")
    print("="*100)
    import pandas as pd
    df = pd.DataFrame(results)
    # Pool-level summary
    print("\nDAO POSITIONS (all pools):")
    # Only apply float formatting to numeric columns
    def safe_float_format(val):
        try:
            return f"{float(val):.4f}"
        except Exception:
            return str(val) if val != '' else 'N/A'
    print(df.applymap(safe_float_format).to_string(index=False))
    # Pool totals
    print("\nPOOL TOTALS:")
    pool_totals = df.groupby(['chain_name','pool_name']).agg(
        pool_usd_value = ('dao_usd_value', 'sum'),
        dao_lp_balance = ('dao_balance', 'sum'),
        ownership_pct = ('ownership_percentage', 'mean') if 'ownership_percentage' in df.columns else ('dao_usd_value', lambda x: ''),
    ).reset_index()
    print(pool_totals.applymap(safe_float_format).to_string(index=False))
    # Chain totals
    print("\nCHAIN TOTALS:")
    chain_totals = df.groupby('chain_name').agg(
        chain_pool_usd = ('dao_usd_value', 'sum'),
        chain_dao_lp = ('dao_balance', 'sum'),
        ownership_pct = ('ownership_percentage', 'mean') if 'ownership_percentage' in df.columns else ('dao_usd_value', lambda x: ''),
    ).reset_index()
    print(chain_totals.applymap(safe_float_format).to_string(index=False))
    # Overall totals
    total_dao_usd = df['dao_usd_value'].sum()
    print(f"\nTotal DAO USD Value: ${total_dao_usd:,.2f}")
    if 'ownership_percentage' in df.columns:
        avg_ownership = df['ownership_percentage'].mean()
        print(f"Average DAO Ownership (where available): {avg_ownership:.2f}%")

def main():
    """Main function to analyze DAO ownership"""
    logger.info("Starting DAO treasury FOX pool ownership analysis")
    
    print("DAO Treasury Addresses:")
    for chain, address in DAO_TREASURY_ADDRESSES.items():
        print(f"  {chain}: {address}")
    
    # Analyze DAO ownership
    results = analyze_dao_ownership()
    
    # Display summary
    display_summary(results)
    
    logger.info("DAO ownership analysis complete!")

if __name__ == "__main__":
    main() 