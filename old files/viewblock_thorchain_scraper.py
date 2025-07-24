#!/usr/bin/env python3
"""
ViewBlock THORChain Affiliate Fee Scraper
Scrapes https://viewblock.io/thorchain/txs?affiliate=ss and captures full data from hover tooltips
"""

import requests
import sqlite3
import time
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import re

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
VIEWBLOCK_URL = 'https://viewblock.io/thorchain/txs?affiliate=ss'
DB_PATH = 'viewblock_thorchain_fees.db'
CHROME_DRIVER_PATH = None  # Will use system Chrome driver

def init_database():
    """Initialize the ViewBlock THORChain affiliate fees database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS viewblock_thorchain_fees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tx_hash TEXT UNIQUE,
            block_height INTEGER,
            timestamp TEXT,
            from_address TEXT,
            to_address TEXT,
            affiliate_address TEXT,
            from_asset TEXT,
            to_asset TEXT,
            from_amount REAL,
            to_amount REAL,
            from_amount_usd REAL,
            to_amount_usd REAL,
            affiliate_fee_amount REAL,
            affiliate_fee_basis_points INTEGER,
            swap_slip REAL,
            liquidity_fee REAL,
            gas_fee REAL,
            gas_asset TEXT,
            status TEXT,
            memo TEXT,
            raw_data TEXT,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_viewblock_tx_hash ON viewblock_thorchain_fees(tx_hash)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_viewblock_timestamp ON viewblock_thorchain_fees(timestamp)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_viewblock_affiliate ON viewblock_thorchain_fees(affiliate_address)
    ''')
    
    conn.commit()
    conn.close()
    logger.info("ViewBlock THORChain affiliate fees database initialized")

def setup_chrome_driver():
    """Setup Chrome driver with appropriate options for scraping"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # Run in background
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        driver.set_page_load_timeout(30)
        return driver
    except Exception as e:
        logger.error(f"Failed to setup Chrome driver: {e}")
        return None

def extract_full_text_from_tooltip(driver, element) -> str:
    """Extract full text from hover tooltip"""
    try:
        # Hover over the element to show tooltip
        driver.execute_script("arguments[0].dispatchEvent(new MouseEvent('mouseover', {bubbles: true}));", element)
        time.sleep(0.5)  # Wait for tooltip to appear
        
        # Look for tooltip elements
        tooltips = driver.find_elements(By.CSS_SELECTOR, '[class*="tooltip"], [class*="Tooltip"], [class*="popover"], [class*="Popover"]')
        
        for tooltip in tooltips:
            if tooltip.is_displayed():
                return tooltip.text.strip()
        
        # If no tooltip found, return the element's title attribute
        title = element.get_attribute('title')
        if title:
            return title.strip()
        
        # Fallback to element text
        return element.text.strip()
        
    except Exception as e:
        logger.warning(f"Error extracting tooltip: {e}")
        return element.text.strip()

