import pytest
from listeners.portals_listener import parse_erc20_transfer_event, parse_portals_event

class MockEth:
    def get_transaction(self, tx_hash):
        return {'to': '0x1234567890abcdef1234567890abcdef12345678'}
    def get_block(self, block_number):
        return {'timestamp': 1234567890}

@pytest.fixture
def mock_w3():
    class W3:
        eth = MockEth()
    return W3()

def test_parse_erc20_transfer_event(mock_w3):
    log = {
        'topics': [
            bytes.fromhex('ddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'),
            bytes.fromhex('000000000000000000000000aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'),
            bytes.fromhex('000000000000000000000000bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb')
        ],
        'transactionHash': bytes.fromhex('c0ffee' * 5),
        'blockNumber': 123,
        'address': '0xTokenAddress',
        'data': bytes.fromhex('00000000000000000000000000000000000000000000000000000000000003e8')
    }
    event = parse_erc20_transfer_event(log, 'ethereum', '0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb', ['0x1234567890abcdef1234567890abcdef12345678'], mock_w3)
    assert event['chain'] == 'ethereum'
    assert event['token'] == '0xTokenAddress'
    assert event['amount'] == '1000'
    assert event['recipient'].lower() == '0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb'

def test_parse_portals_event(mock_w3):
    log = {
        'topics': [
            bytes.fromhex('b1b2b3b4b5b6b7b8b9babbbcbdbebfc0c1c2c3c4c5c6c7c8c9cacbcccdcecfc0'),
            bytes.fromhex('000000000000000000000000aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'),
            bytes.fromhex('000000000000000000000000bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb'),
            bytes.fromhex('000000000000000000000000cccccccccccccccccccccccccccccccccccccccc')
        ],
        'transactionHash': bytes.fromhex('c0ffee' * 5),
        'blockNumber': 123,
        'data': '0x' + '00' * 160
    }
    event = parse_portals_event(log, 'ethereum', mock_w3)
    assert event['chain'] == 'ethereum'
    assert event['sender'].lower() == '0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
    assert event['broadcaster'].lower() == '0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb'
    assert event['partner'].lower() == '0xcccccccccccccccccccccccccccccccccccccccc' 