import requests
import sqlite3
from web3 import Web3
from eth_abi import decode

PORTALS_ROUTER = "0xbf5A7F3629fB325E2a8453D595AB103465F75E62"
SHAPESHIFT_PARTNER = "0x90A48D5CF7343B08dA12E067680B4C6dbfE551Be"
PORTAL_EVENT_TOPIC = "0x5915121ae705c6baa1bd6698f437ff30eb4b7dbd20e1f7d83c2f1a8be09a1f03"
ETHERSCAN_API_KEY = "XQ9KTU99VCHTPRNTDGPGY1RUKM3UIFP6ZJ"
ETHERSCAN_API_URL = "https://api.etherscan.io/api"
DB_PATH = "portals_affiliate_events.db"
DB_TABLE = "portals_affiliate_events2"

# Portal event ABI
PORTAL_EVENT_ABI = {
    "anonymous": False,
    "inputs": [
        {"indexed": False, "internalType": "address", "name": "inputToken", "type": "address"},
        {"indexed": False, "internalType": "uint256", "name": "inputAmount", "type": "uint256"},
        {"indexed": False, "internalType": "address", "name": "outputToken", "type": "address"},
        {"indexed": False, "internalType": "uint256", "name": "outputAmount", "type": "uint256"},
        {"indexed": True, "internalType": "address", "name": "sender", "type": "address"},
        {"indexed": True, "internalType": "address", "name": "broadcaster", "type": "address"},
        {"indexed": False, "internalType": "address", "name": "recipient", "type": "address"},
        {"indexed": True, "internalType": "address", "name": "partner", "type": "address"}
    ],
    "name": "Portal",
    "type": "event"
}   

def pad_topic_address(address: str) -> str:
    # Remove '0x' and pad left with zeros to 64 chars, then add '0x' back
    return '0x' + address.lower().replace('0x', '').rjust(64, '0')

partner_topic = pad_topic_address(SHAPESHIFT_PARTNER)

url = (
    f"{ETHERSCAN_API_URL}"
    f"?module=logs&action=getLogs"
    f"&address={PORTALS_ROUTER}"
    f"&topic0={PORTAL_EVENT_TOPIC}"
    f"&topic3={partner_topic}"
    f"&apikey={ETHERSCAN_API_KEY}"
)

response = requests.get(url)
data = response.json()

# Set up DB
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
c.execute(f'''CREATE TABLE IF NOT EXISTS {DB_TABLE} (
    tx_hash TEXT,
    block_number INTEGER,
    input_token TEXT,
    input_amount TEXT,
    output_token TEXT,
    output_amount TEXT,
    sender TEXT,
    broadcaster TEXT,
    recipient TEXT,
    partner TEXT,
    timestamp INTEGER,
    affiliate_token TEXT,
    affiliate_amount TEXT
)''')
conn.commit()

# Set up web3 for decoding
w3 = Web3()
event_abi = PORTAL_EVENT_ABI

def decode_portal_event(log):
    topics = log['topics']
    data = log['data']
    try:
        decoded = Web3().codec.decode_abi(
            ["address", "uint256", "address", "uint256", "address"],
            bytes.fromhex(data[2:])
        )
    except Exception:
        try:
            # Try eth-abi v2/v1
            from eth_abi import decode_abi
            decoded = decode_abi(
                ["address", "uint256", "address", "uint256", "address"],
                bytes.fromhex(data[2:])
            )
        except ImportError:
            # Try eth-abi v5+
            from eth_abi import decode
            decoded = decode(
                ["address", "uint256", "address", "uint256", "address"],
                bytes.fromhex(data[2:])
            )
    input_token, input_amount, output_token, output_amount, recipient = decoded
    sender = Web3.to_checksum_address('0x' + topics[1][26:])
    broadcaster = Web3.to_checksum_address('0x' + topics[2][26:])
    partner = Web3.to_checksum_address('0x' + topics[3][26:])
    return {
        'input_token': input_token,
        'input_amount': str(input_amount),
        'output_token': output_token,
        'output_amount': str(output_amount),
        'recipient': recipient,
        'sender': sender,
        'broadcaster': broadcaster,
        'partner': partner
    }

def get_block_timestamp(block_number):
    url = f"{ETHERSCAN_API_URL}?module=block&action=getblockreward&blockno={block_number}&apikey={ETHERSCAN_API_KEY}"
    resp = requests.get(url)
    result = resp.json()
    if result.get("status") == "1":
        return int(result["result"]["timeStamp"])
    return None

def fetch_and_decode_affiliate_payment(tx_hash: str, partner: str, recipient: str) -> tuple[str, str]:
    """
    Fetch all logs for the transaction and return (token_address, amount) for the affiliate payment to the partner only.
    Returns (None, None) if not found or on error.
    """
    try:
        url = f"{ETHERSCAN_API_URL}?module=proxy&action=eth_getTransactionReceipt&txhash={tx_hash}&apikey={ETHERSCAN_API_KEY}"
        resp = requests.get(url)
        receipt = resp.json().get("result")
        if not receipt or "logs" not in receipt:
            return (None, None)
        logs = receipt["logs"]
        transfer_topic = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
        for log in logs:
            try:
                if log["topics"][0].lower() == transfer_topic:
                    if len(log["topics"]) < 3:
                        print(f"Warning: Transfer log in tx {tx_hash} has fewer than 3 topics, skipping.")
                        continue
                    to_addr = "0x" + log["topics"][2][-40:]
                    if Web3.to_checksum_address(to_addr) == Web3.to_checksum_address(partner):
                        token = log["address"]
                        try:
                            amount = int(log["data"], 16)
                        except Exception as e:
                            print(f"Warning: Could not decode amount in log for tx {tx_hash}: {e}")
                            amount = None
                        return (token, str(amount) if amount is not None else None)
            except Exception as e:
                print(f"Warning: Error processing log in tx {tx_hash}: {e}")
                continue
        return (None, None)
    except Exception as e:
        print(f"Error fetching affiliate payment for tx {tx_hash}: {e}")
        return (None, None)

if data.get("status") == "1":
    # Process the 10 most recent events (latest first)
    logs = data["result"][::-1]  # reverse order
    count = 0
    for log in logs:
        if count >= 10:
            break
        tx_hash = log["transactionHash"]
        # Check if this tx_hash is already in the DB
        c.execute(f'SELECT 1 FROM {DB_TABLE} WHERE tx_hash = ?', (tx_hash,))
        if c.fetchone():
            continue  # Skip if already logged
        block_number = int(log["blockNumber"], 16)
        decoded = decode_portal_event(log)
        timestamp = get_block_timestamp(block_number)
        affiliate_token, affiliate_amount = fetch_and_decode_affiliate_payment(tx_hash, decoded['partner'], decoded['recipient'])
        c.execute(f'''INSERT INTO {DB_TABLE} (
            tx_hash, block_number, input_token, input_amount, output_token, output_amount, sender, broadcaster, recipient, partner, timestamp, affiliate_token, affiliate_amount
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (
            tx_hash, block_number, decoded['input_token'], decoded['input_amount'], decoded['output_token'], decoded['output_amount'],
            decoded['sender'], decoded['broadcaster'], decoded['recipient'], decoded['partner'], timestamp, affiliate_token, affiliate_amount
        ))
        print(f"Saved event: tx_hash={tx_hash}, block={block_number}, input_amount={decoded['input_amount']}, output_amount={decoded['output_amount']}, affiliate_token={affiliate_token}, affiliate_amount={affiliate_amount}")
        count += 1
    conn.commit()
else:
    print("No logs found or error:", data.get("message"))

conn.close() 