import sys
from typing import List, Dict
import requests
from web3 import Web3
import os

# List of missing token addresses (lowercase)
MISSING_ADDRESSES = [
    "0xfc43aaf89a71acaa644842ee4219e8eb77657427",
    "0xf0346b437fe43e64fa799c2bd3cf5db1f7e9327c",
    "0x6456333ba58056754334341e6754ed422c188982",
    "0xde568fd89b3349a766f45d5ab2a7c0510f476a80",
    "0x2905d7e4d048d29954f81b02171dd313f457a4a4",
    "0xc654a41e45a4e47561caae38052478d00fa64830",
    "0xf5042e6ffac5a625d4e7848e0b01373d8eb9e222",
    "0xd387c40a72703b38a5181573724bcaf2ce6038a5",
    "0x3c2bf5c0be7be4919fae1330b748e89f165259d7",
]

ARBITRUM_RPC = "https://arbitrum-mainnet.infura.io/v3/208a3474635e4ebe8ee409cef3fbcd40"
COINGECKO_API = "https://api.coingecko.com/api/v3"

ERC20_ABI = [
    {
        "constant": True,
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "name",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function",
    },
]


def fetch_from_coingecko(address: str) -> Dict:
    """Try to fetch token metadata from CoinGecko by contract address."""
    url = f"{COINGECKO_API}/coins/ethereum/contract/{address}"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return {
                "address": address,
                "symbol": data["symbol"].upper(),
                "name": data["name"],
                "decimals": int(data["detail_platforms"]["ethereum"]["decimal_place"]),
            }
    except Exception as e:
        print(f"  CoinGecko error for {address}: {e}")
    return {}


def fetch_from_web3(address: str, w3: Web3) -> Dict:
    """Fallback: fetch token metadata from the blockchain via Web3."""
    try:
        contract = w3.eth.contract(
            address=Web3.to_checksum_address(address), abi=ERC20_ABI
        )
        symbol = contract.functions.symbol().call()
        name = contract.functions.name().call()
        decimals = contract.functions.decimals().call()
        return {
            "address": address,
            "symbol": symbol,
            "name": name,
            "decimals": int(decimals),
        }
    except Exception as e:
        print(f"  Web3 error for {address}: {e}")
        return {}


def fetch_metadata(addresses: List[str]) -> List[Dict]:
    """Fetch metadata for a list of token addresses using CoinGecko, fallback to Web3."""
    w3 = Web3(Web3.HTTPProvider(ARBITRUM_RPC))
    results = []
    for addr in addresses:
        print(f"Checking {addr}...")
        meta = fetch_from_coingecko(addr)
        if not meta:
            meta = fetch_from_web3(addr, w3)
        if meta:
            print(
                f"  Found: {meta['symbol']} | {meta['name']} | decimals: {meta['decimals']}"
            )
            results.append(meta)
        else:
            print(f"  Not found: {addr}")
    return results


def print_as_json_array(tokens: List[Dict]) -> None:
    import json

    print(json.dumps(tokens, indent=2))


if __name__ == "__main__":
    tokens = fetch_metadata(MISSING_ADDRESSES)
    print("\n--- JSON for tokens.json ---")
    print_as_json_array(tokens)
    # Example usage: python fetch_token_metadata.py
