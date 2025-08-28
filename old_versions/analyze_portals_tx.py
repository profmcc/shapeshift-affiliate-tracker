import os
from dotenv import load_dotenv

load_dotenv()
from web3 import Web3
import requests
from shared.token_cache import get_token_info, init_web3
import json
from web3._utils.events import event_abi_to_log_topic

# --- CONFIG ---
ALCHEMY_API_KEY = os.getenv("ALCHEMY_API_KEY")
INFURA_API_KEY = os.getenv("INFURA_API_KEY")
if ALCHEMY_API_KEY:
    ETH_RPC = f"https://eth-mainnet.g.alchemy.com/v2/{ALCHEMY_API_KEY}"
elif INFURA_API_KEY:
    ETH_RPC = f"https://mainnet.infura.io/v3/{INFURA_API_KEY}"
else:
    raise RuntimeError("No Ethereum RPC key found in .env")
init_web3(ETH_RPC)
COINGECKO_URL = "https://api.coingecko.com/api/v3/simple/token_price/ethereum"
SHAPESHIFT_DAO = "0x90A48D5CF7343B08dA12E067680B4C6dbfE551Be".lower()
PORTALS_ABI_JSON = """[{"anonymous":false,"inputs":[{"indexed":false,"internalType":"address","name":"inputToken","type":"address"},{"indexed":false,"internalType":"uint256","name":"inputAmount","type":"uint256"},{"indexed":false,"internalType":"address","name":"outputToken","type":"address"},{"indexed":false,"internalType":"uint256","name":"outputAmount","type":"uint256"},{"indexed":true,"internalType":"address","name":"sender","type":"address"},{"indexed":true,"internalType":"address","name":"broadcaster","type":"address"},{"indexed":false,"internalType":"address","name":"recipient","type":"address"},{"indexed":true,"internalType":"address","name":"partner","type":"address"}],"name":"Portal","type":"event"}]"""
PORTALS_ABI = json.loads(PORTALS_ABI_JSON)


# --- HELPERS ---
def get_token_price_coingecko(address: str, block: int) -> float:
    # Special case for ETH
    if address.lower() == "0x0000000000000000000000000000000000000000":
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {"ids": "ethereum", "vs_currencies": "usd"}
        try:
            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            price = data.get("ethereum", {}).get("usd")
            return float(price) if price else 0.0
        except Exception as e:
            print(f"[DEBUG] CoinGecko ETH price error: {e}")
            return 0.0
    # ERC-20 tokens
    params = {
        "contract_addresses": address,
        "vs_currencies": "usd",
    }
    try:
        resp = requests.get(COINGECKO_URL, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        price = data.get(address.lower(), {}).get("usd")
        return float(price) if price else 0.0
    except Exception as e:
        print(f"[DEBUG] CoinGecko price error for {address}: {e}")
        return 0.0


def parse_erc20_transfer(log):
    from_addr = "0x" + log["topics"][1].hex()[-40:]
    to_addr = "0x" + log["topics"][2].hex()[-40:]
    token = log["address"]
    amount = int(log["data"].hex(), 16)
    return {"from": from_addr, "to": to_addr, "token": token, "amount": amount}


def analyze_portals_tx(tx_hash: str):
    w3 = Web3(Web3.HTTPProvider(ETH_RPC))
    receipt = w3.eth.get_transaction_receipt(tx_hash)
    block = w3.eth.get_block(receipt["blockNumber"])
    timestamp = block["timestamp"]
    print(f"Block: {receipt['blockNumber']} Timestamp: {timestamp}")
    # ETH transfer (value field)
    tx = w3.eth.get_transaction(tx_hash)
    if tx["value"] > 0:
        eth_value = Web3.from_wei(tx["value"], "ether")
        price = get_token_price_coingecko(
            "0x0000000000000000000000000000000000000000", receipt["blockNumber"]
        )
        usd = eth_value * price
        print(f"ETH sent: {eth_value} ETH, USD: {usd}")
    # Parse logs
    affiliate_fees = []
    volume_transfers = []
    portal_events = []
    contract = w3.eth.contract(abi=PORTALS_ABI)
    portal_event_abi = PORTALS_ABI[0]
    portal_topic = event_abi_to_log_topic(portal_event_abi).hex()
    for log in receipt["logs"]:
        if not log["topics"]:
            continue
        # ERC-20 Transfer
        if (
            log["topics"][0].hex()
            == "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
        ):
            transfer = parse_erc20_transfer(log)
            if transfer["to"].lower() == SHAPESHIFT_DAO:
                info = get_token_info(transfer["token"])
                price = get_token_price_coingecko(
                    transfer["token"], receipt["blockNumber"]
                )
                decimals = (
                    info["decimals"]
                    if info and info.get("decimals") is not None
                    else 18
                )
                amount_adj = transfer["amount"] / (10**decimals)
                usd = amount_adj * price
                affiliate_fees.append(
                    {"token": transfer["token"], "amount": amount_adj, "usd": usd}
                )
            else:
                volume_transfers.append(transfer)
        # Portal event
        elif log["topics"][0].hex() == portal_topic:
            try:
                decoded = contract.events.Portal().process_log(log)
                args = decoded["args"]
                portal_events.append(args)
            except Exception as e:
                print(f"[DEBUG] Error decoding Portal event: {e}")
    print("Affiliate Fees:")
    for fee in affiliate_fees:
        print(f"  Token: {fee['token']} Amount: {fee['amount']} USD: {fee['usd']}")
    print("Volume Transfers:")
    for t in volume_transfers:
        info = get_token_info(t["token"])
        price = get_token_price_coingecko(t["token"], receipt["blockNumber"])
        decimals = info["decimals"] if info and info.get("decimals") is not None else 18
        amount_adj = t["amount"] / (10**decimals)
        usd = amount_adj * price
        print(
            f"  Token: {t['token']} From: {t['from']} To: {t['to']} Amount: {amount_adj} USD: {usd}"
        )
    print("Portal Events:")
    for ev in portal_events:
        # Calculate USD values for input and output
        input_token = ev["inputToken"]
        output_token = ev["outputToken"]
        input_amount = int(ev["inputAmount"])
        output_amount = int(ev["outputAmount"])
        input_info = get_token_info(input_token)
        output_info = get_token_info(output_token)
        input_decimals = (
            input_info["decimals"]
            if input_info and input_info.get("decimals") is not None
            else 18
        )
        output_decimals = (
            output_info["decimals"]
            if output_info and output_info.get("decimals") is not None
            else 18
        )
        input_amount_adj = input_amount / (10**input_decimals)
        output_amount_adj = output_amount / (10**output_decimals)
        input_price = get_token_price_coingecko(input_token, receipt["blockNumber"])
        output_price = get_token_price_coingecko(output_token, receipt["blockNumber"])
        input_usd = input_amount_adj * input_price
        output_usd = output_amount_adj * output_price
        print(
            f"  inputToken: {input_token} inputAmount: {input_amount} ({input_amount_adj} adj, ${input_usd} USD) outputToken: {output_token} outputAmount: {output_amount} ({output_amount_adj} adj, ${output_usd} USD) sender: {ev['sender']} broadcaster: {ev['broadcaster']} recipient: {ev['recipient']} partner: {ev['partner']}"
        )


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python analyze_portals_tx.py <tx_hash>")
        exit(1)
    analyze_portals_tx(sys.argv[1])
