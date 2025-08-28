from web3 import Web3

# Connect to Ethereum
w3 = Web3(
    Web3.HTTPProvider(
        "https://eth-mainnet.g.alchemy.com/v2/_3x-ZVAe8aKBUMeRax2zOjg0fotYb3ms"
    )
)

# Get latest block
latest = w3.eth.block_number

# Calculate start block (30 days ago, ~192,000 blocks)
start = latest - 192000

print(f"Latest block: {latest}")
print(f"Start block (30 days ago): {start}")
print(f"Block range: {start} to {latest}")

# Also calculate exact 30 days if needed
print(f"\nTo run the script for past month:")
print(
    f"INFURA_URL='https://eth-mainnet.g.alchemy.com/v2/_3x-ZVAe8aKBUMeRax2zOjg0fotYb3ms' python fetch_v2_weth_fox_events.py {start} {latest}"
)
