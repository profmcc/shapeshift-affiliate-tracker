from web3 import Web3
import os

# WETH/USDC pair address
WETH_USDC_PAIR = '0xB4e16d0168e52d35CaCD2c6185b44281Ec28C9Dc'
SWAP_SIGNATURE = '0xd78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822'

INFURA_URL = os.getenv('INFURA_URL', 'https://eth-mainnet.g.alchemy.com/v2/_3x-ZVAe8aKBUMeRax2zOjg0fotYb3ms')

w3 = Web3(Web3.HTTPProvider(INFURA_URL))

# Test with a small block range
start_block = 22825000
end_block = 22825100

print(f"Testing WETH/USDC pair: {WETH_USDC_PAIR}")
print(f"Block range: {start_block} to {end_block}")

try:
    logs = w3.eth.get_logs({
        'address': WETH_USDC_PAIR,
        'topics': [SWAP_SIGNATURE],
        'fromBlock': start_block,
        'toBlock': end_block
    })
    print(f"Success! Found {len(logs)} Swap events")
    if logs:
        print(f"First log: {logs[0]}")
except Exception as e:
    print(f"Error: {e}") 