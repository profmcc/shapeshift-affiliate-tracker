import sys
from typing import List, Set
from web3 import Web3
import os

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../shared"))
)
from token_cache import init_web3, get_token_info

ARBITRUM_RPC = "https://arbitrum-mainnet.infura.io/v3/208a3474635e4ebe8ee409cef3fbcd40"

# Example transaction hashes (replace with your own)
TX_HASHES = [
    "0efbc16d26edb48b9cab0cb65646ec350c933a8d1633b4360ec01c38ccb73042",
    "9d1ff54a73637966a0b879994b7f5f4269089823551448a06cdc0082a40f915a",
    "b2ad642082300e12f9a1b305a5056d86ecb674b7392e88f992702cb2b1d4492a",
    "dd71e2c435a97ead213e8dcaa1f52a04e0802666ba877fcd6d3f1d14e91bdf23",
    "fa2b18fbcb942d7eb3a3fc28668c8acb957f229974b02a12de9ad5106aa49973",
    "4f4ed6e9c7a68d29dba8a2d613d99c3dbacf835d6218a226259d5c18724634a8",
    "da858fc59c7573040b3f07f89c03963d53c801b99f6c7613d2dd7f6df202e7a3",
]


def get_token_addresses_from_tx(w3: Web3, tx_hash: str) -> Set[str]:
    """Extract all unique token contract addresses from a transaction's logs."""
    try:
        receipt = w3.eth.get_transaction_receipt(tx_hash)
        return set(log["address"].lower() for log in receipt["logs"])
    except Exception as e:
        print(f"Error fetching logs for {tx_hash}: {e}")
        return set()


def check_missing_tokens(tx_hashes: List[str]) -> None:
    """Check which token addresses in the given transactions are missing from the token cache."""
    w3 = Web3(Web3.HTTPProvider(ARBITRUM_RPC))
    init_web3(ARBITRUM_RPC)
    all_missing = set()
    for tx_hash in tx_hashes:
        print(f"\nChecking transaction: {tx_hash}")
        token_addrs = get_token_addresses_from_tx(w3, tx_hash)
        for addr in token_addrs:
            info = get_token_info(addr)
            if not info:
                print(f"  MISSING: {addr}")
                all_missing.add(addr)
            else:
                print(f"  Found: {addr} ({info['symbol']})")
    if all_missing:
        print(f"\nSummary: {len(all_missing)} missing token(s):")
        for addr in all_missing:
            print(f"  {addr}")
    else:
        print("\nAll tokens found in cache.")


if __name__ == "__main__":
    check_missing_tokens(TX_HASHES)
    # Example usage: python check_missing_token_metadata.py
