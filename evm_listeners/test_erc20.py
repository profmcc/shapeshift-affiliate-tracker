from web3 import Web3
import os

# Test with USDC contract (known to have many Transfer events)
USDC_ADDRESS = '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48'
TRANSFER_SIGNATURE = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'

INFURA_URL = os.getenv('INFURA_URL', 'https://eth-mainnet.g.alchemy.com/v2/_3x-ZVAe8aKBUMeRax2zOjg0fotYb3ms')

w3 = Web3(Web3.HTTPProvider(INFURA_URL))

# Test with a smaller block range
start_block = 22825000
end_block = 22825100

print(f"Testing connectivity with Alchemy...")
print(f"Latest block: {w3.eth.block_number}")

try:
    # Try to get Transfer events from USDC
    logs = w3.eth.get_logs({
        'address': USDC_ADDRESS,
        'topics': [TRANSFER_SIGNATURE],
        'fromBlock': start_block,
        'toBlock': end_block
    })
    print(f"Success! Found {len(logs)} Transfer events")
except Exception as e:
    print(f"Error: {e}") 