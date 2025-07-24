from web3 import Web3

# Use your Alchemy mainnet endpoint
alchemy_url = 'https://eth-mainnet.g.alchemy.com/v2/_3x-ZVAe8aKBUMeRax2zOjg0fotYb3ms'
w3 = Web3(Web3.HTTPProvider(alchemy_url))

# Use a small block range for testing
from_block = 22971003
to_block = 22971013

# ERC20 Transfer topic
transfer_topic = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
# DAO address as strict 32-byte, lowercase, zero-padded hex
dao_topic = '0x00000000000000000000000090a48d5cf7343b08da12e067680b4c6dbfe551be'

filter_params = {
    'fromBlock': from_block,
    'toBlock': to_block,
    'topics': [transfer_topic, None, dao_topic]
}

print("Filter params:", filter_params)
try:
    logs = w3.eth.get_logs(filter_params)
    print("Logs:", logs)
except Exception as e:
    print("Error:", e)