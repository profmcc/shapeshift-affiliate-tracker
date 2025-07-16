from web3 import Web3
from typing import Dict

# Hardcoded decimals for common tokens (add more as needed)
COMMON_TOKEN_DECIMALS: Dict[str, int] = {
    # Ethereum mainnet
    '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48': 6,   # USDC
    '0xdac17f958d2ee523a2206206994597c13d831ec7': 6,   # USDT
    '0x6b175474e89094c44da98b954eedeac495271d0f': 18,  # DAI
    '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2'.lower(): 18, # WETH
    '0xc770eefad204b5180df6a14ee197d99d808ee52d': 18,  # FOX
    '0x2260fac5e5542a773aa44fbcfedf7c193bc2c599': 8,   # WBTC
    # Add more tokens as needed
}

ERC20_ABI = [
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function"
    }
]

def get_token_decimals(token_address: str, w3: Web3 = None) -> int:
    """
    Get the decimals for a token address. Use hardcoded map for common tokens, fallback to web3 if available.
    """
    address = token_address.lower()
    if address in COMMON_TOKEN_DECIMALS:
        return COMMON_TOKEN_DECIMALS[address]
    if w3 is not None:
        try:
            contract = w3.eth.contract(address=Web3.to_checksum_address(token_address), abi=ERC20_ABI)
            return contract.functions.decimals().call()
        except Exception:
            pass
    # Default to 18 if unknown
    return 18