def parse_transaction_row(driver, row_element) -> Optional[Dict]:
    """Parse a single transaction row from the ViewBlock table"""
    try:
        # Find all cells in the row
        cells = row_element.find_elements(By.TAG_NAME, "td")
        if len(cells) < 6:  # Minimum expected columns
            return None
        
        # Extract data from each column with tooltip handling
        tx_data = {}
        
        # Column 1: Transaction Hash (with tooltip for full hash)
        tx_hash_cell = cells[0]
        tx_hash_full = extract_full_text_from_tooltip(driver, tx_hash_cell)
        tx_data['tx_hash'] = tx_hash_full
        
        # Column 2: Block Height (with tooltip for full number)
        block_cell = cells[1]
        block_full = extract_full_text_from_tooltip(driver, block_cell)
        try:
            tx_data['block_height'] = int(block_full.replace(',', ''))
        except (ValueError, AttributeError):
            tx_data['block_height'] = 0
        
        # Column 3: Timestamp (with tooltip for full timestamp)
        timestamp_cell = cells[2]
        timestamp_full = extract_full_text_from_tooltip(driver, timestamp_cell)
        tx_data['timestamp'] = timestamp_full
        
        # Column 4: From Address (with tooltip for full address)
        from_cell = cells[3]
        from_full = extract_full_text_from_tooltip(driver, from_cell)
        tx_data['from_address'] = from_full
        
        # Column 5: To Address (with tooltip for full address)
        to_cell = cells[4]
        to_full = extract_full_text_from_tooltip(driver, to_cell)
        tx_data['to_address'] = to_full
        
        # Column 6: Amount (with tooltip for full amount)
        amount_cell = cells[5]
        amount_full = extract_full_text_from_tooltip(driver, amount_cell)
        tx_data['amount'] = amount_full
        
        # Try to extract additional data from the row
        try:
            # Look for affiliate information in the row
            affiliate_elements = row_element.find_elements(By.XPATH, ".//*[contains(text(), 'ss') or contains(text(), 'affiliate')]")
            if affiliate_elements:
                tx_data['affiliate_address'] = 'ss'
            
            # Extract asset information from amount field
            amount_text = amount_full
            if '→' in amount_text:
                parts = amount_text.split('→')
                if len(parts) >= 2:
                    from_part = parts[0].strip()
                    to_part = parts[1].strip()
                    
                    # Parse from asset and amount
                    from_match = re.search(r'([\d,]+\.?\d*)\s*([A-Z]+)', from_part)
                    if from_match:
                        tx_data['from_amount'] = float(from_match.group(1).replace(',', ''))
                        tx_data['from_asset'] = from_match.group(2)
                    
                    # Parse to asset and amount
                    to_match = re.search(r'([\d,]+\.?\d*)\s*([A-Z]+)', to_part)
                    if to_match:
                        tx_data['to_amount'] = float(to_match.group(1).replace(',', ''))
                        tx_data['to_asset'] = to_match.group(2)
            
        except Exception as e:
            logger.warning(f"Error parsing additional data: {e}")
        
        # Store raw data for debugging
        tx_data['raw_data'] = json.dumps({
            'row_text': row_element.text,
            'cells_count': len(cells)
        })
        
        return tx_data
        
    except Exception as e:
        logger.error(f"Error parsing transaction row: {e}")
        return None

def scrape_viewblock_page(driver, page_num: int = 1) -> List[Dict]:
    """Scrape a single page of ViewBlock THORChain transactions"""
    transactions = []
    
    try:
        # Navigate to the page
        page_url = f"{VIEWBLOCK_URL}&page={page_num}" if page_num > 1 else VIEWBLOCK_URL
        logger.info(f"Scraping page {page_num}: {page_url}")
        
        driver.get(page_url)
        
        # Wait for the table to load
        wait = WebDriverWait(driver, 20)
        table = wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
        
        # Wait a bit more for data to fully load
        time.sleep(3)
        
        # Find all transaction rows
        rows = table.find_elements(By.TAG_NAME, "tr")
        logger.info(f"Found {len(rows)} rows on page {page_num}")
        
        # Skip header row
        for i, row in enumerate(rows[1:], 1):
            try:
                tx_data = parse_transaction_row(driver, row)
                if tx_data:
                    transactions.append(tx_data)
                    logger.debug(f"Parsed transaction {i}: {tx_data.get('tx_hash', 'unknown')}")
                
                # Add small delay between rows to avoid overwhelming the page
                time.sleep(0.1)
                
            except Exception as e:
                logger.warning(f"Error processing row {i}: {e}")
                continue
        
        logger.info(f"Successfully scraped {len(transactions)} transactions from page {page_num}")
        return transactions
        
    except TimeoutException:
        logger.error(f"Timeout waiting for page {page_num} to load")
        return []
    except Exception as e:
        logger.error(f"Error scraping page {page_num}: {e}")
        return []

