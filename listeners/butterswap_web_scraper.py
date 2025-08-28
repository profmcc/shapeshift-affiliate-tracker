#!/usr/bin/env python3
"""
ButterSwap Web Scraper
Scrapes transaction data from the Butterswap explorer interface.
Handles copy-paste operations for full addresses and transaction details.
"""

import os
import sqlite3
import time
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import pyperclip
import requests

# Add shared directory to path
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from shared.block_tracker import BlockTracker

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ButterSwapWebScraper:
    def __init__(self, db_path: str = "databases/butterswap_web_transactions.db"):
        self.db_path = db_path
        self.explorer_url = "https://explorer.butterswap.io/en"
        self.init_database()

        # Initialize block tracker
        self.block_tracker = BlockTracker()

        # ShapeShift affiliate addresses by chain
        self.shapeshift_affiliates = {
            "ethereum": "0x90A48D5CF7343B08dA12E067680B4C6dbfE551Be",
            "polygon": "0xB5F944600785724e31Edb90F9DFa16dBF01Af000",
            "optimism": "0x6268d07327f4fb7380732dc6d63d95F88c0E083b",
            "arbitrum": "0x38276553F8fbf2A027D901F8be45f00373d8Dd48",
            "base": "0x9c9aA90363630d4ab1D9dbF416cc3BBC8d3Ed502",
            "avalanche": "0x74d63F31C2335b5b3BA7ad2812357672b2624cEd",
            "bsc": "0x8b92b1698b57bEDF2142297e9397875ADBb2297E",
        }

        # Supported chains for Butterswap
        self.supported_chains = [
            "ethereum",
            "polygon",
            "optimism",
            "arbitrum",
            "base",
            "avalanche",
            "bsc",
        ]

    def init_database(self):
        """Initialize the database with Butterswap web transactions table"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS butterswap_web_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chain TEXT NOT NULL,
                tx_hash TEXT NOT NULL,
                block_number INTEGER,
                block_timestamp INTEGER,
                from_address TEXT,
                to_address TEXT,
                token_in TEXT,
                token_out TEXT,
                amount_in TEXT,
                amount_out TEXT,
                fee_amount TEXT,
                fee_token TEXT,
                affiliate_address TEXT,
                affiliate_fee_usd REAL,
                volume_usd REAL,
                token_in_name TEXT,
                token_out_name TEXT,
                status TEXT,
                explorer_url TEXT,
                scraped_at INTEGER DEFAULT (strftime('%s', 'now')),
                UNIQUE(tx_hash, chain)
            )
        """
        )

        # Create index for faster lookups
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_tx_hash ON butterswap_web_transactions(tx_hash)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_chain ON butterswap_web_transactions(chain)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_affiliate ON butterswap_web_transactions(affiliate_address)"
        )

        conn.commit()
        conn.close()
        logger.info(f"✅ ButterSwap web database initialized: {self.db_path}")

    def setup_webdriver(self, headless: bool = False) -> webdriver.Chrome:
        """Setup Chrome webdriver with appropriate options"""
        chrome_options = Options()

        if headless:
            chrome_options.add_argument("--headless")

        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument(
            "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        # Disable images and CSS for faster loading
        prefs = {
            "profile.managed_default_content_settings.images": 2,
            "profile.default_content_setting_values.notifications": 2,
        }
        chrome_options.add_experimental_option("prefs", prefs)

        try:
            driver = webdriver.Chrome(options=chrome_options)
            driver.set_page_load_timeout(30)
            return driver
        except Exception as e:
            logger.error(f"Failed to setup Chrome webdriver: {e}")
            raise

    def navigate_to_explorer(
        self, driver: webdriver.Chrome, chain: str = "ethereum"
    ) -> bool:
        """Navigate to the Butterswap explorer for a specific chain"""
        try:
            # Navigate to main explorer
            driver.get(self.explorer_url)
            time.sleep(3)

            # Try to find chain selector
            try:
                chain_selector = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located(
                        (
                            By.CSS_SELECTOR,
                            "[data-testid='chain-selector'], .chain-selector, select",
                        )
                    )
                )

                # Select the desired chain
                if chain_selector.tag_name == "select":
                    from selenium.webdriver.support.ui import Select

                    select = Select(chain_selector)
                    select.select_by_visible_text(chain.title())
                else:
                    # Click on chain selector and choose chain
                    chain_selector.click()
                    time.sleep(1)

                    # Look for chain option
                    chain_option = driver.find_element(
                        By.XPATH,
                        f"//*[contains(text(), '{chain.title()}') or contains(text(), '{chain.upper()}')]",
                    )
                    chain_option.click()

                time.sleep(3)
                logger.info(f"✅ Successfully navigated to {chain} chain")
                return True

            except TimeoutException:
                logger.warning(
                    f"Chain selector not found, assuming default chain: {chain}"
                )
                return True

        except Exception as e:
            logger.error(f"Error navigating to explorer: {e}")
            return False

    def extract_transaction_data(
        self, driver: webdriver.Chrome, tx_element
    ) -> Optional[Dict]:
        """Extract transaction data from a transaction element"""
        try:
            # Extract basic transaction info
            tx_data = {}

            # Try to find transaction hash
            try:
                hash_element = tx_element.find_element(
                    By.CSS_SELECTOR, "[data-testid='tx-hash'], .tx-hash, .hash"
                )
                tx_data["tx_hash"] = hash_element.text.strip()
            except NoSuchElementException:
                # Look for any element that looks like a hash
                hash_pattern = re.compile(r"0x[a-fA-F0-9]{64}")
                hash_text = tx_element.text
                hash_match = hash_pattern.search(hash_text)
                if hash_match:
                    tx_data["tx_hash"] = hash_match.group()
                else:
                    return None

            # Extract from/to addresses
            try:
                from_element = tx_element.find_element(
                    By.CSS_SELECTOR,
                    "[data-testid='from-address'], .from-address, .sender",
                )
                tx_data["from_address"] = from_element.text.strip()
            except NoSuchElementException:
                tx_data["from_address"] = None

            try:
                to_element = tx_element.find_element(
                    By.CSS_SELECTOR,
                    "[data-testid='to-address'], .to-address, .recipient",
                )
                tx_data["to_address"] = to_element.text.strip()
            except NoSuchElementException:
                tx_data["to_address"] = None

            # Extract token information
            try:
                token_in_element = tx_element.find_element(
                    By.CSS_SELECTOR, "[data-testid='token-in'], .token-in, .input-token"
                )
                tx_data["token_in"] = token_in_element.text.strip()
            except NoSuchElementException:
                tx_data["token_in"] = None

            try:
                token_out_element = tx_element.find_element(
                    By.CSS_SELECTOR,
                    "[data-testid='token-out'], .token-out, .output-token",
                )
                tx_data["token_out"] = token_out_element.text.strip()
            except NoSuchElementException:
                tx_data["token_out"] = None

            # Extract amounts
            try:
                amount_in_element = tx_element.find_element(
                    By.CSS_SELECTOR,
                    "[data-testid='amount-in'], .amount-in, .input-amount",
                )
                tx_data["amount_in"] = amount_in_element.text.strip()
            except NoSuchElementException:
                tx_data["amount_in"] = None

            try:
                amount_out_element = tx_element.find_element(
                    By.CSS_SELECTOR,
                    "[data-testid='amount-out'], .amount-out, .output-amount",
                )
                tx_data["amount_out"] = amount_out_element.text.strip()
            except NoSuchElementException:
                tx_data["amount_out"] = None

            # Extract status
            try:
                status_element = tx_element.find_element(
                    By.CSS_SELECTOR, "[data-testid='status'], .status, .tx-status"
                )
                tx_data["status"] = status_element.text.strip()
            except NoSuchElementException:
                tx_data["status"] = "unknown"

            # Extract timestamp if available
            try:
                timestamp_element = tx_element.find_element(
                    By.CSS_SELECTOR, "[data-testid='timestamp'], .timestamp, .time"
                )
                timestamp_text = timestamp_element.text.strip()
                tx_data["block_timestamp"] = self.parse_timestamp(timestamp_text)
            except NoSuchElementException:
                tx_data["block_timestamp"] = int(time.time())

            return tx_data

        except Exception as e:
            logger.error(f"Error extracting transaction data: {e}")
            return None

    def parse_timestamp(self, timestamp_text: str) -> int:
        """Parse timestamp text to Unix timestamp"""
        try:
            # Handle relative timestamps like "2 hours ago", "5 minutes ago"
            if "ago" in timestamp_text.lower():
                # Simple relative time parsing
                if "hour" in timestamp_text.lower():
                    hours = int(re.search(r"(\d+)", timestamp_text).group(1))
                    return int(time.time()) - (hours * 3600)
                elif "minute" in timestamp_text.lower():
                    minutes = int(re.search(r"(\d+)", timestamp_text).group(1))
                    return int(time.time()) - (minutes * 60)
                elif "second" in timestamp_text.lower():
                    seconds = int(re.search(r"(\d+)", timestamp_text).group(1))
                    return int(time.time()) - seconds
                else:
                    return int(time.time())
            else:
                # Try to parse absolute timestamp
                try:
                    dt = datetime.strptime(timestamp_text, "%Y-%m-%d %H:%M:%S")
                    return int(dt.timestamp())
                except ValueError:
                    try:
                        dt = datetime.strptime(timestamp_text, "%m/%d/%Y %H:%M")
                        return int(dt.timestamp())
                    except ValueError:
                        return int(time.time())
        except Exception:
            return int(time.time())

    def copy_address_to_clipboard(
        self, driver: webdriver.Chrome, address_element
    ) -> str:
        """Copy address to clipboard and return the copied text"""
        try:
            # Click on the address element to select it
            address_element.click()
            time.sleep(0.5)

            # Use keyboard shortcuts to copy
            from selenium.webdriver.common.keys import Keys
            from selenium.webdriver.common.action_chains import ActionChains

            actions = ActionChains(driver)
            actions.key_down(Keys.COMMAND).send_keys("c").key_up(Keys.COMMAND).perform()
            time.sleep(0.5)

            # Get the copied text from clipboard
            copied_text = pyperclip.paste()

            # Clean up the copied text
            if copied_text:
                # Remove any extra whitespace or newlines
                copied_text = copied_text.strip()
                # Validate it looks like an address
                if re.match(r"^0x[a-fA-F0-9]{40}$", copied_text):
                    return copied_text

            # Fallback: try to get text directly
            return address_element.text.strip()

        except Exception as e:
            logger.error(f"Error copying address to clipboard: {e}")
            # Fallback: return text directly
            return address_element.text.strip()

    def scrape_transactions(
        self, driver: webdriver.Chrome, max_transactions: int = 100
    ) -> List[Dict]:
        """Scrape transactions from the current page"""
        transactions = []

        try:
            # Wait for transactions to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (
                        By.CSS_SELECTOR,
                        "[data-testid='transaction'], .transaction, .tx-item, tr",
                    )
                )
            )

            # Find transaction elements
            tx_elements = driver.find_elements(
                By.CSS_SELECTOR,
                "[data-testid='transaction'], .transaction, .tx-item, tr",
            )

            logger.info(f"Found {len(tx_elements)} transaction elements")

            for i, tx_element in enumerate(tx_elements[:max_transactions]):
                try:
                    # Extract basic transaction data
                    tx_data = self.extract_transaction_data(driver, tx_element)
                    if not tx_data:
                        continue

                    # Try to get full addresses by copying to clipboard
                    if tx_data.get("from_address"):
                        try:
                            from_element = tx_element.find_element(
                                By.CSS_SELECTOR,
                                "[data-testid='from-address'], .from-address, .sender",
                            )
                            full_from_address = self.copy_address_to_clipboard(
                                driver, from_element
                            )
                            if (
                                full_from_address and len(full_from_address) == 42
                            ):  # 0x + 40 hex chars
                                tx_data["from_address"] = full_from_address
                        except Exception as e:
                            logger.debug(f"Could not copy from address: {e}")

                    if tx_data.get("to_address"):
                        try:
                            to_element = tx_element.find_element(
                                By.CSS_SELECTOR,
                                "[data-testid='to-address'], .to-address, .recipient",
                            )
                            full_to_address = self.copy_address_to_clipboard(
                                driver, to_element
                            )
                            if full_to_address and len(full_to_address) == 42:
                                tx_data["to_address"] = full_to_address
                        except Exception as e:
                            logger.debug(f"Could not copy to address: {e}")

                    # Check if this transaction involves ShapeShift affiliate
                    if self.is_shapeshift_affiliate_transaction(tx_data):
                        tx_data[
                            "affiliate_address"
                        ] = self.get_affiliate_address_for_chain(
                            tx_data.get("chain", "ethereum")
                        )
                        transactions.append(tx_data)
                        logger.info(
                            f"✅ Found ShapeShift affiliate transaction: {tx_data['tx_hash']}"
                        )

                    # Add small delay to avoid overwhelming the page
                    time.sleep(0.1)

                except Exception as e:
                    logger.error(f"Error processing transaction {i}: {e}")
                    continue

            logger.info(
                f"Successfully scraped {len(transactions)} ShapeShift affiliate transactions"
            )
            return transactions

        except Exception as e:
            logger.error(f"Error scraping transactions: {e}")
            return []

    def is_shapeshift_affiliate_transaction(self, tx_data: Dict) -> bool:
        """Check if transaction involves ShapeShift affiliate addresses"""
        try:
            from_address = tx_data.get("from_address", "").lower()
            to_address = tx_data.get("to_address", "").lower()

            # Check if any ShapeShift affiliate address is involved
            for affiliate_address in self.shapeshift_affiliates.values():
                if affiliate_address.lower() in [from_address, to_address]:
                    return True

            # Also check if the transaction involves known affiliate patterns
            # (This could be expanded based on observed patterns)

            return False

        except Exception as e:
            logger.error(f"Error checking affiliate status: {e}")
            return False

    def get_affiliate_address_for_chain(self, chain: str) -> str:
        """Get the ShapeShift affiliate address for a specific chain"""
        return self.shapeshift_affiliates.get(
            chain, self.shapeshift_affiliates["ethereum"]
        )

    def save_transactions_to_db(self, transactions: List[Dict], chain: str):
        """Save scraped transactions to database"""
        if not transactions:
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        saved_count = 0
        for tx in transactions:
            try:
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO butterswap_web_transactions 
                    (chain, tx_hash, block_number, block_timestamp, from_address, to_address,
                     token_in, token_out, amount_in, amount_out, fee_amount, fee_token,
                     affiliate_address, affiliate_fee_usd, volume_usd, token_in_name,
                     token_out_name, status, explorer_url)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        chain,
                        tx.get("tx_hash"),
                        tx.get("block_number"),
                        tx.get("block_timestamp"),
                        tx.get("from_address"),
                        tx.get("to_address"),
                        tx.get("token_in"),
                        tx.get("token_out"),
                        tx.get("amount_in"),
                        tx.get("amount_out"),
                        tx.get("fee_amount"),
                        tx.get("fee_token"),
                        tx.get("affiliate_address"),
                        tx.get("affiliate_fee_usd", 0.0),
                        tx.get("volume_usd", 0.0),
                        tx.get("token_in_name"),
                        tx.get("token_out_name"),
                        tx.get("status"),
                        f"{self.explorer_url}?tx={tx.get('tx_hash')}",
                    ),
                )

                if cursor.rowcount > 0:
                    saved_count += 1

            except Exception as e:
                logger.error(f"Error saving transaction {tx.get('tx_hash')}: {e}")

        conn.commit()
        conn.close()

        logger.info(f"💾 Saved {saved_count} new transactions to database")

    def get_database_stats(self):
        """Get database statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM butterswap_web_transactions")
        total_transactions = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(DISTINCT chain) FROM butterswap_web_transactions")
        unique_chains = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(DISTINCT affiliate_address) FROM butterswap_web_transactions WHERE affiliate_address IS NOT NULL"
        )
        affiliate_transactions = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(*) FROM butterswap_web_transactions WHERE status = 'success'"
        )
        successful_transactions = cursor.fetchone()[0]

        conn.close()

        print(f"\n📊 ButterSwap Web Scraper Database Statistics:")
        print(f"   Total transactions: {total_transactions}")
        print(f"   Affiliate transactions: {affiliate_transactions}")
        print(f"   Successful transactions: {successful_transactions}")
        print(f"   Unique chains: {unique_chains}")

    def run_scraper(
        self,
        chains: List[str] = None,
        max_transactions_per_chain: int = 100,
        headless: bool = False,
    ):
        """Run the Butterswap web scraper"""
        if chains is None:
            chains = ["ethereum"]  # Default to Ethereum

        logger.info("🚀 Starting ButterSwap web scraper")

        driver = None
        try:
            driver = self.setup_webdriver(headless)

            total_transactions = 0
            for chain in chains:
                if chain not in self.supported_chains:
                    logger.warning(f"Unsupported chain: {chain}, skipping...")
                    continue

                logger.info(f"\n🔍 Scraping {chain} chain...")

                # Navigate to explorer for this chain
                if not self.navigate_to_explorer(driver, chain):
                    logger.error(f"Failed to navigate to {chain} explorer, skipping...")
                    continue

                # Scrape transactions
                transactions = self.scrape_transactions(
                    driver, max_transactions_per_chain
                )

                # Save to database
                self.save_transactions_to_db(transactions, chain)
                total_transactions += len(transactions)

                # Add delay between chains
                time.sleep(2)

            logger.info(
                f"\n✅ ButterSwap web scraper completed! Found {total_transactions} total transactions"
            )
            self.get_database_stats()

        except Exception as e:
            logger.error(f"Error running scraper: {e}")
        finally:
            if driver:
                driver.quit()


def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description="ButterSwap Web Scraper")
    parser.add_argument(
        "--chains",
        nargs="+",
        default=["ethereum"],
        help="Chains to scrape (default: ethereum)",
    )
    parser.add_argument(
        "--max-tx",
        type=int,
        default=100,
        help="Maximum transactions per chain (default: 100)",
    )
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    args = parser.parse_args()

    scraper = ButterSwapWebScraper()
    scraper.run_scraper(args.chains, args.max_tx, args.headless)


if __name__ == "__main__":
    main()
