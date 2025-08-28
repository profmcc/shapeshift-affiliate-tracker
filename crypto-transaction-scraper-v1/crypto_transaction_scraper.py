#!/usr/bin/env python3
"""
Crypto Transaction Web Scraper using Firecrawl API

This scraper is specifically designed for crypto transactions and can:
- Handle abbreviated transaction hashes and wallet addresses
- Extract full addresses from hover elements
- Parse various crypto explorer formats
- Handle dynamic content with JavaScript rendering
- Extract structured transaction data

Author: AI Assistant
License: MIT
"""

import os
import json
import re
import time
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import logging
from pathlib import Path

try:
    from firecrawl import Firecrawl
except ImportError:
    print("Firecrawl not installed. Installing...")
    import subprocess
    subprocess.check_call(["pip", "install", "firecrawl-py"])
    from firecrawl import Firecrawl

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class CryptoAddress:
    """Represents a crypto address with metadata"""
    address: str
    address_type: str  # 'wallet', 'contract', 'transaction', 'unknown'
    network: str
    abbreviated: str
    full_address: str
    confidence: float  # 0.0 to 1.0
    source_element: str  # HTML element where found
    hover_text: Optional[str] = None

@dataclass
class TransactionData:
    """Represents extracted transaction data"""
    tx_hash: Optional[str] = None
    from_address: Optional[CryptoAddress] = None
    to_address: Optional[CryptoAddress] = None
    amount: Optional[str] = None
    token: Optional[str] = None
    gas_fee: Optional[str] = None
    block_number: Optional[int] = None
    timestamp: Optional[datetime] = None
    status: Optional[str] = None
    network: Optional[str] = None
    explorer_url: Optional[str] = None

