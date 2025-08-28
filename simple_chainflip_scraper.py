#!/usr/bin/env python3
"""
Simple Chainflip Broker Scraper
Scrapes broker pages without external dependencies
"""

import requests
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
            
            # Extract data from HTML text
            balance_info = extract_balance_info(response.text, broker_address)
            transaction_info = extract_transaction_info(response.text, broker_address)
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

def extract_balance_info(html_text, broker_address):
    """Extract balance information from the HTML text"""
    
    balance_info = {
        'balance': None,
        'currency': None,
        'balance_elements': []
    }
    
    # Look for balance-related text patterns
    balance_patterns = [
        r'(\d+\.?\d*)\s*(FLIP|USDC|ETH|BTC|USD)',
        r'Balance[:\s]*(\d+\.?\d*)',
        r'(\d+\.?\d*)\s*Chainflip',
        r'Total[:\s]*(\d+\.?\d*)',
        r'(\d+\.?\d*)\s*coins?',
        r'(\d+\.?\d*)\s*tokens?'
    ]
    
    for pattern in balance_patterns:
        matches = re.findall(pattern, html_text, re.IGNORECASE)
        if matches:
            balance_info['balance_elements'].extend(matches)
    
    # Look for specific HTML patterns
    html_patterns = [
        r'<[^>]*class="[^"]*balance[^"]*"[^>]*>([^<]+)</[^>]*>',
        r'<[^>]*class="[^"]*amount[^"]*"[^>]*>([^<]+)</[^>]*>',
        r'<[^>]*class="[^"]*value[^"]*"[^>]*>([^<]+)</[^>]*>'
    ]
    
    for pattern in html_patterns:
        matches = re.findall(pattern, html_text, re.IGNORECASE)
        if matches:
            for match in matches:
                text = match.strip()
                if text and len(text) < 100:  # Reasonable length for balance
                    balance_info['balance_elements'].append(text)
    
    # Look for data attributes
    data_patterns = [
        r'data-balance="([^"]*)"',
        r'data-amount="([^"]*)"',
        r'data-value="([^"]*)"'
    ]
    
    for pattern in data_patterns:
        matches = re.findall(pattern, html_text)
        if matches:
            balance_info['balance_elements'].extend(matches)
    
    return balance_info

def extract_transaction_info(html_text, broker_address):
    """Extract transaction information from the HTML text"""
    
    transaction_info = {
        'transaction_count': None,
        'last_transaction': None,
        'volume': None,
        'fees': None
    }
    
    # Look for transaction-related text patterns
    tx_patterns = [
        r'(\d+)\s*transactions?',
        r'Volume[:\s]*(\d+\.?\d*)',
        r'Fees[:\s]*(\d+\.?\d*)',
        r'Total[:\s]*(\d+\.?\d*)',
        r'(\d+)\s*swaps?',
        r'(\d+)\s*trades?'
    ]
    
    for pattern in tx_patterns:
        matches = re.findall(pattern, html_text, re.IGNORECASE)
        if matches:
            if 'transaction' in pattern:
                transaction_info['transaction_count'] = matches[0]
            elif 'volume' in pattern:
                transaction_info['volume'] = matches[0]
            elif 'fees' in pattern:
                transaction_info['fees'] = matches[0]
            elif 'swap' in pattern:
                transaction_info['transaction_count'] = matches[0]
    
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
    
    # Look for any other script content that might contain data
    script_pattern = r'<script[^>]*>(.*?)</script>'
    script_matches = re.findall(script_pattern, html_text, re.DOTALL)
    
    for match in script_matches:
        # Look for JSON-like content in scripts
        if '{' in match and '}' in match:
            # Try to extract JSON-like objects
            json_like_pattern = r'\{[^{}]*"[^"]*"[^{}]*\}'
            json_like_matches = re.findall(json_like_pattern, match)
            
            for json_like in json_like_matches:
                try:
                    # Try to make it valid JSON
                    cleaned = re.sub(r'([{,])\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', json_like)
                    data = json.loads(cleaned)
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
    filename = f"simple_chainflip_scraping_{timestamp}.json"
    
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
        
        if result.get('embedded_data', {}).get('script_data'):
            print(f"  Script Data: {len(result['embedded_data']['script_data'])} found")
    
    print(f"{'='*60}")
    
    return results

if __name__ == "__main__":
    main()
