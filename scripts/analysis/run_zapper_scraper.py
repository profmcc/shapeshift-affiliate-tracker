#!/usr/bin/env python3
"""
Simple runner for the Zapper wallet scraper.
Provides easy execution with different options.
"""

import asyncio
import argparse
import sys
from pathlib import Path

# Add current directory to path to import the scraper
sys.path.append(str(Path(__file__).parent))

from zapper_wallet_scraper import ZapperWalletScraper, logger


async def run_scraper(url: str, headless: bool = True, output_dir: str = "data"):
    """Run the Zapper scraper with specified parameters."""
    logger.info("=" * 60)
    logger.info("ZAPPER WALLET DATA SCRAPER")
    logger.info("=" * 60)
    
    scraper = ZapperWalletScraper(headless=headless)
    result = await scraper.scrape_wallet_data(url, output_dir)
    
    if result:
        csv_file, json_file = result
        logger.info("=" * 60)
        logger.info("SCRAPING COMPLETED SUCCESSFULLY!")
        logger.info("=" * 60)
        logger.info(f"📁 CSV file: {csv_file}")
        logger.info(f"📁 JSON file: {json_file}")
        
        # Try to display a summary
        try:
            import pandas as pd
            df = pd.read_csv(csv_file)
            logger.info(f"📊 Total tokens extracted: {len(df)}")
            
            if 'Value' in df.columns:
                # Clean and calculate total value
                df['Value_Numeric'] = pd.to_numeric(
                    df['Value'].str.replace('$', '').str.replace(',', ''), 
                    errors='coerce'
                )
                total_value = df['Value_Numeric'].sum()
                logger.info(f"💰 Total portfolio value: ${total_value:,.2f}")
                
                # Show top 5 tokens by value
                top_tokens = df.nlargest(5, 'Value_Numeric')
                logger.info("🏆 Top 5 tokens by value:")
                for _, row in top_tokens.iterrows():
                    logger.info(f"   {row['Token']}: ${row['Value']}")
                    
        except Exception as e:
            logger.warning(f"Could not generate summary: {e}")
    else:
        logger.error("❌ Scraping failed!")
        sys.exit(1)


def main():
    """Main function with command line argument parsing."""
    parser = argparse.ArgumentParser(
        description="Scrape token data from Zapper wallet tables",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_zapper_scraper.py
  python run_zapper_scraper.py --url "https://zapper.xyz/..." --visible
  python run_zapper_scraper.py --output-dir "my_data"
        """
    )
    
    parser.add_argument(
        '--url',
        type=str,
        default="https://zapper.xyz/bundle/0x90a48d5cf7343b08da12e067680b4c6dbfe551be,0x6268d07327f4fb7380732dc6d63d95f88c0e083b,0x74d63f31c2335b5b3ba7ad2812357672b2624ced,0xb5f944600785724e31edb90f9dfa16dbf01af000,0xb0e3175341794d1dc8e5f02a02f9d26989ebedb3,0x8b92b1698b57bedf2142297e9397875adbb2297e,0x38276553f8fbf2a027d901f8be45f00373d8dd48,0x5c59d0ec51729e40c413903be6a4612f4e2452da,0x9c9aa90363630d4ab1d9dbf416cc3bbc8d3ed502,C7RTJbss7R1r7j8NUNYbasUXfbPJR99PMhqznvCiU43N?id=0x4e4c9e7717da5bd1e98a5d723b6b1f964dd30861&label=SS%20DAO&icon=%F0%9F%98%83&tab=wallet",
        help="Zapper URL to scrape (default: SS DAO bundle)"
    )
    
    parser.add_argument(
        '--visible',
        action='store_true',
        help="Run browser in visible mode (not headless)"
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default="data",
        help="Output directory for data files (default: data)"
    )
    
    args = parser.parse_args()
    
    # Run the scraper
    asyncio.run(run_scraper(
        url=args.url,
        headless=not args.visible,
        output_dir=args.output_dir
    ))


if __name__ == "__main__":
    main() 