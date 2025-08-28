#!/usr/bin/env python3
"""
Command Line Interface for Crypto Transaction Scraper

Usage:
    python crypto_scraper_cli.py scrape <url> [options]
    python crypto_scraper_cli.py batch <file> [options]
    python crypto_scraper_cli.py extract <url> [options]
    python crypto_scraper_cli.py config [options]

Examples:
    python crypto_scraper_cli.py scrape https://etherscan.io/tx/0x123...
    python crypto_scraper_cli.py batch urls.txt --delay 3.0
    python crypto_scraper_cli.py extract https://etherscan.io/tx/0x123... --selectors .address,.hash
"""

import argparse
import sys
import json
import yaml
from pathlib import Path
from typing import List, Optional
import logging

from crypto_transaction_scraper import CryptoTransactionScraper

def setup_logging(level: str = 'INFO', log_file: Optional[str] = None):
    """Setup logging configuration"""
    log_level = getattr(logging, level.upper())
    
    # Configure logging
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_file) if log_file else logging.NullHandler()
        ]
    )

def load_config(config_file: str = 'config.yaml') -> dict:
    """Load configuration from YAML file"""
    config_path = Path(config_file)
    if not config_path.exists():
        print(f"Config file {config_file} not found. Using defaults.")
        return {}
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config or {}
    except Exception as e:
        print(f"Error loading config file: {e}")
        return {}

def scrape_single_url(args):
    """Scrape a single URL"""
    config = load_config(args.config)
    
    # Initialize scraper
    try:
        scraper = CryptoTransactionScraper()
    except ValueError as e:
        print(f"Error: {e}")
        print("Please set FIRECRAWL_API_KEY environment variable")
        return 1
    
    # Get target selectors
    target_selectors = args.selectors.split(',') if args.selectors else None
    
    print(f"Scraping: {args.url}")
    print("This may take a few moments...")
    
    # Scrape the URL
    result = scraper.scrape_with_hover_extraction(
        args.url, 
        target_selectors=target_selectors
    )
    
    if result.get('success'):
        print("\n✅ Scraping successful!")
        print(f"Network detected: {result.get('network', 'unknown')}")
        print(f"Addresses found: {len(result.get('addresses', []))}")
        
        if result.get('transaction_data'):
            tx_data = result['transaction_data']
            print(f"Transaction hash: {tx_data.get('tx_hash', 'Not found')}")
            print(f"Block number: {tx_data.get('block_number', 'Not found')}")
            print(f"Amount: {tx_data.get('amount', 'Not found')} {tx_data.get('token', '')}")
            print(f"Status: {tx_data.get('status', 'Not found')}")
        
        # Save results if requested
        if args.output:
            output_file = args.output
            scraper.save_results([result], output_file)
            print(f"\nResults saved to: {output_file}")
        
        # Show addresses if requested
        if args.show_addresses:
            addresses = result.get('addresses', [])
            if addresses:
                print("\n📋 Addresses found:")
                for i, addr in enumerate(addresses, 1):
                    print(f"  {i}. {addr.get('address', 'N/A')}")
                    print(f"     Type: {addr.get('address_type', 'N/A')}")
                    print(f"     Network: {addr.get('network', 'N/A')}")
                    print(f"     Confidence: {addr.get('confidence', 'N/A')}")
                    print()
        
        # Show raw data if requested
        if args.verbose:
            print("\n📄 Raw data:")
            print(json.dumps(result, indent=2))
    
    else:
        print(f"\n❌ Scraping failed: {result.get('error', 'Unknown error')}")
        return 1
    
    return 0

def scrape_batch_urls(args):
    """Scrape multiple URLs from a file"""
    config = load_config(args.config)
    
    # Check if input file exists
    input_file = Path(args.file)
    if not input_file.exists():
        print(f"Input file {args.file} not found.")
        return 1
    
    # Read URLs from file
    try:
        with open(input_file, 'r') as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    except Exception as e:
        print(f"Error reading file {args.file}: {e}")
        return 1
    
    if not urls:
        print(f"No valid URLs found in {args.file}")
        return 1
    
    print(f"Found {len(urls)} URLs to scrape")
    
    # Initialize scraper
    try:
        scraper = CryptoTransactionScraper()
    except ValueError as e:
        print(f"Error: {e}")
        print("Please set FIRECRAWL_API_KEY environment variable")
        return 1
    
    # Scrape URLs
    delay = args.delay or config.get('api', {}).get('rate_limit_delay', 2.0)
    results = scraper.batch_scrape_transactions(urls, delay=delay)
    
    # Print summary
    successful = [r for r in results if r.get('success')]
    failed = [r for r in results if not r.get('success')]
    
    print(f"\n📊 Scraping Summary:")
    print(f"  Total URLs: {len(urls)}")
    print(f"  Successful: {len(successful)}")
    print(f"  Failed: {len(failed)}")
    
    if successful:
        total_addresses = sum(len(r.get('addresses', [])) for r in successful)
        print(f"  Total addresses found: {total_addresses}")
    
    if failed:
        print(f"\n❌ Failed URLs:")
        for result in failed:
            print(f"  - {result.get('url')}: {result.get('error')}")
    
    # Save results
    if args.output:
        output_file = args.output
    else:
        output_file = f"batch_scraping_results_{len(urls)}_urls.json"
    
    scraper.save_results(results, output_file)
    print(f"\n💾 Results saved to: {output_file}")
    
    return 0

