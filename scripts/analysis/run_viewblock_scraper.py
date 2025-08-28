#!/usr/bin/env python3
"""
Runner script for ViewBlock THORChain affiliate fee scraper
"""

import sys
import os
import logging
from viewblock_thorchain_scraper import (
    scrape_viewblock_comprehensive,
    get_database_stats,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("viewblock_scraper.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import selenium
        import requests

        logger.info("✓ All dependencies are installed")
        return True
    except ImportError as e:
        logger.error(f"Missing dependency: {e}")
        logger.error(
            "Please install dependencies with: pip install -r requirements_viewblock_scraper.txt"
        )
        return False


def check_chrome_driver():
    """Check if Chrome driver is available"""
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options

        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        # Try to create a driver instance
        driver = webdriver.Chrome(options=chrome_options)
        driver.quit()
        logger.info("✓ Chrome driver is working")
        return True
    except Exception as e:
        logger.error(f"Chrome driver issue: {e}")
        logger.error(
            "Please ensure Chrome browser is installed and ChromeDriver is available"
        )
        logger.error(
            "You can install ChromeDriver with: brew install chromedriver (on macOS)"
        )
        return False


def main():
    """Main function to run the ViewBlock scraper"""
    logger.info("Starting ViewBlock THORChain affiliate fee scraper")

    # Check dependencies
    if not check_dependencies():
        sys.exit(1)

    # Check Chrome driver
    if not check_chrome_driver():
        sys.exit(1)

    # Configuration
    max_pages = 20  # Adjust this based on how many pages you want to scrape

    logger.info(f"Configuration:")
    logger.info(f"  Max pages to scrape: {max_pages}")
    logger.info(f"  Database: viewblock_thorchain_fees.db")
    logger.info(f"  Log file: viewblock_scraper.log")

    try:
        # Run the scraper
        scrape_viewblock_comprehensive(max_pages=max_pages)

        # Show final statistics
        logger.info("Final database statistics:")
        get_database_stats()

        logger.info("Scraping completed successfully!")

    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
    except Exception as e:
        logger.error(f"Error during scraping: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