class CryptoTransactionScraper:
    """
    Advanced crypto transaction scraper using Firecrawl API
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the scraper with Firecrawl API key
        
        Args:
            api_key: Firecrawl API key. If None, will try to get from environment
        """
        self.api_key = api_key or os.getenv('FIRECRAWL_API_KEY')
        if not self.api_key:
            raise ValueError(
                "Firecrawl API key required. Set FIRECRAWL_API_KEY environment variable "
                "or pass api_key parameter"
            )
        
        self.firecrawl = Firecrawl(api_key=self.api_key)
        
        # Common crypto address patterns
        self.address_patterns = {
            'ethereum': r'0x[a-fA-F0-9]{40}',
            'bitcoin': r'[13][a-km-zA-HJ-NP-Z1-9]{25,34}',
            'bitcoin_legacy': r'[1][a-km-zA-HJ-NP-Z1-9]{25,34}',
            'bitcoin_segwit': r'[3][a-km-zA-HJ-NP-Z1-9]{25,34}',
            'bitcoin_bech32': r'bc1[a-z0-9]{39,59}',
            'solana': r'[1-9A-HJ-NP-Za-km-z]{32,44}',
            'cardano': r'addr1[a-z0-9]{98,103}',
            'polkadot': r'[1-9A-HJ-NP-Za-km-z]{47,48}',
            'cosmos': r'cosmos[a-z0-9]{38,45}',
            'transaction_hash': r'0x[a-fA-F0-9]{64}',
        }
        
        # Common abbreviated address patterns
        self.abbreviated_patterns = {
            'ethereum_short': r'0x[a-fA-F0-9]{4}\.\.\.[a-fA-F0-9]{4}',
            'ethereum_medium': r'0x[a-fA-F0-9]{6}\.\.\.[a-fA-F0-9]{6}',
            'bitcoin_short': r'[13][a-km-zA-HJ-NP-Z1-9]{4}\.\.\.[a-km-zA-HJ-NP-Z1-9]{4}',
            'generic_short': r'[a-zA-Z0-9]{4,8}\.\.\.[a-zA-Z0-9]{4,8}',
        }
        
        # Common crypto explorer domains
        self.explorer_domains = {
            'ethereum': ['etherscan.io', 'etherscan.com'],
            'polygon': ['polygonscan.com'],
            'bsc': ['bscscan.com'],
            'arbitrum': ['arbiscan.io'],
            'optimism': ['optimistic.etherscan.io'],
            'avalanche': ['snowtrace.io'],
            'fantom': ['ftmscan.com'],
            'bitcoin': ['blockchain.com', 'blockstream.info', 'mempool.space'],
            'solana': ['solscan.io', 'explorer.solana.com'],
        }

    def detect_network_from_url(self, url: str) -> str:
        """Detect the blockchain network from the URL"""
        url_lower = url.lower()
        
        for network, domains in self.explorer_domains.items():
            if any(domain in url_lower for domain in domains):
                return network
        
        # Fallback detection based on URL patterns
        if 'eth' in url_lower or 'ethereum' in url_lower:
            return 'ethereum'
        elif 'btc' in url_lower or 'bitcoin' in url_lower:
            return 'bitcoin'
        elif 'sol' in url_lower or 'solana' in url_lower:
            return 'solana'
        elif 'polygon' in url_lower or 'matic' in url_lower:
            return 'polygon'
        elif 'bsc' in url_lower or 'binance' in url_lower:
            return 'bsc'
        
        return 'unknown'

    def extract_addresses_from_text(self, text: str, network: str = 'unknown') -> List[CryptoAddress]:
        """
        Extract crypto addresses from text content
        
        Args:
            text: Text content to search
            network: Blockchain network for context
            
        Returns:
            List of found CryptoAddress objects
        """
        addresses = []
        
        # Search for full addresses
        for addr_type, pattern in self.address_patterns.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                address = match.group()
                confidence = 1.0 if addr_type == 'transaction_hash' else 0.9
                
                addresses.append(CryptoAddress(
                    address=address,
                    address_type=addr_type,
                    network=network,
                    abbreviated=address[:10] + '...' + address[-10:] if len(address) > 20 else address,
                    full_address=address,
                    confidence=confidence,
                    source_element='text_content'
                ))
        
        # Search for abbreviated addresses
        for abbrev_type, pattern in self.abbreviated_patterns.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                abbreviated = match.group()
                confidence = 0.7  # Lower confidence for abbreviated addresses
                
                addresses.append(CryptoAddress(
                    address=abbreviated,
                    address_type='abbreviated',
                    network=network,
                    abbreviated=abbreviated,
                    full_address='',  # Will be filled by hover extraction
                    confidence=confidence,
                    source_element='text_content'
                ))
        
        return addresses

    def scrape_with_hover_extraction(self, url: str, target_selectors: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Scrape a URL with special focus on extracting full addresses from hover elements
        
        Args:
            url: URL to scrape
            target_selectors: CSS selectors for elements that might contain addresses
            
        Returns:
            Dictionary containing scraped data and extracted addresses
        """
        network = self.detect_network_from_url(url)
        
        # Default selectors for common crypto explorer elements
        if target_selectors is None:
            target_selectors = [
                '[title*="0x"]',  # Elements with title containing hex addresses
                '[data-tooltip*="0x"]',  # Tooltip data attributes
                '[data-address]',  # Elements with address data
                '.address',  # Common address class
                '.hash',  # Common hash class
                '.tx-hash',  # Transaction hash class
                '[onmouseover*="0x"]',  # Mouse over events
                '[onmouseenter*="0x"]',  # Mouse enter events
            ]
        
        # Create actions to interact with hover elements
        actions = []
        
        # Add wait action to ensure page loads
        actions.append({'type': 'wait', 'milliseconds': 2000})
        
        # Add hover actions for target selectors
        for selector in target_selectors:
            actions.extend([
                {'type': 'hover', 'selector': selector},
                {'type': 'wait', 'milliseconds': 500},
                {'type': 'screenshot', 'fullPage': False},
                {'type': 'wait', 'milliseconds': 200}
            ])
        
        # Add scroll actions to reveal more content
        actions.extend([
            {'type': 'scroll', 'y': 500},
            {'type': 'wait', 'milliseconds': 1000},
            {'type': 'scroll', 'y': -500},
            {'type': 'wait', 'milliseconds': 500}
        ])
        
        try:
            # Scrape with actions
            result = self.firecrawl.scrape(
                url=url,
                formats=['markdown', 'html'],
                actions=actions,
                only_main_content=False,
                timeout=120000
            )
            
            if not result.get('success'):
                logger.error(f"Failed to scrape {url}: {result}")
                return {'success': False, 'error': result.get('error', 'Unknown error')}
            
            # Extract addresses from the content
            markdown_content = result['data'].get('markdown', '')
            html_content = result['data'].get('html', '')
            
            # Extract addresses from markdown
            addresses_from_md = self.extract_addresses_from_text(markdown_content, network)
            
            # Extract addresses from HTML
            addresses_from_html = self.extract_addresses_from_text(html_content, network)
            
            # Combine and deduplicate addresses
            all_addresses = self._deduplicate_addresses(addresses_from_md + addresses_from_html)
            
            # Try to extract transaction data
            transaction_data = self._extract_transaction_data(markdown_content, html_content, network)
            
            return {
                'success': True,
                'url': url,
                'network': network,
                'addresses': [asdict(addr) for addr in all_addresses],
                'transaction_data': asdict(transaction_data) if transaction_data else None,
                'markdown': markdown_content,
                'html': html_content,
                'actions_results': result['data'].get('actions', {}),
                'metadata': result['data'].get('metadata', {})
            }
            
        except Exception as e:
            logger.error(f"Error scraping {url}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'url': url
            }

    def _deduplicate_addresses(self, addresses: List[CryptoAddress]) -> List[CryptoAddress]:
        """Remove duplicate addresses based on full address or abbreviated form"""
        seen = set()
        unique_addresses = []
        
        for addr in addresses:
            # Use full address if available, otherwise use abbreviated
            key = addr.full_address if addr.full_address else addr.abbreviated
            
            if key not in seen:
                seen.add(key)
                unique_addresses.append(addr)
        
        return unique_addresses

    def _extract_transaction_data(self, markdown: str, html: str, network: str) -> Optional[TransactionData]:
        """Extract transaction data from scraped content"""
        # Combine both markdown and HTML for extraction
        combined_text = markdown + ' ' + html
        
        # Extract transaction hash
        tx_hash_match = re.search(self.address_patterns['transaction_hash'], combined_text)
        tx_hash = tx_hash_match.group() if tx_hash_match else None
        
        # Extract block number
        block_patterns = [
            r'block\s+#?(\d+)',
            r'block\s+(\d+)',
            r'#(\d+)',
            r'block\s+number:\s*(\d+)',
        ]
        
        block_number = None
        for pattern in block_patterns:
            match = re.search(pattern, combined_text, re.IGNORECASE)
            if match:
                try:
                    block_number = int(match.group(1))
                    break
                except ValueError:
                    continue
        
        # Extract amount and token
        amount_patterns = [
            r'(\d+(?:\.\d+)?)\s+([A-Z]{2,10})',  # 1.5 ETH, 1000 USDC
            r'([A-Z]{2,10})\s+(\d+(?:\.\d+)?)',  # ETH 1.5, USDC 1000
        ]
        
        amount = None
        token = None
        for pattern in amount_patterns:
            match = re.search(pattern, combined_text, re.IGNORECASE)
            if match:
                amount = match.group(1)
                token = match.group(2)
                break
        
        # Extract gas fee
        gas_patterns = [
            r'gas:\s*(\d+(?:\.\d+)?)\s*([A-Z]{2,10})',
            r'fee:\s*(\d+(?:\.\d+)?)\s*([A-Z]{2,10})',
            r'(\d+(?:\.\d+)?)\s*([A-Z]{2,10})\s*gas',
        ]
        
        gas_fee = None
        for pattern in gas_patterns:
            match = re.search(pattern, combined_text, re.IGNORECASE)
            if match:
                gas_fee = f"{match.group(1)} {match.group(2)}"
                break
        
        # Extract status
        status_patterns = [
            r'status:\s*(\w+)',
            r'(\w+)\s*status',
            r'confirmed',
            r'pending',
            r'failed',
        ]
        
        status = None
        for pattern in status_patterns:
            match = re.search(pattern, combined_text, re.IGNORECASE)
            if match:
                status = match.group(1) if match.groups() else match.group(0)
                break
        
        if tx_hash or block_number or amount:
            return TransactionData(
                tx_hash=tx_hash,
                block_number=block_number,
                amount=amount,
                token=token,
                gas_fee=gas_fee,
                status=status,
                network=network
            )
        
        return None

    def batch_scrape_transactions(self, urls: List[str], delay: float = 1.0) -> List[Dict[str, Any]]:
        """
        Scrape multiple transaction URLs with rate limiting
        
        Args:
            urls: List of URLs to scrape
            delay: Delay between requests in seconds
            
        Returns:
            List of scraping results
        """
        results = []
        
        for i, url in enumerate(urls):
            logger.info(f"Scraping {i+1}/{len(urls)}: {url}")
            
            result = self.scrape_with_hover_extraction(url)
            results.append(result)
            
            # Rate limiting
            if i < len(urls) - 1:  # Don't delay after the last request
                time.sleep(delay)
        
        return results

    def save_results(self, results: List[Dict[str, Any]], output_file: str):
        """
        Save scraping results to a file
        
        Args:
            results: List of scraping results
            output_file: Output file path
        """
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Add timestamp to results
        timestamped_results = {
            'scraped_at': datetime.now().isoformat(),
            'total_urls': len(results),
            'successful_scrapes': len([r for r in results if r.get('success')]),
            'failed_scrapes': len([r for r in results if not r.get('success')]),
            'results': results
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(timestamped_results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Results saved to {output_path}")

def main():
    """Example usage of the crypto transaction scraper"""
    
    # Check for API key
    api_key = os.getenv('FIRECRAWL_API_KEY')
    if not api_key:
        print("Please set FIRECRAWL_API_KEY environment variable")
        print("You can get an API key from: https://firecrawl.dev")
        return
    
    # Initialize scraper
    scraper = CryptoTransactionScraper(api_key=api_key)
    
    # Example URLs to scrape
    example_urls = [
        "https://etherscan.io/tx/0x0840bba848e991cdcfbf2b71b8e1cb94fb72d6343ad4bb182f7ee1c48612221d",
        "https://polygonscan.com/tx/0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
    ]
    
    print("Starting crypto transaction scraping...")
    print(f"Will scrape {len(example_urls)} URLs")
    
    # Scrape URLs
    results = scraper.batch_scrape_transactions(example_urls, delay=2.0)
    
    # Save results
    output_file = f"crypto_scraping_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    scraper.save_results(results, output_file)
    
    # Print summary
    successful = [r for r in results if r.get('success')]
    failed = [r for r in results if not r.get('success')]
    
    print(f"\nScraping completed!")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")
    
    if successful:
        total_addresses = sum(len(r.get('addresses', [])) for r in successful)
        print(f"Total addresses found: {total_addresses}")
    
    if failed:
        print("\nFailed URLs:")
        for result in failed:
            print(f"  - {result.get('url')}: {result.get('error')}")

if __name__ == "__main__":
    main()

