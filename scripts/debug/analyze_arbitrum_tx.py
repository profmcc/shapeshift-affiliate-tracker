#!/usr/bin/env python3
"""
Analyze a specific Arbitrum transaction to understand WETH/FOX pool interactions
"""

import json
from web3 import Web3
from eth_abi import decode
import sqlite3
from datetime import datetime

# Arbitrum RPC endpoint
ARBITRUM_RPC = "https://arb1.arbitrum.io/rpc"

# Pool and token addresses (Arbitrum)
POOL_ADDRESS = "0x5f6ce0ca13b87bd738519545d3e018e70e339c24"
WETH_ADDRESS = "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1"
FOX_ADDRESS = "0x7c6d161b367ec0605260628c37b8dd778446256b"

# ABI for basic ERC20 functions
ERC20_ABI = [
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
        "name": "symbol",
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
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function",
    },
]

# Uniswap V2 Pair ABI for events
PAIR_ABI = [
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "sender", "type": "address"},
            {"indexed": False, "name": "amount0", "type": "uint256"},
            {"indexed": False, "name": "amount1", "type": "uint256"},
        ],
        "name": "Mint",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "sender", "type": "address"},
            {"indexed": False, "name": "amount0", "type": "uint256"},
            {"indexed": False, "name": "amount1", "type": "uint256"},
            {"indexed": True, "name": "to", "type": "address"},
        ],
        "name": "Burn",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "sender", "type": "address"},
            {"indexed": False, "name": "amount0In", "type": "uint256"},
            {"indexed": False, "name": "amount1In", "type": "uint256"},
            {"indexed": False, "name": "amount0Out", "type": "uint256"},
            {"indexed": False, "name": "amount1Out", "type": "uint256"},
            {"indexed": True, "name": "to", "type": "address"},
        ],
        "name": "Swap",
        "type": "event",
    },
]


def setup_web3():
    """Setup Web3 connection to Arbitrum"""
    w3 = Web3(Web3.HTTPProvider(ARBITRUM_RPC))
    # Ensure addresses are checksummed
    global POOL_ADDRESS, WETH_ADDRESS, FOX_ADDRESS
    POOL_ADDRESS = w3.to_checksum_address(POOL_ADDRESS)
    WETH_ADDRESS = w3.to_checksum_address(WETH_ADDRESS)
    FOX_ADDRESS = w3.to_checksum_address(FOX_ADDRESS)
    return w3


def get_token_info(web3, token_address):
    """Get token information"""
    contract = web3.eth.contract(address=token_address, abi=ERC20_ABI)
    try:
        name = contract.functions.name().call()
        symbol = contract.functions.symbol().call()
        decimals = contract.functions.decimals().call()
        return {"name": name, "symbol": symbol, "decimals": decimals}
    except Exception as e:
        print(f"Error getting token info for {token_address}: {e}")
        return None


