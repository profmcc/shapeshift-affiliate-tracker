import sys
from typing import List, Dict
from web3 import Web3
from eth_abi.abi import decode as decode_abi
import binascii

ARBITRUM_RPC = "https://arbitrum-mainnet.infura.io/v3/208a3474635e4ebe8ee409cef3fbcd40"

# Inferred ABI fragments for known event signatures (all lowercase, 0x-prefixed)
INFERRED_EVENTS = {
    # ERC-20 Transfer
    "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef": {
        "name": "Transfer",
        "inputs": ["address", "address", "uint256"],
        "indexed": [True, True, False]
    },
    # ERC-20 Approval
    "0x8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925": {
        "name": "Approval",
        "inputs": ["address", "address", "uint256"],
        "indexed": [True, True, False]
    },
    # SolverCallExecuted(address,bytes,uint256)
    "0x93485dcd31a905e3ffd7b012abe3438fa8fa77f98ddc9f50e879d3fa7ccdc324": {
        "name": "SolverCallExecuted",
        "inputs": ["address", "bytes", "uint256"],
        "indexed": [True, True, True]
    },
    # SolverNativeTransfer(address,uint256)
    "0xd35467972d1fda5b63c735f59d3974fa51785a41a92aa3ed1b70832836f8dba6": {
        "name": "SolverNativeTransfer",
        "inputs": ["address", "uint256"],
        "indexed": [True, True]
    },
    # Swap(address,address,int256,int256,uint160,uint128,int24,uint128,uint128)
    "0x19b47279256b2a23a1665c810c8d55a1758940ee09377d4f8d26497a3577dc83": {
        "name": "Swap",
        "inputs": ["address", "address", "int256", "int256", "uint160", "uint128", "int24", "uint128", "uint128"],
        "indexed": [True, True, True, True, True, True, True, True, True]
    }
}

def decode_log(log: Dict, w3: Web3) -> None:
    topic0 = log['topics'][0].hex().lower()
    topic0 = '0x' + topic0 if not topic0.startswith('0x') else topic0
    found = False
    for key in INFERRED_EVENTS.keys():
        if topic0 == key:
            event = INFERRED_EVENTS[key]
            found = True
            break
    if not found:
        print(f"Unknown event: {topic0}")
        return
    print(f"Event: {event['name']} at {log['address']}")
    indexed_inputs = [i for i, idx in enumerate(event['indexed']) if idx]
    non_indexed_inputs = [i for i, idx in enumerate(event['indexed']) if not idx]
    # Decode indexed params from topics
    decoded_indexed = []
    for idx in indexed_inputs:
        # topics[1:] are indexed params
        if idx+1 < len(log['topics']):
            val = log['topics'][idx+1].hex()
            # For address, last 40 hex chars
            if event['inputs'][idx] == 'address':
                val = '0x' + val[-40:]
            decoded_indexed.append(val)
        else:
            decoded_indexed.append(None)
    # Decode non-indexed params from data
    decoded_non_indexed = []
    if non_indexed_inputs:
        types = [event['inputs'][i] for i in non_indexed_inputs]
        data = log['data']
        if data and data != b'' and data != '0x':
            try:
                # Handle both bytes and hex string
                if isinstance(data, bytes):
                    data_bytes = data
                else:
                    # Convert hex string to bytes
                    data_hex = data
                    data_bytes = bytes.fromhex(data_hex[2:]) if data_hex.startswith('0x') else bytes.fromhex(data_hex)
                print(f"    [DEBUG: types={types}, data_bytes={data_bytes.hex()}]")
                decoded_non_indexed = list(decode_abi(types, data_bytes))
            except Exception as e:
                print(f"    [decode error: {e} | raw data: {data}]")
                decoded_non_indexed = [None for _ in types]
        else:
            decoded_non_indexed = [None for _ in types]
    # Print all params
    for i, typ in enumerate(event['inputs']):
        if i in indexed_inputs:
            print(f"  {typ} (indexed): {decoded_indexed[indexed_inputs.index(i)]}")
        else:
            if non_indexed_inputs:
                print(f"  {typ}: {decoded_non_indexed[non_indexed_inputs.index(i)]}")
            else:
                print(f"  {typ}: (no non-indexed params)")
    print()

def decode_transaction_logs(tx_hash: str) -> None:
    w3 = Web3(Web3.HTTPProvider(ARBITRUM_RPC))
    try:
        receipt = w3.eth.get_transaction_receipt(tx_hash)
    except Exception as e:
        print(f"Error fetching receipt: {e}")
        return
    for log in receipt['logs']:
        decode_log(log, w3)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python decode_logs_with_inferred_abi.py <tx_hash>")
        sys.exit(1)
    decode_transaction_logs(sys.argv[1]) 