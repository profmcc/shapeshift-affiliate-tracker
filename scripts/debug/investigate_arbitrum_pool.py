import json
from web3 import Web3
from datetime import datetime, timedelta

# Configuration
PAIR_ADDRESS = "0x5f6ce0ca13b87bd738519545d3e018e70e339c24"
INFURA_URL = "https://arbitrum-mainnet.infura.io/v3/208a3474635e4ebe8ee409cef3fbcd40"


def get_web3():
    return Web3(Web3.HTTPProvider(INFURA_URL))


def get_pool_info():
    """Get detailed pool information"""
    w3 = get_web3()
    checksum_address = w3.to_checksum_address(PAIR_ADDRESS)

    # Extended ABI to get token addresses
    abi = [
        {
            "constant": True,
            "inputs": [],
            "name": "getReserves",
            "outputs": [
                {"name": "_reserve0", "type": "uint112"},
                {"name": "_reserve1", "type": "uint112"},
                {"name": "_blockTimestampLast", "type": "uint32"},
            ],
            "type": "function",
        },
        {
            "constant": True,
            "inputs": [],
            "name": "token0",
            "outputs": [{"name": "", "type": "address"}],
            "type": "function",
        },
        {
            "constant": True,
            "inputs": [],
            "name": "token1",
            "outputs": [{"name": "", "type": "address"}],
            "type": "function",
        },
        {
            "constant": True,
            "inputs": [],
            "name": "totalSupply",
            "outputs": [{"name": "", "type": "uint256"}],
            "type": "function",
        },
    ]

    try:
        contract = w3.eth.contract(address=checksum_address, abi=abi)
        reserves = contract.functions.getReserves().call()
        token0 = contract.functions.token0().call()
        token1 = contract.functions.token1().call()
        total_supply = contract.functions.totalSupply().call()

        print(f"Pool Information:")
        print(f"  Token0: {token0}")
        print(f"  Token1: {token1}")
        print(f"  Reserve0: {reserves[0]}")
        print(f"  Reserve1: {reserves[1]}")
        print(f"  Total Supply: {total_supply}")
        print(f"  Block Timestamp: {reserves[2]}")

        return {
            "token0": token0,
            "token1": token1,
            "reserve0": reserves[0],
            "reserve1": reserves[1],
            "total_supply": total_supply,
        }
    except Exception as e:
        print(f"Error getting pool info: {e}")
        return None


def get_recent_transactions():
    """Get recent transactions involving the pool"""
    w3 = get_web3()
    checksum_address = w3.to_checksum_address(PAIR_ADDRESS)

    # Get current block
    latest_block = w3.eth.block_number

    # Look at last 10,000 blocks (about 1-2 days on Arbitrum)
    start_block = latest_block - 10000

    print(f"\nAnalyzing blocks {start_block} to {latest_block}")
    print(f"Pool address: {checksum_address}")
    print("=" * 80)

    # Get all logs for this address
    logs = w3.eth.get_logs(
        {"address": checksum_address, "fromBlock": start_block, "toBlock": latest_block}
    )

    print(f"Found {len(logs)} log entries")

    # Group by transaction hash
    tx_logs = {}
    for log in logs:
        tx_hash = log["transactionHash"].hex()
        if tx_hash not in tx_logs:
            tx_logs[tx_hash] = []
        tx_logs[tx_hash].append(log)

    print(f"Found {len(tx_logs)} unique transactions")

    if len(tx_logs) == 0:
        print("\nNo recent transactions found. Let's check a larger range...")

        # Try last 100,000 blocks (about 1-2 weeks)
        start_block = latest_block - 100000
        print(f"\nChecking blocks {start_block} to {latest_block}")

        logs = w3.eth.get_logs(
            {
                "address": checksum_address,
                "fromBlock": start_block,
                "toBlock": latest_block,
            }
        )

        print(f"Found {len(logs)} log entries in larger range")

        # Group by transaction hash
        tx_logs = {}
        for log in logs:
            tx_hash = log["transactionHash"].hex()
            if tx_hash not in tx_logs:
                tx_logs[tx_hash] = []
            tx_logs[tx_hash].append(log)

        print(f"Found {len(tx_logs)} unique transactions in larger range")

    print("=" * 80)

    # Analyze each transaction (limit to first 10 to avoid spam)
    count = 0
    for tx_hash, logs in list(tx_logs.items())[:10]:
        count += 1
        print(f"\nTransaction {count}: {tx_hash}")

        # Get transaction details
        try:
            tx = w3.eth.get_transaction(tx_hash)
            block = w3.eth.get_block(tx["blockNumber"])
            timestamp = datetime.utcfromtimestamp(block["timestamp"])

            print(f"  Block: {tx['blockNumber']}")
            print(f"  Time: {timestamp}")
            print(f"  From: {tx['from']}")
            print(f"  To: {tx['to']}")
            print(f"  Value: {w3.from_wei(tx['value'], 'ether')} ETH")

            # Analyze logs
            print(f"  Logs ({len(logs)}):")
            for i, log in enumerate(logs):
                print(f"    Log {i+1}:")
                print(f"      Topics: {[topic.hex() for topic in log['topics']]}")
                print(f"      Data: {log['data'].hex()}")

                # Try to identify event type
                if len(log["topics"]) > 0:
                    event_sig = log["topics"][0].hex()
                    print(f"      Event signature: {event_sig}")

                    # Known event signatures
                    known_events = {
                        "0x4c209b5fc8ad50758f13e2e1088ba56a560dff690a1c6fef26394f4c03821c4f": "Mint",
                        "0xdccd412f0b1252819cb1fd330b93224ca42612892bb3f4f789976e6d81936496": "Burn",
                        "0xd78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822": "Swap",
                        "0x1c411e9a96e071241c2f21f7726b17ae89e3cab4c78be50e062b03a9fffbbad1": "Sync",
                        "0x8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925": "Approval",
                        "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef": "Transfer",
                    }

                    if event_sig in known_events:
                        print(f"      Event type: {known_events[event_sig]}")
                    else:
                        print(f"      Event type: Unknown")

            print("-" * 60)

        except Exception as e:
            print(f"  Error getting transaction details: {e}")

    if len(tx_logs) > 10:
        print(f"\n... and {len(tx_logs) - 10} more transactions")


def check_pool_contract():
    """Check if this is actually a Uniswap V2 pair"""
    w3 = get_web3()
    checksum_address = w3.to_checksum_address(PAIR_ADDRESS)

    # Try to call getReserves
    try:
        # Minimal ABI for getReserves
        abi = [
            {
                "constant": True,
                "inputs": [],
                "name": "getReserves",
                "outputs": [
                    {"name": "_reserve0", "type": "uint112"},
                    {"name": "_reserve1", "type": "uint112"},
                    {"name": "_blockTimestampLast", "type": "uint32"},
                ],
                "type": "function",
            }
        ]
        contract = w3.eth.contract(address=checksum_address, abi=abi)
        reserves = contract.functions.getReserves().call()
        print(f"Pool reserves: {reserves}")
        return True
    except Exception as e:
        print(f"Error calling getReserves: {e}")
        return False


if __name__ == "__main__":
    print("Investigating Arbitrum Pool")
    print("=" * 80)

    # First get pool info
    pool_info = get_pool_info()

    print("\n" + "=" * 80)
    get_recent_transactions()

    # First check if it's a valid pool
    if check_pool_contract():
        print("✓ Contract responds to getReserves - likely a Uniswap V2 pair")
    else:
        print(
            "✗ Contract doesn't respond to getReserves - might not be a Uniswap V2 pair"
        )
