#!/usr/bin/env python3
"""
Zapper Wallet Token Data Scraper

This script extracts token data from Zapper's wallet table, capturing:
- Token name/symbol
- Current price
- Balance amount
- Total value

Handles dynamic loading, pagination, and data validation.
"""

import asyncio
import csv
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
from playwright.async_api import async_playwright, Browser, Page
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("zapper_scraper.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


class ZapperWalletScraper:
    """Scraper for extracting token data from Zapper wallet tables."""

    def __init__(self, headless: bool = True, timeout: int = 60000):
        self.headless = headless
        self.timeout = timeout
        self.data: List[Dict[str, str]] = []

    async def setup_browser(self) -> Tuple[Browser, Page]:
        """Initialize browser and create a new page with anti-detection measures."""
        playwright = await async_playwright().start()

        # Use a more realistic browser configuration
        browser = await playwright.chromium.launch(
            headless=self.headless,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
                "--disable-web-security",
                "--disable-features=VizDisplayCompositor",
                "--disable-extensions",
                "--no-first-run",
                "--disable-default-apps",
                "--disable-background-timer-throttling",
                "--disable-backgrounding-occluded-windows",
                "--disable-renderer-backgrounding",
                "--disable-features=TranslateUI",
                "--disable-ipc-flooding-protection",
                "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            ],
        )

        page = await browser.new_page()

        # Set viewport to a common resolution
        await page.set_viewport_size({"width": 1920, "height": 1080})

        # Add extra headers to appear more human
        await page.set_extra_http_headers(
            {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
                "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                "Sec-Ch-Ua-Mobile": "?0",
                "Sec-Ch-Ua-Platform": '"macOS"',
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                "Upgrade-Insecure-Requests": "1",
            }
        )

        # Execute script to remove webdriver property
        await page.add_init_script(
            """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
        """
        )

        return browser, page

    async def navigate_to_url(self, page: Page, url: str) -> bool:
        """Navigate to the Zapper URL and wait for page load with Cloudflare handling."""
        try:
            logger.info(f"Navigating to: {url}")

            # First, try to load the page with a more relaxed timeout
            await page.goto(url, wait_until="domcontentloaded", timeout=self.timeout)

            # Wait a bit for Cloudflare to process
            await page.wait_for_timeout(3000)

            # Check if we're on a Cloudflare challenge page
            cloudflare_selectors = [
                'iframe[src*="cloudflare"]',
                "#challenge-form",
                ".cf-browser-verification",
                'div[class*="cf-"]',
            ]

            for selector in cloudflare_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        logger.info(
                            "Detected Cloudflare challenge, waiting for resolution..."
                        )
                        # Wait for Cloudflare to resolve
                        await page.wait_for_timeout(10000)
                        break
                except:
                    continue

            # Wait for the page to be fully loaded
            try:
                await page.wait_for_load_state("networkidle", timeout=30000)
            except PlaywrightTimeoutError:
                logger.warning("Network idle timeout, continuing anyway...")

            # Wait for the wallet tab to be active or any content to load
            try:
                await page.wait_for_selector(
                    '[data-testid="wallet-tab"], .wallet-tab, [role="tab"][aria-selected="true"], table, [class*="table"]',
                    timeout=20000,
                )
            except PlaywrightTimeoutError:
                logger.warning("Wallet tab selector not found, trying to continue...")

            logger.info("Page loaded successfully")
            return True

        except PlaywrightTimeoutError as e:
            logger.error(f"Timeout while loading page: {e}")
            return False
        except Exception as e:
            logger.error(f"Error navigating to URL: {e}")
            return False

    async def wait_for_table(self, page: Page) -> bool:
        """Wait for the token table to load."""
        try:
            # Multiple possible selectors for the table
            selectors = [
                'table[data-testid="wallet-table"]',
                ".wallet-table",
                "table",
                '[role="table"]',
                ".token-table",
                '[class*="table"]',
                '[class*="Table"]',
            ]

            for selector in selectors:
                try:
                    await page.wait_for_selector(selector, timeout=15000)
                    logger.info(f"Found table with selector: {selector}")
                    return True
                except PlaywrightTimeoutError:
                    continue

            logger.warning("No table found with any expected selector")
            return False

        except Exception as e:
            logger.error(f"Error waiting for table: {e}")
            return False

    async def extract_table_data(self, page: Page) -> List[Dict[str, str]]:
        """Extract all token data from the table."""
        try:
            # Try to find the table with various selectors
            table_selectors = [
                'table[data-testid="wallet-table"]',
                ".wallet-table",
                "table",
                '[role="table"]',
                '[class*="table"]',
            ]

            table = None
            for selector in table_selectors:
                try:
                    table = await page.query_selector(selector)
                    if table:
                        logger.info(f"Using table selector: {selector}")
                        break
                except:
                    continue

            if not table:
                logger.error("No table found")
                return []

            # Extract all rows
            rows = await table.query_selector_all("tr")
            if not rows:
                logger.warning("No rows found in table")
                return []

            logger.info(f"Found {len(rows)} rows in table")

            data = []
            for i, row in enumerate(rows):
                if i == 0:  # Skip header row
                    continue

                try:
                    cells = await row.query_selector_all("td")
                    if len(cells) >= 4:
                        token = await self.extract_text(cells[0])
                        price = await self.extract_text(cells[1])
                        balance = await self.extract_text(cells[2])
                        value = await self.extract_text(cells[3])

                        if token and token.strip():  # Only add if token name exists
                            data.append(
                                {
                                    "Token": token.strip(),
                                    "Price": price.strip() if price else "",
                                    "Balance": balance.strip() if balance else "",
                                    "Value": value.strip() if value else "",
                                }
                            )

                except Exception as e:
                    logger.warning(f"Error extracting row {i}: {e}")
                    continue

            logger.info(f"Successfully extracted {len(data)} token entries")
            return data

        except Exception as e:
            logger.error(f"Error extracting table data: {e}")
            return []

    async def extract_text(self, element) -> str:
        """Extract text content from an element, handling nested elements."""
        try:
            # Get all text content, including nested elements
            text = await element.inner_text()
            return text.strip()
        except:
            return ""

    async def handle_pagination(self, page: Page) -> bool:
        """Handle pagination or lazy loading if present."""
        try:
            # Look for "Load More" button or similar
            load_more_selectors = [
                'button:has-text("Load More")',
                'button:has-text("Show More")',
                '[data-testid="load-more"]',
                ".load-more-button",
            ]

            for selector in load_more_selectors:
                try:
                    load_more_btn = await page.query_selector(selector)
                    if load_more_btn and await load_more_btn.is_visible():
                        logger.info("Found load more button, clicking...")
                        await load_more_btn.click()
                        await page.wait_for_timeout(2000)  # Wait for content to load
                        return True
                except:
                    continue

            # Check for scroll-based loading
            try:
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(2000)
                logger.info("Scrolled to bottom to trigger lazy loading")
                return True
            except:
                pass

            return False

        except Exception as e:
            logger.error(f"Error handling pagination: {e}")
            return False

    async def validate_data(self, data: List[Dict[str, str]]) -> bool:
        """Validate extracted data for completeness."""
        if not data:
            logger.error("No data extracted")
            return False

        # Check for required columns
        required_columns = ["Token", "Price", "Balance", "Value"]
        for row in data:
            for col in required_columns:
                if col not in row:
                    logger.error(f"Missing required column: {col}")
                    return False

        # Check for empty token names
        empty_tokens = [row for row in data if not row.get("Token", "").strip()]
        if empty_tokens:
            logger.warning(f"Found {len(empty_tokens)} rows with empty token names")

        logger.info(f"Data validation passed. Extracted {len(data)} valid rows")
        return True

    def save_data(
        self, data: List[Dict[str, str]], output_dir: str = "data"
    ) -> Tuple[str, str]:
        """Save extracted data to CSV and JSON files."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Create output directory
        Path(output_dir).mkdir(exist_ok=True)

        # Save as CSV
        csv_filename = f"{output_dir}/zapper_wallet_data_{timestamp}.csv"
        with open(csv_filename, "w", newline="", encoding="utf-8") as csvfile:
            if data:
                fieldnames = data[0].keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)

        # Save as JSON
        json_filename = f"{output_dir}/zapper_wallet_data_{timestamp}.json"
        with open(json_filename, "w", encoding="utf-8") as jsonfile:
            json.dump(data, jsonfile, indent=2, ensure_ascii=False)

        logger.info(f"Data saved to: {csv_filename} and {json_filename}")
        return csv_filename, json_filename

    async def scrape_wallet_data(
        self, url: str, output_dir: str = "data"
    ) -> Optional[Tuple[str, str]]:
        """Main method to scrape wallet data from Zapper."""
        browser = None
        try:
            # Setup browser
            browser, page = await self.setup_browser()

            # Navigate to URL
            if not await self.navigate_to_url(page, url):
                return None

            # Wait for table to load
            if not await self.wait_for_table(page):
                logger.error("Table not found or failed to load")
                return None

            # Extract initial data
            data = await self.extract_table_data(page)

            # Handle pagination/lazy loading
            max_pagination_attempts = 5
            for attempt in range(max_pagination_attempts):
                if await self.handle_pagination(page):
                    # Extract additional data after pagination
                    additional_data = await self.extract_table_data(page)
                    # Merge new data, avoiding duplicates
                    existing_tokens = {row["Token"] for row in data}
                    for row in additional_data:
                        if row["Token"] not in existing_tokens:
                            data.append(row)
                            existing_tokens.add(row["Token"])
                    logger.info(
                        f"Pagination attempt {attempt + 1}: Added {len(additional_data)} new rows"
                    )
                else:
                    break

            # Validate data
            if not await self.validate_data(data):
                return None

            # Save data
            return self.save_data(data, output_dir)

        except Exception as e:
            logger.error(f"Error during scraping: {e}")
            return None
        finally:
            if browser:
                await browser.close()


async def main():
    """Main function to run the scraper."""
    # Zapper URL with multiple addresses
    url = "https://zapper.xyz/bundle/0x90a48d5cf7343b08da12e067680b4c6dbfe551be,0x6268d07327f4fb7380732dc6d63d95f88c0e083b,0x74d63f31c2335b5b3ba7ad2812357672b2624ced,0xb5f944600785724e31edb90f9dfa16dbf01af000,0xb0e3175341794d1dc8e5f02a02f9d26989ebedb3,0x8b92b1698b57bedf2142297e9397875adbb2297e,0x38276553f8fbf2a027d901f8be45f00373d8dd48,0x5c59d0ec51729e40c413903be6a4612f4e2452da,0x9c9aa90363630d4ab1d9dbf416cc3bbc8d3ed502,C7RTJbss7R1r7j8NUNYbasUXfbPJR99PMhqznvCiU43N?id=0x4e4c9e7717da5bd1e98a5d723b6b1f964dd30861&label=SS%20DAO&icon=%F0%9F%98%83&tab=wallet"

    logger.info("Starting Zapper wallet data scraper")

    scraper = ZapperWalletScraper(headless=True)
    result = await scraper.scrape_wallet_data(url)

    if result:
        csv_file, json_file = result
        logger.info(f"Scraping completed successfully!")
        logger.info(f"CSV file: {csv_file}")
        logger.info(f"JSON file: {json_file}")

        # Display summary
        try:
            df = pd.read_csv(csv_file)
            logger.info(f"Total tokens extracted: {len(df)}")
            if "Value" in df.columns:
                # Try to extract numeric values for total calculation
                df["Value_Numeric"] = pd.to_numeric(
                    df["Value"].str.replace("$", "").str.replace(",", ""),
                    errors="coerce",
                )
                total_value = df["Value_Numeric"].sum()
                logger.info(f"Total portfolio value: ${total_value:,.2f}")
        except Exception as e:
            logger.warning(f"Could not calculate total value: {e}")
    else:
        logger.error("Scraping failed")


if __name__ == "__main__":
    asyncio.run(main())
