#!/usr/bin/env python3
"""
Debug script to understand Zapper page structure and find correct selectors.
"""

import asyncio
import logging
import sys
from playwright.async_api import async_playwright, Browser, Page

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def debug_page_structure():
    """Debug the Zapper page structure to find correct selectors."""
    playwright = await async_playwright().start()
    
    browser = await playwright.chromium.launch(
        headless=False,
        args=[
            '--no-sandbox',
            '--disable-dev-shm-usage',
            '--disable-blink-features=AutomationControlled',
            '--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
    )
    
    page = await browser.new_page()
    await page.set_viewport_size({"width": 1920, "height": 1080})
    
    # Add headers
    await page.set_extra_http_headers({
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
        'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"macOS"',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
    })
    
    # Remove automation indicators
    await page.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
        });
    """)
    
    url = "https://zapper.xyz/bundle/0x90a48d5cf7343b08da12e067680b4c6dbfe551be,0x6268d07327f4fb7380732dc6d63d95f88c0e083b,0x74d63f31c2335b5b3ba7ad2812357672b2624ced,0xb5f944600785724e31edb90f9dfa16dbf01af000,0xb0e3175341794d1dc8e5f02a02f9d26989ebedb3,0x8b92b1698b57bedf2142297e9397875adbb2297e,0x38276553f8fbf2a027d901f8be45f00373d8dd48,0x5c59d0ec51729e40c413903be6a4612f4e2452da,0x9c9aa90363630d4ab1d9dbf416cc3bbc8d3ed502,C7RTJbss7R1r7j8NUNYbasUXfbPJR99PMhqznvCiU43N?id=0x4e4c9e7717da5bd1e98a5d723b6b1f964dd30861&label=SS%20DAO&icon=%F0%9F%98%83&tab=wallet"
    
    logger.info("🔍 Starting page structure debug...")
    logger.info(f"Navigating to: {url}")
    logger.info("⚠️  Please complete the Cloudflare challenge manually")
    logger.info("⏳ Waiting for page to load...")
    
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        
        # Wait for manual interaction
        logger.info("⏳ Waiting for manual Cloudflare bypass...")
        await page.wait_for_timeout(10000)  # Wait 10 seconds for manual interaction
        
        # Check page title
        title = await page.title()
        logger.info(f"📄 Page title: {title}")
        
        # Check current URL
        current_url = page.url
        logger.info(f"🌐 Current URL: {current_url}")
        
        # Look for various elements that might contain token data
        logger.info("🔍 Searching for token data elements...")
        
        # Check for tables
        tables = await page.query_selector_all('table')
        logger.info(f"📊 Found {len(tables)} table elements")
        
        for i, table in enumerate(tables):
            try:
                rows = await table.query_selector_all('tr')
                logger.info(f"  Table {i}: {len(rows)} rows")
                
                if len(rows) > 0:
                    # Check first row for headers
                    first_row = rows[0]
                    cells = await first_row.query_selector_all('th, td')
                    headers = []
                    for cell in cells:
                        text = await cell.inner_text()
                        headers.append(text.strip())
                    logger.info(f"    Headers: {headers}")
                    
                    # Check a few data rows
                    for j in range(1, min(4, len(rows))):
                        row = rows[j]
                        cells = await row.query_selector_all('td')
                        row_data = []
                        for cell in cells:
                            text = await cell.inner_text()
                            row_data.append(text.strip())
                        logger.info(f"    Row {j}: {row_data}")
                        
            except Exception as e:
                logger.warning(f"  Error analyzing table {i}: {e}")
        
        # Check for div-based layouts
        logger.info("🔍 Searching for div-based token containers...")
        
        div_selectors = [
            '[class*="token"]',
            '[class*="Token"]',
            '[class*="asset"]',
            '[class*="Asset"]',
            '[class*="portfolio"]',
            '[class*="Portfolio"]',
            '[class*="wallet"]',
            '[class*="Wallet"]'
        ]
        
        for selector in div_selectors:
            try:
                elements = await page.query_selector_all(selector)
                if elements:
                    logger.info(f"  Found {len(elements)} elements with selector: {selector}")
                    
                    # Check first few elements
                    for i, elem in enumerate(elements[:3]):
                        try:
                            text = await elem.inner_text()
                            if text.strip():
                                logger.info(f"    Element {i}: {text.strip()[:100]}...")
                        except:
                            pass
                            
            except Exception as e:
                logger.warning(f"  Error with selector {selector}: {e}")
        
        # Check for any elements with price/value indicators
        logger.info("🔍 Searching for price/value elements...")
        
        price_selectors = [
            '[class*="price"]',
            '[class*="Price"]',
            '[class*="value"]',
            '[class*="Value"]',
            '[class*="balance"]',
            '[class*="Balance"]',
            '[class*="amount"]',
            '[class*="Amount"]'
        ]
        
        for selector in price_selectors:
            try:
                elements = await page.query_selector_all(selector)
                if elements:
                    logger.info(f"  Found {len(elements)} elements with selector: {selector}")
                    
                    # Check first few elements
                    for i, elem in enumerate(elements[:3]):
                        try:
                            text = await elem.inner_text()
                            if text.strip():
                                logger.info(f"    Element {i}: {text.strip()}")
                        except:
                            pass
                            
            except Exception as e:
                logger.warning(f"  Error with selector {selector}: {e}")
        
        # Get page HTML structure for manual inspection
        logger.info("📝 Getting page HTML for manual inspection...")
        
        # Wait for user to manually inspect
        logger.info("⏳ Please manually inspect the page and press Enter when ready to continue...")
        input("Press Enter to continue...")
        
        # Get the page HTML
        html = await page.content()
        
        # Save HTML for inspection
        with open('zapper_page_debug.html', 'w', encoding='utf-8') as f:
            f.write(html)
        
        logger.info("💾 Page HTML saved to: zapper_page_debug.html")
        
        # Try to find any text that looks like token data
        logger.info("🔍 Searching for token-like text patterns...")
        
        # Look for patterns like "$X.XX" or token symbols
        page_text = await page.inner_text('body')
        
        # Split into lines and look for patterns
        lines = page_text.split('\n')
        token_patterns = []
        
        for line in lines:
            line = line.strip()
            if line and (
                '$' in line or 
                any(word in line.lower() for word in ['eth', 'btc', 'usdc', 'usdt', 'fox', 'token', 'coin']) or
                any(char.isupper() for char in line[:3])  # Likely token symbols
            ):
                token_patterns.append(line)
        
        logger.info(f"🎯 Found {len(token_patterns)} potential token data lines:")
        for i, pattern in enumerate(token_patterns[:10]):  # Show first 10
            logger.info(f"  {i+1}: {pattern}")
        
        logger.info("✅ Debug complete! Check the HTML file for detailed structure.")
        
    except Exception as e:
        logger.error(f"❌ Error during debug: {e}")
    finally:
        await browser.close()


if __name__ == "__main__":
    asyncio.run(debug_page_structure()) 