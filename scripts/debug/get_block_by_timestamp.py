import sys
from web3 import Web3
from datetime import datetime

RPC_ENDPOINTS = {
    'ethereum': "https://mainnet.infura.io/v3/208a3474635e4ebe8ee409cef3fbcd40",
    'polygon': "https://polygon-mainnet.infura.io/v3/208a3474635e4ebe8ee409cef3fbcd40",
    'optimism': "https://optimism-mainnet.infura.io/v3/208a3474635e4ebe8ee409cef3fbcd40",
    'arbitrum': "https://arbitrum-mainnet.infura.io/v3/208a3474635e4ebe8ee409cef3fbcd40",
    'base': "https://mainnet.base.org"
}

def get_block_by_timestamp(w3: Web3, target_ts: int) -> int:
    latest = w3.eth.block_number
    earliest = 1
    while earliest < latest:
        mid = (earliest + latest) // 2
        block = w3.eth.get_block(mid)
        if block['timestamp'] < target_ts:
            earliest = mid + 1
        else:
            latest = mid
    return earliest

def main():
    if len(sys.argv) != 3:
        print("Usage: python get_block_by_timestamp.py <start_utc> <end_utc>")
        print("Example: python get_block_by_timestamp.py '2024-07-13 00:00:00' '2024-07-19 23:59:59'")
        return
    start_utc = sys.argv[1]
    end_utc = sys.argv[2]
    start_ts = int(datetime.strptime(start_utc, "%Y-%m-%d %H:%M:%S").timestamp())
    end_ts = int(datetime.strptime(end_utc, "%Y-%m-%d %H:%M:%S").timestamp())
    print(f"Start UTC: {start_utc} ({start_ts})")
    print(f"End UTC:   {end_utc} ({end_ts})\n")
    for chain, rpc in RPC_ENDPOINTS.items():
        print(f"Chain: {chain}")
        w3 = Web3(Web3.HTTPProvider(rpc))
        try:
            start_block = get_block_by_timestamp(w3, start_ts)
            end_block = get_block_by_timestamp(w3, end_ts)
            print(f"  Start block: {start_block}")
            print(f"  End block:   {end_block}\n")
        except Exception as e:
            print(f"  Error: {e}\n")

if __name__ == "__main__":
    main() 