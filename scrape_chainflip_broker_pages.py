#!/usr/bin/env python3
"""
Scrape Chainflip Broker Pages for Balance Information
Scrapes the actual broker pages to extract balance and transaction data
"""

import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime
import re

def scrape_broker_page(broker_address: str):
    """Scrape a specific broker page for balance information"""
    
    url = f"https://scan.chainflip.io/brokers/{broker_address}"
    
    print(f"🔍 Scraping broker page: {url}")
    
    try:
        # Set headers to mimic a browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            print(f"✅ Successfully retrieved page")
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for balance information in the page
            balance_info = extract_balance_info(soup, broker_address)
            
            # Look for transaction data
            transaction_info = extract_transaction_info(soup, broker_address)
            
            # Look for any JSON data embedded in the page
            embedded_data = extract_embedded_data(response.text, broker_address)
            
            return {
                'address': broker_address,
                'url': url,
                'status_code': response.status_code,
                'balance_info': balance_info,
                'transaction_info': transaction_info,
                'embedded_data': embedded_data,
                'page_length': len(response.text),
                'queried_at': datetime.now().isoformat()
            }
            
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return {
                'address': broker_address,
                'url': url,
                'status_code': response.status_code,
                'error': f"HTTP {response.status_code}"
            }
            
    except Exception as e:
        print(f"❌ Error scraping {broker_address}: {e}")
        return {
            'address': broker_address,
            'url': url,
            'error': str(e)
        }

def extract_balance_info(soup, broker_address):
    """Extract balance information from the HTML"""
    
    balance_info = {
        'balance': None,
        'currency': None,
        'balance_elements': []
    }
    
    # Look for balance-related text
    balance_patterns = [
        r'(\d+\.?\d*)\s*(FLIP|USDC|ETH|BTC|USD)',
        r'Balance[:\s]*(\d+\.?\d*)',
        r'(\d+\.?\d*)\s*Chainflip',
        r'Total[:\s]*(\d+\.?\d*)'
    ]
    
    # Search in text content
    page_text = soup.get_text()
    
    for pattern in balance_patterns:
        matches = re.findall(pattern, page_text, re.IGNORECASE)
        if matches:
            balance_info['balance_elements'].extend(matches)
    
    # Look for specific HTML elements that might contain balance
    balance_elements = soup.find_all(['div', 'span', 'p'], class_=re.compile(r'balance|amount|value', re.I))
    
    for elem in balance_elements:
        text = elem.get_text().strip()
        if text and len(text) < 100:  # Reasonable length for balance
            balance_info['balance_elements'].append(text)
    
    # Look for data attributes that might contain balance
    data_elements = soup.find_all(attrs={'data-balance': True})
    for elem in data_elements:
        balance_info['balance_elements'].append(elem['data-balance'])
    
    return balance_info

def extract_transaction_info(soup, broker_address):
    """Extract transaction information from the HTML"""
    
    transaction_info = {
        'transaction_count': None,
        'last_transaction': None,
        'volume': None,
        'fees': None
    }
    
    # Look for transaction-related text
    tx_patterns = [
        r'(\d+)\s*transactions?',
        r'Volume[:\s]*(\d+\.?\d*)',
        r'Fees[:\s]*(\d+\.?\d*)',
        r'Total[:\s]*(\d+\.?\d*)'
    ]
    
    page_text = soup.get_text()
    
    for pattern in tx_patterns:
        matches = re.findall(pattern, page_text, re.IGNORECASE)
        if matches:
            if 'transaction' in pattern:
                transaction_info['transaction_count'] = matches[0]
            elif 'volume' in pattern:
                transaction_info['volume'] = matches[0]
            elif 'fees' in pattern:
                transaction_info['fees'] = matches[0]
    
    return transaction_info

def extract_embedded_data(html_text, broker_address):
    """Extract any embedded JSON data from the HTML"""
    
    embedded_data = {
        'json_blocks': [],
        'script_data': []
    }
    
    # Look for JSON blocks in script tags
    json_pattern = r'<script[^>]*type="application/json"[^>]*>(.*?)</script>'
    json_matches = re.findall(json_pattern, html_text, re.DOTALL | re.IGNORECASE)
    
    for match in json_matches:
        try:
            data = json.loads(match)
            embedded_data['json_blocks'].append(data)
        except json.JSONDecodeError:
            pass
    
    # Look for data in __NEXT_DATA__ script
    next_data_pattern = r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>'
    next_data_matches = re.findall(next_data_pattern, html_text, re.DOTALL)
    
    for match in next_data_matches:
        try:
            data = json.loads(match)
            embedded_data['script_data'].append(data)
        except json.JSONDecodeError:
            pass
    
    return embedded_data

def main():
    """Main function to scrape broker pages"""
    
    # ShapeShift affiliate addresses
    brokers = [
        {
            'address': 'cFMeDPtPHccVYdBSJKTtCYuy7rewFNpro3xZBKaCGbSS2xhRi',
            'name': 'ShapeShift Broker 1'
        },
        {
            'address': 'cFK6mYjpajcwPDZ7JUsac8XUoVSJnhjL43ZMZW7YoN8HE4dD8',
            'name': 'ShapeShift Broker 2'
        }
    ]
    
    print("🚀 Starting Chainflip broker page scraping...")
    print(f"⏰ Time: {datetime.now().isoformat()}")
    
    results = []
    
    for broker in brokers:
        print(f"\n{'='*60}")
        print(f"🔍 Scraping: {broker['name']}")
        print(f"Address: {broker['address']}")
        print(f"{'='*60}")
        
        # Scrape the broker page
        broker_data = scrape_broker_page(broker['address'])
        
        # Add broker metadata
        broker_data['broker_name'] = broker['name']
        broker_data['broker_address'] = broker['address']
        
        results.append(broker_data)
        
        # Rate limiting
        time.sleep(2)
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"chainflip_broker_scraping_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to: {filename}")
    
    # Display summary
    print(f"\n{'='*60}")
    print(f"💰 CHAINFLIP BROKER SCRAPING SUMMARY")
    print(f"{'='*60}")
    
    for result in results:
        print(f"\n{result['broker_name']}:")
        print(f"  Address: {result['address']}")
        print(f"  Status: {result.get('status_code', 'N/A')}")
        
        if result.get('balance_info', {}).get('balance_elements'):
            print(f"  Balance Elements: {len(result['balance_info']['balance_elements'])} found")
            for elem in result['balance_info']['balance_elements'][:3]:  # Show first 3
                print(f"    - {elem}")
        
        if result.get('transaction_info', {}).get('transaction_count'):
            print(f"  Transactions: {result['transaction_info']['transaction_count']}")
        
        if result.get('embedded_data', {}).get('json_blocks'):
            print(f"  JSON Blocks: {len(result['embedded_data']['json_blocks'])} found")
    
    print(f"{'='*60}")
    
    return results

if __name__ == "__main__":
    main()
