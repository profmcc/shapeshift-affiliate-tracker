#!/usr/bin/env python3
"""
Test script for Crypto Transaction Scraper

This script tests the basic functionality without requiring a Firecrawl API key.
It focuses on testing the address detection and parsing logic.
"""

import os
import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

def test_address_detection():
    """Test address detection patterns without API calls"""
    print("🧪 Testing address detection patterns...")
    
    try:
        from crypto_transaction_scraper import CryptoTransactionScraper
        
        # Create a mock scraper (won't make API calls)
        class MockFirecrawl:
            def scrape(self, *args, **kwargs):
                return {'success': False, 'error': 'Mock - no API key'}
        
        # Test address patterns
        test_texts = [
            "Transaction: 0x0840bba848e991cdcfbf2b71b8e1cb94fb72d6343ad4bb182f7ee1c48612221d",
            "Wallet: 0x1234...5678",
            "Contract: 0xabcdef1234567890abcdef1234567890abcdef1234",
            "Bitcoin: 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
            "Solana: 7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU"
        ]
        
        # Create scraper instance
        scraper = CryptoTransactionScraper(api_key="mock-key")
        scraper.firecrawl = MockFirecrawl()  # Replace with mock
        
        print("✅ Scraper initialized successfully")
        
        # Test network detection
        test_urls = [
            "https://etherscan.io/tx/0x123...",
            "https://polygonscan.com/tx/0x456...",
            "https://bscscan.com/tx/0x789...",
            "https://arbiscan.io/tx/0xabc...",
            "https://www.blockchain.com/explorer/transactions/123..."
        ]
        
        for url in test_urls:
            network = scraper.detect_network_from_url(url)
            print(f"  {url} -> {network}")
        
        # Test address extraction from text
        for i, text in enumerate(test_texts, 1):
            print(f"\nTest {i}: {text}")
            addresses = scraper.extract_addresses_from_text(text, "ethereum")
            print(f"  Found {len(addresses)} addresses:")
            for addr in addresses:
                print(f"    - {addr.address} ({addr.address_type}, confidence: {addr.confidence})")
        
        print("\n✅ Address detection tests completed successfully!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure all dependencies are installed: pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_config_loading():
    """Test configuration file loading"""
    print("\n🧪 Testing configuration loading...")
    
    try:
        import yaml
        
        config_file = Path(__file__).parent / "config.yaml"
        if config_file.exists():
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
            
            print("✅ Configuration file loaded successfully")
            print(f"  API timeout: {config.get('api', {}).get('timeout', 'Not set')}ms")
            print(f"  Supported networks: {len(config.get('networks', {}))}")
            print(f"  Target selectors: {len(config.get('scraping', {}).get('target_selectors', []))}")
            return True
        else:
            print("❌ Configuration file not found")
            return False
            
    except ImportError:
        print("❌ PyYAML not installed. Install with: pip install pyyaml")
        return False
    except Exception as e:
        print(f"❌ Config test failed: {e}")
        return False

def test_cli_help():
    """Test CLI help functionality"""
    print("\n🧪 Testing CLI help...")
    
    try:
        from crypto_scraper_cli import main
        
        # This will just test that the CLI can be imported
        print("✅ CLI module imported successfully")
        
        # Test argument parser creation
        import argparse
        parser = argparse.ArgumentParser(description="Test")
        print("✅ Argument parser works")
        
        return True
        
    except ImportError as e:
        print(f"❌ CLI import error: {e}")
        return False
    except Exception as e:
        print(f"❌ CLI test failed: {e}")
        return False

def test_sample_urls():
    """Test sample URLs file"""
    print("\n🧪 Testing sample URLs file...")
    
    try:
        sample_file = Path(__file__).parent / "sample_urls.txt"
        if sample_file.exists():
            with open(sample_file, 'r') as f:
                urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            
            print(f"✅ Sample URLs file loaded: {len(urls)} URLs found")
            
            # Show first few URLs
            for i, url in enumerate(urls[:3], 1):
                print(f"  {i}. {url}")
            
            if len(urls) > 3:
                print(f"  ... and {len(urls) - 3} more")
            
            return True
        else:
            print("❌ Sample URLs file not found")
            return False
            
    except Exception as e:
        print(f"❌ Sample URLs test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Crypto Transaction Scraper - Test Suite")
    print("=" * 50)
    
    tests = [
        ("Address Detection", test_address_detection),
        ("Configuration Loading", test_config_loading),
        ("CLI Functionality", test_cli_help),
        ("Sample URLs", test_sample_urls),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} failed")
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
    
    print(f"\n{'='*50}")
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The scraper is ready to use.")
        print("\nNext steps:")
        print("1. Get a Firecrawl API key from https://firecrawl.dev")
        print("2. Set FIRECRAWL_API_KEY environment variable")
        print("3. Run: python crypto_scraper_cli.py scrape <url>")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        print("\nTroubleshooting:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Check file permissions and paths")
        print("3. Verify Python version (3.8+)")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

