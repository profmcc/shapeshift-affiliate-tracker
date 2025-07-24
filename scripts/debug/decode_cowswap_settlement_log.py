import sys
from web3 import Web3
from eth_abi import decode
from eth_utils import decode_hex
import requests
import json
import os
from web3._utils.events import get_event_data
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../shared')))
from token_cache import get_token_info, init_web3

INFURA_URL = 'https://mainnet.infura.io/v3/208a3474635e4ebe8ee409cef3fbcd40'
COW_API_URL = 'https://api.cow.fi/mainnet/api/v1/app_data/'
ABI_PATH = os.path.join(os.path.dirname(__file__), 'cowswap_settlement_abi.json')

# Static token symbol mapping for common tokens
TOKEN_SYMBOLS = {
    '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48'.lower(): 'USDC',
    '0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE'.lower(): 'ETH',
    '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2'.lower(): 'WETH',
    # Add more as needed
}

EXAMPLE_TX_HASH = '0x5b9feed8d8ea714e9a5371f727b81ade545379fe8e786d3c4df93ab25bc14915'


def fetch_app_code(app_data_hash: str) -> str:
    try:
        url = COW_API_URL + app_data_hash
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return data.get('metadata', {}).get('appCode', '(no appCode)')
        return '(not found)'
    except Exception as e:
        return f'(error: {e})'

def load_abi() -> list:
    with open(ABI_PATH, 'r') as f:
        return json.load(f)

def get_trade_event_abi(abi):
    for item in abi:
        if item.get('type') == 'event' and item.get('name') == 'Trade':
            return item
    return None

def get_trade_event_signature(abi):
    for item in abi:
        if item.get('type') == 'event' and item.get('name') == 'Trade':
            from web3._utils.events import event_abi_to_log_topic
            return event_abi_to_log_topic(item).hex()
    return None

def token_info(address: str):
    info = get_token_info(address.lower())
    if info and info.get('symbol'):
        return info['symbol'], info.get('decimals', 18)
    # fallback to static mapping
    return TOKEN_SYMBOLS.get(address.lower(), address), 18

def format_amount(amount: int, decimals: int) -> str:
    try:
        return f'{amount / (10 ** decimals):,.6f}'
    except Exception:
        return str(amount)

def print_log_info(log, trade_event_abi, w3):
    print(f'LogIndex: {log["logIndex"]}, Address: {log["address"]}')
    topic_hexes = [t.hex() for t in log["topics"]]
    print(f'  Topics: {topic_hexes}')
    data_bytes = log["data"] if isinstance(log["data"], bytes) else bytes.fromhex(log["data"][2:] if log["data"].startswith('0x') else log["data"]) 
    data_hex = data_bytes.hex()
    print(f'  Data (hex): {data_hex}')
    # Try to decode with get_event_data
    try:
        decoded_event = get_event_data(w3.codec, trade_event_abi, log)
        print(f'  Decoded Trade Event:')
        args = decoded_event["args"]
        # Token info and formatting
        sell_symbol, sell_decimals = token_info(args["sellToken"])
        buy_symbol, buy_decimals = token_info(args["buyToken"])
        print(f'    owner: {args["owner"]}')
        print(f'    sellToken: {args["sellToken"]} ({sell_symbol})')
        print(f'    buyToken: {args["buyToken"]} ({buy_symbol})')
        print(f'    sellAmount: {args["sellAmount"]} ({format_amount(args["sellAmount"], sell_decimals)} {sell_symbol})')
        print(f'    buyAmount: {args["buyAmount"]} ({format_amount(args["buyAmount"], buy_decimals)} {buy_symbol})')
        print(f'    feeAmount: {args["feeAmount"]} ({format_amount(args["feeAmount"], sell_decimals)} {sell_symbol})')
        # Print orderUid as hex string
        order_uid_bytes = args["orderUid"]
        if isinstance(order_uid_bytes, (bytes, bytearray)):
            order_uid_hex = '0x' + order_uid_bytes.hex()
        else:
            order_uid_hex = str(order_uid_bytes)
        print(f'    orderUid: {order_uid_hex}')
    except Exception as e:
        print(f'  (Error decoding as Trade event: {e})')


def process_tx(tx_hash: str, w3, trade_event_abi, trade_sig):
    try:
        receipt = w3.eth.get_transaction_receipt(tx_hash)
    except Exception as e:
        print(f'Error fetching receipt for {tx_hash}: {e}')
        return
    found = False
    for log in receipt['logs']:
        if log['topics'][0].hex() == trade_sig:
            print('='*60)
            print(f'Transaction: {tx_hash}')
            print_log_info(log, trade_event_abi, w3)
            found = True
    if not found:
        print(f'No Trade events found in transaction {tx_hash}.')


def main():
    w3 = Web3(Web3.HTTPProvider(INFURA_URL))
    init_web3(INFURA_URL)
    abi = load_abi()
    trade_event_abi = get_trade_event_abi(abi)
    trade_sig = get_trade_event_signature(abi)
    if not trade_event_abi or not trade_sig:
        print('Could not find Trade event ABI or signature in ABI.')
        return
    if len(sys.argv) == 2:
        arg = sys.argv[1]
        if arg.endswith('.txt'):
            # Batch mode: file with tx hashes
            with open(arg, 'r') as f:
                tx_hashes = [line.strip() for line in f if line.strip()]
            for tx_hash in tx_hashes:
                process_tx(tx_hash, w3, trade_event_abi, trade_sig)
        else:
            # Single tx
            process_tx(arg, w3, trade_event_abi, trade_sig)
    else:
        print('Usage: python decode_cowswap_settlement_log.py <tx_hash | tx_hashes.txt>')
        print('Example:')
        print(f'  python decode_cowswap_settlement_log.py {EXAMPLE_TX_HASH}')
        print('  python decode_cowswap_settlement_log.py tx_hashes.txt')

if __name__ == '__main__':
    main() 