def extract_addresses_only(args):
    """Extract only addresses from a URL without full scraping"""
    config = load_config(args.config)
    
    # Initialize scraper
    try:
        scraper = CryptoTransactionScraper()
    except ValueError as e:
        print(f"Error: {e}")
        print("Please set FIRECRAWL_API_KEY environment variable")
        return 1
    
    print(f"Extracting addresses from: {args.url}")
    
    # Use a simpler scraping approach for just address extraction
    try:
        result = scraper.firecrawl.scrape(
            url=args.url,
            formats=['markdown'],
            only_main_content=True,
            timeout=60000
        )
        
        if result.get('success'):
            markdown_content = result['data'].get('markdown', '')
            network = scraper.detect_network_from_url(args.url)
            
            addresses = scraper.extract_addresses_from_text(markdown_content, network)
            
            print(f"\n🔍 Address extraction completed!")
            print(f"Network: {network}")
            print(f"Addresses found: {len(addresses)}")
            
            if addresses:
                print("\n📋 Extracted addresses:")
                for i, addr in enumerate(addresses, 1):
                    print(f"  {i}. {addr.address}")
                    print(f"     Type: {addr.address_type}")
                    print(f"     Abbreviated: {addr.abbreviated}")
                    print(f"     Confidence: {addr.confidence}")
                    print()
            
            # Save if requested
            if args.output:
                output_data = {
                    'url': args.url,
                    'network': network,
                    'addresses': [scraper._deduplicate_addresses(addresses)],
                    'extracted_at': scraper._extract_transaction_data.__name__
                }
                
                with open(args.output, 'w') as f:
                    json.dump(output_data, f, indent=2)
                print(f"Results saved to: {args.output}")
        
        else:
            print(f"❌ Extraction failed: {result.get('error', 'Unknown error')}")
            return 1
    
    except Exception as e:
        print(f"❌ Error during extraction: {e}")
        return 1
    
    return 0

def show_config_info(args):
    """Show configuration information"""
    config = load_config(args.config)
    
    if not config:
        print("No configuration file found or loaded.")
        return 0
    
    print("📋 Configuration Information:")
    print(f"Config file: {args.config}")
    print()
    
    # API Configuration
    if 'api' in config:
        print("🔑 API Configuration:")
        api_config = config['api']
        print(f"  Timeout: {api_config.get('timeout', 'Not set')}ms")
        print(f"  Rate limit delay: {api_config.get('rate_limit_delay', 'Not set')}s")
        print()
    
    # Scraping Configuration
    if 'scraping' in config:
        print("🕷️  Scraping Configuration:")
        scraping_config = config['scraping']
        print(f"  Target selectors: {len(scraping_config.get('target_selectors', []))}")
        print(f"  Page load wait: {scraping_config.get('wait_times', {}).get('page_load', 'Not set')}ms")
        print(f"  Hover delay: {scraping_config.get('wait_times', {}).get('hover_delay', 'Not set')}ms")
        print()
    
    # Networks
    if 'networks' in config:
        print("🌐 Supported Networks:")
        for network, details in config['networks'].items():
            domains = details.get('domains', [])
            print(f"  {network.capitalize()}: {', '.join(domains)}")
        print()
    
    # Example URLs
    if 'example_urls' in config:
        print("🔗 Example URLs:")
        for i, url in enumerate(config['example_urls'], 1):
            print(f"  {i}. {url}")
    
    return 0

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Crypto Transaction Web Scraper using Firecrawl API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scrape a single transaction URL
  python crypto_scraper_cli.py scrape https://etherscan.io/tx/0x123...
  
  # Scrape multiple URLs from a file
  python crypto_scraper_cli.py batch urls.txt --delay 3.0
  
  # Extract only addresses from a URL
  python crypto_scraper_cli.py extract https://etherscan.io/tx/0x123...
  
  # Show configuration information
  python crypto_scraper_cli.py config
        """
    )
    
    # Global options
    parser.add_argument(
        '--config', '-c',
        default='config.yaml',
        help='Configuration file path (default: config.yaml)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output'
    )
    parser.add_argument(
        '--output', '-o',
        help='Output file path'
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Scrape command
    scrape_parser = subparsers.add_parser('scrape', help='Scrape a single URL')
    scrape_parser.add_argument('url', help='URL to scrape')
    scrape_parser.add_argument(
        '--selectors', '-s',
        help='Comma-separated CSS selectors for target elements'
    )
    scrape_parser.add_argument(
        '--show-addresses', '-a',
        action='store_true',
        help='Show extracted addresses'
    )
    
    # Batch command
    batch_parser = subparsers.add_parser('batch', help='Scrape multiple URLs from a file')
    batch_parser.add_argument('file', help='File containing URLs (one per line)')
    batch_parser.add_argument(
        '--delay', '-d',
        type=float,
        help='Delay between requests in seconds'
    )
    
    # Extract command
    extract_parser = subparsers.add_parser('extract', help='Extract only addresses from a URL')
    extract_parser.add_argument('url', help='URL to extract addresses from')
    
    # Config command
    config_parser = subparsers.add_parser('config', help='Show configuration information')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Check if command was provided
    if not args.command:
        parser.print_help()
        return 1
    
    # Setup logging
    log_level = 'DEBUG' if args.verbose else 'INFO'
    setup_logging(level=log_level)
    
    # Execute command
    try:
        if args.command == 'scrape':
            return scrape_single_url(args)
        elif args.command == 'batch':
            return scrape_batch_urls(args)
        elif args.command == 'extract':
            return extract_addresses_only(args)
        elif args.command == 'config':
            return show_config_info(args)
        else:
            print(f"Unknown command: {args.command}")
            return 1
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())