def analyze_transaction(web3, tx_hash):
    """Analyze a specific transaction"""
    print(f"Analyzing transaction: {tx_hash}")
    print("=" * 60)

    # Get transaction details
    try:
        tx = web3.eth.get_transaction(tx_hash)
        tx_receipt = web3.eth.get_transaction_receipt(tx_hash)
    except Exception as e:
        print(f"Error fetching transaction: {e}")
        return

    print(f"From: {tx['from']}")
    print(f"To: {tx['to']}")
    print(f"Value: {web3.from_wei(tx['value'], 'ether')} ETH")
    print(f"Gas used: {tx_receipt['gasUsed']}")
    print(f"Status: {'Success' if tx_receipt['status'] == 1 else 'Failed'}")
    print()

    # Get token info
    weth_info = get_token_info(web3, WETH_ADDRESS)
    fox_info = get_token_info(web3, FOX_ADDRESS)

    print("Token Information:")
    if weth_info:
        print(
            f"WETH: {weth_info['name']} ({weth_info['symbol']}) - {weth_info['decimals']} decimals"
        )
    if fox_info:
        print(
            f"FOX: {fox_info['name']} ({fox_info['symbol']}) - {fox_info['decimals']} decimals"
        )
    print()

    # Analyze logs
    print("Transaction Logs:")
    print("-" * 40)

    pool_contract = web3.eth.contract(address=POOL_ADDRESS, abi=PAIR_ABI)

    for i, log in enumerate(tx_receipt["logs"]):
        print(f"Log {i}:")
        print(f"  Address: {log['address']}")
        print(f"  Topics: {log['topics']}")
        print(f"  Data: {log['data']}")

        # Check if this is from our pool
        if log["address"].lower() == POOL_ADDRESS.lower():
            print(f"  *** POOL EVENT DETECTED ***")

            # Try to decode as Uniswap V2 events
            try:
                decoded_log = pool_contract.events.Mint().process_log(log)
                print(f"  Event: Mint")
                print(f"  Sender: {decoded_log['args']['sender']}")
                print(f"  Amount0: {decoded_log['args']['amount0']}")
                print(f"  Amount1: {decoded_log['args']['amount1']}")

                # Convert to human readable
                if weth_info:
                    weth_amount = decoded_log["args"]["amount0"] / (
                        10 ** weth_info["decimals"]
                    )
                    print(f"  WETH Amount: {weth_amount:.6f}")
                if fox_info:
                    fox_amount = decoded_log["args"]["amount1"] / (
                        10 ** fox_info["decimals"]
                    )
                    print(f"  FOX Amount: {fox_amount:.6f}")

            except Exception as e1:
                try:
                    decoded_log = pool_contract.events.Burn().process_log(log)
                    print(f"  Event: Burn")
                    print(f"  Sender: {decoded_log['args']['sender']}")
                    print(f"  To: {decoded_log['args']['to']}")
                    print(f"  Amount0: {decoded_log['args']['amount0']}")
                    print(f"  Amount1: {decoded_log['args']['amount1']}")

                    # Convert to human readable
                    if weth_info:
                        weth_amount = decoded_log["args"]["amount0"] / (
                            10 ** weth_info["decimals"]
                        )
                        print(f"  WETH Amount: {weth_amount:.6f}")
                    if fox_info:
                        fox_amount = decoded_log["args"]["amount1"] / (
                            10 ** fox_info["decimals"]
                        )
                        print(f"  FOX Amount: {fox_amount:.6f}")

                except Exception as e2:
                    try:
                        decoded_log = pool_contract.events.Swap().process_log(log)
                        print(f"  Event: Swap")
                        print(f"  Sender: {decoded_log['args']['sender']}")
                        print(f"  To: {decoded_log['args']['to']}")
                        print(f"  Amount0In: {decoded_log['args']['amount0In']}")
                        print(f"  Amount1In: {decoded_log['args']['amount1In']}")
                        print(f"  Amount0Out: {decoded_log['args']['amount0Out']}")
                        print(f"  Amount1Out: {decoded_log['args']['amount1Out']}")

                        # Convert to human readable
                        if weth_info:
                            weth_in = decoded_log["args"]["amount0In"] / (
                                10 ** weth_info["decimals"]
                            )
                            weth_out = decoded_log["args"]["amount0Out"] / (
                                10 ** weth_info["decimals"]
                            )
                            print(f"  WETH In: {weth_in:.6f}, Out: {weth_out:.6f}")
                        if fox_info:
                            fox_in = decoded_log["args"]["amount1In"] / (
                                10 ** fox_info["decimals"]
                            )
                            fox_out = decoded_log["args"]["amount1Out"] / (
                                10 ** fox_info["decimals"]
                            )
                            print(f"  FOX In: {fox_in:.6f}, Out: {fox_out:.6f}")

                    except Exception as e3:
                        print(f"  Could not decode as Uniswap V2 event")
                        print(f"  Error: {e3}")

        # Check for ERC20 Transfer events
        if (
            len(log["topics"]) > 0
            and log["topics"][0].hex()
            == "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
        ):
            print(f"  *** ERC20 TRANSFER EVENT ***")
            try:
                # Decode transfer event
                # Transfer(address indexed from, address indexed to, uint256 value)
                from_addr = "0x" + log["topics"][1].hex()[-40:]
                to_addr = "0x" + log["topics"][2].hex()[-40:]
                value = int(log["data"], 16)

                print(f"  From: {from_addr}")
                print(f"  To: {to_addr}")
                print(f"  Value: {value}")

                # Check if this involves our tokens
                if log["address"].lower() == WETH_ADDRESS.lower():
                    if weth_info:
                        weth_amount = value / (10 ** weth_info["decimals"])
                        print(f"  WETH Amount: {weth_amount:.6f}")
                elif log["address"].lower() == FOX_ADDRESS.lower():
                    if fox_info:
                        fox_amount = value / (10 ** fox_info["decimals"])
                        print(f"  FOX Amount: {fox_amount:.6f}")

            except Exception as e:
                print(f"  Error decoding transfer: {e}")

        print()

    # Check if transaction involves the pool directly
    if tx["to"] and tx["to"].lower() == POOL_ADDRESS.lower():
        print("*** DIRECT POOL INTERACTION ***")
        print("Transaction is directly calling the pool contract")

        # Try to decode the input data
        if tx["input"] and tx["input"] != "0x":
            print(f"Input data: {tx['input']}")
            # This would need specific function signatures to decode properly
            print("(Input data decoding would require specific function ABIs)")


def main():
    """Main function"""
    web3 = setup_web3()

    if not web3.is_connected():
        print("Failed to connect to Arbitrum")
        return

    print("Connected to Arbitrum")
    print(f"Current block: {web3.eth.block_number}")
    print()

    # Transaction hash from user
    tx_hash = "0xa92e34a0c326ed34f2dab65aa1fcff10e93386b71074d65ffc5b90385b093471"

    analyze_transaction(web3, tx_hash)


if __name__ == "__main__":
    main()
