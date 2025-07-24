from web3 import Web3
from eth_utils import to_checksum_address, to_canonical_address

alchemy_url = 'https://eth-mainnet.g.alchemy.com/v2/_3x-ZVAe8aKBUMeRax2zOjg0fotYb3ms'
w3 = Web3(Web3.HTTPProvider(alchemy_url))

tx_hash = '0xd7d46e63a336b66ee58b038439d65c8cdfd952fcb66e2af3ee3b09e76a4e7b3c'
dao_address = '0x90A48D5CF7343B08dA12E067680B4C6dbfE551Be'
portals_router = '0xbf5A7F3629fB325E2a8453D595AB103465F75E62'

tx = w3.eth.get_transaction(tx_hash)
receipt = w3.eth.get_transaction_receipt(tx_hash)

found = False
for log in receipt['logs']:
    if log['topics'][0].hex() == '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef':
        to_addr = '0x' + log['topics'][2].hex()[-40:]
        if (to_checksum_address(to_addr) == to_checksum_address(dao_address) and
            to_checksum_address(tx['to']) == to_checksum_address(portals_router)):
            print('Captured:', log)
            found = True

print('Found:', found) 