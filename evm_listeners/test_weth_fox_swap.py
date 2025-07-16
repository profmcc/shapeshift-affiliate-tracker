from web3 import Web3
import os

# WETH/FOX pair address
WETH_FOX_PAIR = Web3.to_checksum_address('0x470e8de2ebaef52014a47cb5e6af86884947f08c')
SWAP_SIGNATURE = '0xd78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822'

INFURA_URL = os.getenv('INFURA_URL', 'https://eth-mainnet.g.alchemy.com/v2/_3x-ZVAe8aKBUMeRax2zOjg0fotYb3ms')

w3 = Web3(Web3.HTTPProvider(INFURA_URL))

# Test with a small block range
start_block = 22825000
end_block = 22825100

print(f"Testing WETH/FOX pair: {WETH_FOX_PAIR}")
print(f"Block range: {start_block} to {end_block}")

# Try different filter approaches
filters_to_try = [
    {
        'address': WETH_FOX_PAIR,
        'topics': [SWAP_SIGNATURE],
        'fromBlock': start_block,
        'toBlock': end_block
    },
    {
        'address': WETH_FOX_PAIR,
        'fromBlock': start_block,
        'toBlock': end_block
    }
]

for i, log_filter in enumerate(filters_to_try):
    print(f"\nTrying filter {i+1}: {log_filter}")
    try:
        logs = w3.eth.get_logs(log_filter)
        print(f"Success! Found {len(logs)} events")
        if logs:
            print(f"First log: {logs[0]}")
    except Exception as e:
        print(f"Error: {e}") 