def store_transactions(transactions: List[Dict]):
    """Store scraped transactions in the database"""
    if not transactions:
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    stored_count = 0
    for tx in transactions:
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO viewblock_thorchain_fees (
                    tx_hash, block_height, timestamp, from_address, to_address,
                    affiliate_address, from_asset, to_asset, from_amount, to_amount,
                    from_amount_usd, to_amount_usd, affiliate_fee_amount,
                    affiliate_fee_basis_points, swap_slip, liquidity_fee,
                    gas_fee, gas_asset, status, memo, raw_data
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                tx.get('tx_hash'),
                tx.get('block_height'),
                tx.get('timestamp'),
                tx.get('from_address'),
                tx.get('to_address'),
                tx.get('affiliate_address'),
                tx.get('from_asset'),
                tx.get('to_asset'),
                tx.get('from_amount'),
                tx.get('to_amount'),
                tx.get('from_amount_usd'),
                tx.get('to_amount_usd'),
                tx.get('affiliate_fee_amount'),
                tx.get('affiliate_fee_basis_points'),
                tx.get('swap_slip'),
                tx.get('liquidity_fee'),
                tx.get('gas_fee'),
                tx.get('gas_asset'),
                tx.get('status'),
                tx.get('memo'),
                tx.get('raw_data')
            ))
            stored_count += 1
            
        except Exception as e:
            logger.error(f"Error storing transaction {tx.get('tx_hash', 'unknown')}: {e}")
            continue
    
    conn.commit()
    conn.close()
    logger.info(f"Stored {stored_count} new transactions in database")

def get_database_stats():
    """Get statistics about the scraped data"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM viewblock_thorchain_fees")
    total_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM viewblock_thorchain_fees WHERE timestamp IS NOT NULL")
    time_range = cursor.fetchone()
    
    cursor.execute("SELECT COUNT(DISTINCT from_address) FROM viewblock_thorchain_fees")
    unique_addresses = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT from_asset) FROM viewblock_thorchain_fees WHERE from_asset IS NOT NULL")
    unique_assets = cursor.fetchone()[0]
    
    conn.close()
    
    logger.info(f"Database Statistics:")
    logger.info(f"  Total transactions: {total_count}")
    logger.info(f"  Time range: {time_range[0]} to {time_range[1]}")
    logger.info(f"  Unique addresses: {unique_addresses}")
    logger.info(f"  Unique assets: {unique_assets}")

def scrape_viewblock_comprehensive(max_pages: int = 10):
    """Comprehensive scraping of ViewBlock THORChain affiliate data"""
    logger.info("Starting comprehensive ViewBlock THORChain affiliate fee scraper")
    logger.info(f"This will scrape up to {max_pages} pages of data")
    
    # Initialize database
    init_database()
    
    # Setup Chrome driver
    driver = setup_chrome_driver()
    if not driver:
        logger.error("Failed to setup Chrome driver. Exiting.")
        return
    
    try:
        total_transactions = 0
        
        for page_num in range(1, max_pages + 1):
            logger.info(f"Processing page {page_num}/{max_pages}")
            
            transactions = scrape_viewblock_page(driver, page_num)
            
            if not transactions:
                logger.info(f"No transactions found on page {page_num}. Stopping.")
                break
            
            # Store transactions
            store_transactions(transactions)
            total_transactions += len(transactions)
            
            # Add delay between pages to be respectful
            time.sleep(2)
        
        logger.info(f"Scraping completed! Total transactions processed: {total_transactions}")
        
        # Get database statistics
        get_database_stats()
        
    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
    except Exception as e:
        logger.error(f"Error during scraping: {e}")
    finally:
        driver.quit()
        logger.info("Chrome driver closed")

def main():
    """Main function to run the scraper"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Scrape ViewBlock THORChain affiliate data')
    parser.add_argument('--pages', type=int, default=10, help='Maximum number of pages to scrape')
    parser.add_argument('--headless', action='store_true', help='Run in headless mode (default)')
    
    args = parser.parse_args()
    
    scrape_viewblock_comprehensive(max_pages=args.pages)

if __name__ == "__main__":
    main() 