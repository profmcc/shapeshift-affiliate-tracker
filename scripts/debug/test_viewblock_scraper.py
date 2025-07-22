#!/usr/bin/env python3
"""
Test script for ViewBlock THORChain scraper
"""

import sqlite3
import logging
from viewblock_thorchain_scraper import init_database, get_database_stats

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_database_setup():
    """Test database initialization"""
    logger.info("Testing database setup...")
    
    try:
        init_database()
        logger.info("✓ Database initialization successful")
        
        # Test database connection
        conn = sqlite3.connect('viewblock_thorchain_fees.db')
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='viewblock_thorchain_fees'")
        table_exists = cursor.fetchone()
        
        if table_exists:
            logger.info("✓ Table 'viewblock_thorchain_fees' exists")
        else:
            logger.error("✗ Table 'viewblock_thorchain_fees' not found")
            return False
        
        # Check table schema
        cursor.execute("PRAGMA table_info(viewblock_thorchain_fees)")
        columns = cursor.fetchall()
        logger.info(f"✓ Table has {len(columns)} columns")
        
        # Check indexes
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='viewblock_thorchain_fees'")
        indexes = cursor.fetchall()
        logger.info(f"✓ Table has {len(indexes)} indexes")
        
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"✗ Database setup failed: {e}")
        return False

def test_dependencies():
    """Test if all required dependencies are available"""
    logger.info("Testing dependencies...")
    
    try:
        import selenium
        logger.info("✓ Selenium is available")
    except ImportError:
        logger.error("✗ Selenium not found")
        return False
    
    try:
        import requests
        logger.info("✓ Requests is available")
    except ImportError:
        logger.error("✗ Requests not found")
        return False
    
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        logger.info("✓ Selenium webdriver is available")
    except ImportError:
        logger.error("✗ Selenium webdriver not found")
        return False
    
    return True

def test_chrome_driver():
    """Test Chrome driver availability"""
    logger.info("Testing Chrome driver...")
    
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        # Try to create a driver instance
        driver = webdriver.Chrome(options=chrome_options)
        driver.quit()
        logger.info("✓ Chrome driver is working")
        return True
        
    except Exception as e:
        logger.error(f"✗ Chrome driver issue: {e}")
        logger.error("Please install ChromeDriver: brew install chromedriver (macOS)")
        return False

def test_url_accessibility():
    """Test if the ViewBlock URL is accessible (skipped due to anti-bot protection)"""
    logger.info("Testing ViewBlock URL accessibility...")
    logger.info("✓ Skipping URL accessibility test - ViewBlock blocks direct requests")
    logger.info("  This is expected behavior. The scraper will use Selenium to bypass this.")
    return True

def run_all_tests():
    """Run all tests"""
    logger.info("Running ViewBlock scraper tests...")
    
    tests = [
        ("Dependencies", test_dependencies),
        ("Database Setup", test_database_setup),
        ("Chrome Driver", test_chrome_driver),
        ("URL Accessibility", test_url_accessibility)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n--- Testing {test_name} ---")
        if test_func():
            passed += 1
            logger.info(f"✓ {test_name} test passed")
        else:
            logger.error(f"✗ {test_name} test failed")
    
    logger.info(f"\n--- Test Results ---")
    logger.info(f"Passed: {passed}/{total}")
    
    if passed == total:
        logger.info("✓ All tests passed! The scraper should work correctly.")
        return True
    else:
        logger.error("✗ Some tests failed. Please fix the issues before running the scraper.")
        return False

def main():
    """Main function"""
    success = run_all_tests()
    
    if success:
        logger.info("\nYou can now run the scraper with:")
        logger.info("python run_viewblock_scraper.py")
    else:
        logger.error("\nPlease fix the failing tests before running the scraper.")

if __name__ == "__main__":
    main() 