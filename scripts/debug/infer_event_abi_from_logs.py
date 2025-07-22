import sys
import requests
from web3 import Web3
from typing import List, Dict

ARBITRUM_RPC = "https://arbitrum-mainnet.infura.io/v3/208a3474635e4ebe8ee409cef3fbcd40"
FOURBYTE_API = "https://www.4byte.directory/api/v1/event-signatures/?hex_signature="

def lookup_event_signature(topic0: str) -> List[Dict]:
    """Look up event signature on 4byte.directory by topic0 hash."""
    url = FOURBYTE_API + topic0
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return data.get('results', [])
    except Exception as e:
        print(f"4byte.directory error: {e}")
    return []

def infer_event_abis(tx_hash: str) -> None:
    """For each log in a transaction, print event signature and possible ABI fragment."""
    w3 = Web3(Web3.HTTPProvider(ARBITRUM_RPC))
    try:
        receipt = w3.eth.get_transaction_receipt(tx_hash)
    except Exception as e:
        print(f"Error fetching receipt: {e}")
        return
    for i, log in enumerate(receipt['logs']):
        topic0 = log['topics'][0].hex()
        print(f"Log #{i+1} | Address: {log['address']} | Topic0: {topic0}")
        sigs = lookup_event_signature(topic0)
        if sigs:
            for sig in sigs:
                print(f"  Signature: {sig['text_signature']}")
                # Suggest ABI fragment
                name = sig['text_signature'].split('(')[0]
                params = sig['text_signature'].split('(')[1].rstrip(')').split(',')
                inputs = []
                for idx, p in enumerate(params):
                    if p:
                        inputs.append({"indexed": True, "name": f"param{idx}", "type": p.strip()})
                abi = {
                    "anonymous": False,
                    "inputs": inputs,
                    "name": name,
                    "type": "event"
                }
                print(f"  Possible ABI: {abi}")
        else:
            print("  No signature found on 4byte.directory.")
        print()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python infer_event_abi_from_logs.py <tx_hash>")
        sys.exit(1)
    infer_event_abis(sys.argv[1]) 