#!/usr/bin/env python3
"""
Example integration of Zapper wallet scraper with existing affiliate tracking workflow.

This script demonstrates how to:
1. Scrape portfolio data from Zapper
2. Process and analyze the data
3. Integrate with existing database workflows
4. Generate reports and visualizations
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
from zapper_wallet_scraper import ZapperWalletScraper, logger


class ZapperPortfolioAnalyzer:
    """Analyzer for Zapper portfolio data with integration to existing workflows."""
    
    def __init__(self, output_dir: str = "data"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
    async def scrape_and_analyze(self, url: str) -> Optional[Dict]:
        """Scrape portfolio data and perform analysis."""
        logger.info("🔍 Starting portfolio analysis...")
        
        # Scrape the data
        scraper = ZapperWalletScraper(headless=True)
        result = await scraper.scrape_wallet_data(url, str(self.output_dir))
        
        if not result:
            logger.error("❌ Failed to scrape portfolio data")
            return None
            
        csv_file, json_file = result
        
        # Load and analyze the data
        analysis = await self.analyze_portfolio(csv_file)
        
        # Save analysis results
        analysis_file = self.output_dir / f"portfolio_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(analysis_file, 'w') as f:
            json.dump(analysis, f, indent=2)
            
        logger.info(f"📊 Analysis saved to: {analysis_file}")
        return analysis
    
    async def analyze_portfolio(self, csv_file: str) -> Dict:
        """Analyze portfolio data and generate insights."""
        df = pd.read_csv(csv_file)
        
        # Clean numeric values
        df['Value_Numeric'] = pd.to_numeric(
            df['Value'].str.replace('$', '').str.replace(',', ''), 
            errors='coerce'
        )
        df['Price_Numeric'] = pd.to_numeric(
            df['Price'].str.replace('$', '').str.replace(',', ''), 
            errors='coerce'
        )
        
        # Calculate portfolio metrics
        total_value = df['Value_Numeric'].sum()
        token_count = len(df)
        
        # Top holdings
        top_holdings = df.nlargest(10, 'Value_Numeric')[['Token', 'Value', 'Value_Numeric']]
        
        # Token distribution
        token_distribution = df.groupby('Token')['Value_Numeric'].sum().sort_values(ascending=False)
        
        # Price analysis
        price_stats = df['Price_Numeric'].describe()
        
        analysis = {
            'timestamp': datetime.now().isoformat(),
            'portfolio_summary': {
                'total_value': total_value,
                'total_value_formatted': f"${total_value:,.2f}",
                'token_count': token_count,
                'average_token_value': total_value / token_count if token_count > 0 else 0
            },
            'top_holdings': top_holdings.to_dict('records'),
            'token_distribution': token_distribution.to_dict(),
            'price_statistics': price_stats.to_dict(),
            'data_quality': {
                'total_rows': len(df),
                'rows_with_values': len(df[df['Value_Numeric'].notna()]),
                'rows_with_prices': len(df[df['Price_Numeric'].notna()])
            }
        }
        
        return analysis
    
    def generate_report(self, analysis: Dict) -> str:
        """Generate a human-readable report from analysis."""
        report_lines = [
            "=" * 60,
            "ZAPPER PORTFOLIO ANALYSIS REPORT",
            "=" * 60,
            f"Generated: {analysis['timestamp']}",
            "",
            "📊 PORTFOLIO SUMMARY",
            "-" * 30,
            f"Total Value: {analysis['portfolio_summary']['total_value_formatted']}",
            f"Token Count: {analysis['portfolio_summary']['token_count']}",
            f"Average Token Value: ${analysis['portfolio_summary']['average_token_value']:,.2f}",
            "",
            "🏆 TOP 10 HOLDINGS",
            "-" * 30
        ]
        
        for i, holding in enumerate(analysis['top_holdings'][:10], 1):
            report_lines.append(f"{i:2d}. {holding['Token']:<20} {holding['Value']}")
        
        report_lines.extend([
            "",
            "📈 PRICE STATISTICS",
            "-" * 30,
            f"Min Price: ${analysis['price_statistics']['min']:,.2f}",
            f"Max Price: ${analysis['price_statistics']['max']:,.2f}",
            f"Mean Price: ${analysis['price_statistics']['mean']:,.2f}",
            "",
            "🔍 DATA QUALITY",
            "-" * 30,
            f"Total Rows: {analysis['data_quality']['total_rows']}",
            f"Rows with Values: {analysis['data_quality']['rows_with_values']}",
            f"Rows with Prices: {analysis['data_quality']['rows_with_prices']}",
            "=" * 60
        ])
        
        return "\n".join(report_lines)
    
    def save_to_database_format(self, csv_file: str, db_format: str = "sqlite") -> str:
        """Convert portfolio data to database-compatible format."""
        df = pd.read_csv(csv_file)
        
        # Clean and prepare data for database
        df['scraped_at'] = datetime.now().isoformat()
        df['source'] = 'zapper'
        
        # Save in different formats
        if db_format == "sqlite":
            db_file = self.output_dir / f"zapper_portfolio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            import sqlite3
            conn = sqlite3.connect(db_file)
            df.to_sql('portfolio_tokens', conn, if_exists='replace', index=False)
            conn.close()
            return str(db_file)
        elif db_format == "parquet":
            parquet_file = self.output_dir / f"zapper_portfolio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.parquet"
            df.to_parquet(parquet_file, index=False)
            return str(parquet_file)
        else:
            return csv_file


async def main():
    """Main function demonstrating the integration."""
    logger.info("🚀 Starting Zapper Portfolio Integration Example")
    
    # Initialize analyzer
    analyzer = ZapperPortfolioAnalyzer("data")
    
    # SS DAO bundle URL
    url = "https://zapper.xyz/bundle/0x90a48d5cf7343b08da12e067680b4c6dbfe551be,0x6268d07327f4fb7380732dc6d63d95f88c0e083b,0x74d63f31c2335b5b3ba7ad2812357672b2624ced,0xb5f944600785724e31edb90f9dfa16dbf01af000,0xb0e3175341794d1dc8e5f02a02f9d26989ebedb3,0x8b92b1698b57bedf2142297e9397875adbb2297e,0x38276553f8fbf2a027d901f8be45f00373d8dd48,0x5c59d0ec51729e40c413903be6a4612f4e2452da,0x9c9aa90363630d4ab1d9dbf416cc3bbc8d3ed502,C7RTJbss7R1r7j8NUNYbasUXfbPJR99PMhqznvCiU43N?id=0x4e4c9e7717da5bd1e98a5d723b6b1f964dd30861&label=SS%20DAO&icon=%F0%9F%98%83&tab=wallet"
    
    try:
        # Scrape and analyze
        analysis = await analyzer.scrape_and_analyze(url)
        
        if analysis:
            # Generate and display report
            report = analyzer.generate_report(analysis)
            print("\n" + report)
            
            # Save in database format
            csv_files = list(Path("data").glob("zapper_wallet_data_*.csv"))
            if csv_files:
                latest_csv = max(csv_files, key=lambda x: x.stat().st_mtime)
                db_file = analyzer.save_to_database_format(str(latest_csv))
                logger.info(f"💾 Database file created: {db_file}")
            
            logger.info("✅ Integration example completed successfully!")
        else:
            logger.error("❌ Integration example failed!")
            
    except Exception as e:
        logger.error(f"❌ Error in integration example: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main()) 