import sys
from typing import Dict, List
from web3 import Web3
import os

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../shared"))
)
from token_cache import init_web3, get_token_info

ARBITRUM_RPC = "https://arbitrum-mainnet.infura.io/v3/208a3474635e4ebe8ee409cef3fbcd40"
TRANSFER_SIG = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"


def analyze_transaction(tx_hash: str) -> None:
    """Analyze a transaction, print all ERC-20 token transfers with from/to/amount, and show metadata if available."""
    w3 = Web3(Web3.HTTPProvider(ARBITRUM_RPC))
    init_web3(ARBITRUM_RPC)
    try:
        receipt = w3.eth.get_transaction_receipt(tx_hash)
    except Exception as e:
        print(f"Error fetching receipt: {e}")
        return
    found = False
    for log in receipt["logs"]:
        if log["topics"][0].hex().lower() == TRANSFER_SIG:
            token_addr = log["address"].lower()
            info = get_token_info(token_addr)
            # Parse amount
            data_hex = log["data"]
            if data_hex.startswith("0x"):
                data_hex = data_hex[2:]
            amount = int(data_hex, 16) if data_hex else 0
            # Parse from/to
            from_addr = "0x" + log["topics"][1].hex()[-40:]
            to_addr = "0x" + log["topics"][2].hex()[-40:]
            if info:
                decimals = info["decimals"] or 18
                formatted = f"{amount / (10 ** decimals):,.6f} {info['symbol']}"
                print(
                    f"Token: {info['symbol']} | Name: {info['name']} | Address: {token_addr}"
                )
                print(f"  From: {from_addr}\n  To:   {to_addr}\n  Amount: {formatted}")
            else:
                print(f"Token: UNKNOWN | Address: {token_addr}")
                print(f"  From: {from_addr}\n  To:   {to_addr}\n  Raw Amount: {amount}")
                print("  (Token metadata missing from cache)")
            found = True
    if not found:
        print("No ERC-20 token transfers found in this transaction.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python analyze_no_volume_tx.py <tx_hash>")
        sys.exit(1)
    analyze_transaction(sys.argv[1])
    # Example usage:
    # python analyze_no_volume_tx.py 0xefbc16d26edb48b9cab0cb65646ec350c933a8d1633b4360ec01c38ccb73042
