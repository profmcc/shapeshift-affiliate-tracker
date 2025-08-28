import sys
import requests
import json
from typing import Optional

ETHERSCAN_API_KEY = "3F2DTAIMWNBEFTNKNUKJHKBKR4A9ZUW4HN"
ETHERSCAN_API_URL = "https://api.etherscan.io/api"


def fetch_abi(address: str, api_key: str = ETHERSCAN_API_KEY) -> Optional[str]:
    """Fetch contract ABI from Etherscan. Returns ABI JSON string or None on failure."""
    params = {
        "module": "contract",
        "action": "getabi",
        "address": address,
        "apikey": api_key,
    }
    try:
        resp = requests.get(ETHERSCAN_API_URL, params=params, timeout=10)
        data = resp.json()
        if data.get("status") == "1":
            return data["result"]
        else:
            print(f"Error: {data.get('result') or data.get('message')}")
    except Exception as e:
        print(f"Request error: {e}")
    return None


def save_abi(address: str, abi_json: str) -> None:
    """Save ABI JSON string to a file named <address>.abi.json."""
    filename = f"{address}.abi.json"
    with open(filename, "w") as f:
        f.write(abi_json)
    print(f"ABI saved to {filename}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python fetch_contract_abi.py <contract_address>")
        sys.exit(1)
    address = sys.argv[1]
    abi_json = fetch_abi(address)
    if abi_json:
        save_abi(address, abi_json)
    else:
        print("Failed to fetch ABI.")
