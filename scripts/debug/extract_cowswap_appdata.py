import json
from web3 import Web3
from eth_abi import decode_abi
from eth_utils import function_signature_to_4byte_selector

# CowSwap Settlement contract ABI (truncated to just the settle function for brevity)
ABI = [
    {
        "inputs": [
            {"internalType": "contract IERC20[]", "name": "tokens", "type": "address[]"},
            {"internalType": "uint256[]", "name": "clearingPrices", "type": "uint256[]"},
            {
                "components": [
                    {"internalType": "uint256", "name": "sellTokenIndex", "type": "uint256"},
                    {"internalType": "uint256", "name": "buyTokenIndex", "type": "uint256"},
                    {"internalType": "address", "name": "receiver", "type": "address"},
                    {"internalType": "uint256", "name": "sellAmount", "type": "uint256"},
                    {"internalType": "uint256", "name": "buyAmount", "type": "uint256"},
                    {"internalType": "uint32", "name": "validTo", "type": "uint32"},
                    {"internalType": "bytes32", "name": "appData", "type": "bytes32"},
                    {"internalType": "uint256", "name": "feeAmount", "type": "uint256"},
                    {"internalType": "uint256", "name": "flags", "type": "uint256"},
                    {"internalType": "uint256", "name": "executedAmount", "type": "uint256"},
                    {"internalType": "bytes", "name": "signature", "type": "bytes"}
                ],
                "internalType": "struct GPv2Trade.Data[]",
                "name": "trades",
                "type": "tuple[]"
            },
            {
                "components": [
                    {"internalType": "address", "name": "target", "type": "address"},
                    {"internalType": "uint256", "name": "value", "type": "uint256"},
                    {"internalType": "bytes", "name": "callData", "type": "bytes"}
                ],
                "internalType": "struct GPv2Interaction.Data[][3]",
                "name": "interactions",
                "type": "tuple[][3]"
            }
        ],
        "name": "settle",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

# Transaction hash to analyze
TX_HASH = "0x187c568abb795fe2e375af3c2870427cfa895c596455be106877a3a63a483341"
INFURA_URL = "https://mainnet.infura.io/v3/208a3474635e4ebe8ee409cef3fbcd40"

w3 = Web3(Web3.HTTPProvider(INFURA_URL))
tx = w3.eth.get_transaction(TX_HASH)
input_data = tx['input']

# Find the function selector for settle
settle_fn_abi = [item for item in ABI if item['name'] == 'settle'][0]
settle_sig = 'settle(address[],uint256[],(uint256,uint256,address,uint256,uint256,uint32,bytes32,uint256,uint256,uint256,bytes)[],(address,uint256,bytes)[3])'
selector = function_signature_to_4byte_selector(settle_sig)

# Remove the selector (first 4 bytes)
input_bytes = bytes.fromhex(input_data[2:])
params_bytes = input_bytes[4:]

# Decode using eth_abi (must match the ABI types exactly)
abi_types = [
    'address[]',
    'uint256[]',
    'tuple[]',
    'tuple[3][]'
]
trade_tuple_type = (
    'tuple(uint256,uint256,address,uint256,uint256,uint32,bytes32,uint256,uint256,uint256,bytes)'
)

# eth_abi does not support nested dynamic arrays in one call, so use web3's contract decode
contract = w3.eth.contract(abi=ABI)
decoded = contract.decode_function_input(input_data)

# Extract trades
trades = decoded[1]['trades']

print("appData fields in this transaction:")
for i, trade in enumerate(trades):
    app_data = trade['appData']
    print(f"Trade {i+1}: appData = {app_data.hex()} (hex)")
    try:
        ascii_str = bytes.fromhex(app_data.hex()[2:]).decode('utf-8', errors='replace')
        print(f"           appData (ascii): {ascii_str}")
    except Exception:
        pass 