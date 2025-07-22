#!/usr/bin/env python3
"""
Automated Zapper Portfolio Scraper

This script can be scheduled to run periodically to track portfolio changes over time.
It includes:
- Scheduled scraping
- Historical data tracking
- Change detection
- Automated reporting
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
from zapper_wallet_scraper import ZapperWalletScraper, logger


class AutomatedZapperTracker:
    """Automated tracker for Zapper portfolio data with historical analysis."""
    
    def __init__(self, data_dir: str = "data", history_file: str = "portfolio_history.json"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.history_file = self.data_dir / history_file
        self.history = self.load_history()
        
    def load_history(self) -> Dict:
        """Load historical portfolio data."""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not load history file: {e}")
        return {"snapshots": [], "metadata": {"created": datetime.now().isoformat()}}
    
    def save_history(self):
        """Save historical portfolio data."""
        try:
            with open(self.history_file, 'w') as f:
                json.dump(self.history, f, indent=2)
        except Exception as e:
            logger.error(f"Could not save history: {e}")
    
    async def capture_snapshot(self, url: str) -> Optional[Dict]:
        """Capture a new portfolio snapshot."""
        logger.info("📸 Capturing portfolio snapshot...")
        
        scraper = ZapperWalletScraper(headless=True)
        result = await scraper.scrape_wallet_data(url, str(self.data_dir))
        
        if not result:
            logger.error("❌ Failed to capture snapshot")
            return None
            
        csv_file, json_file = result
        
        # Load and process the data
        df = pd.read_csv(csv_file)
        
        # Calculate portfolio metrics
        df['Value_Numeric'] = pd.to_numeric(
            df['Value'].str.replace('$', '').str.replace(',', ''), 
            errors='coerce'
        )
        
        total_value = df['Value_Numeric'].sum()
        token_count = len(df)
        
        snapshot = {
            'timestamp': datetime.now().isoformat(),
            'total_value': total_value,
            'total_value_formatted': f"${total_value:,.2f}",
            'token_count': token_count,
            'data_file': csv_file,
            'tokens': df.to_dict('records')
        }
        
        # Add to history
        self.history['snapshots'].append(snapshot)
        self.save_history()
        
        logger.info(f"✅ Snapshot captured: {snapshot['total_value_formatted']} ({token_count} tokens)")
        return snapshot
    
    def analyze_changes(self, days_back: int = 7) -> Dict:
        """Analyze portfolio changes over time."""
        if len(self.history['snapshots']) < 2:
            return {"error": "Insufficient historical data"}
        
        # Get recent snapshots
        cutoff_date = datetime.now() - timedelta(days=days_back)
        recent_snapshots = [
            s for s in self.history['snapshots']
            if datetime.fromisoformat(s['timestamp']) > cutoff_date
        ]
        
        if len(recent_snapshots) < 2:
            return {"error": f"Insufficient data for {days_back} day analysis"}
        
        # Calculate changes
        oldest = recent_snapshots[0]
        newest = recent_snapshots[-1]
        
        value_change = newest['total_value'] - oldest['total_value']
        value_change_pct = (value_change / oldest['total_value']) * 100 if oldest['total_value'] > 0 else 0
        
        token_change = newest['token_count'] - oldest['token_count']
        
        # Token-level changes
        old_tokens = {t['Token']: t for t in oldest['tokens']}
        new_tokens = {t['Token']: t for t in newest['tokens']}
        
        added_tokens = [t for token, t in new_tokens.items() if token not in old_tokens]
        removed_tokens = [t for token, t in old_tokens.items() if token not in new_tokens]
        
        analysis = {
            'period_days': days_back,
            'snapshots_analyzed': len(recent_snapshots),
            'oldest_snapshot': oldest['timestamp'],
            'newest_snapshot': newest['timestamp'],
            'value_change': value_change,
            'value_change_formatted': f"${value_change:+,.2f}",
            'value_change_percentage': value_change_pct,
            'token_count_change': token_change,
            'added_tokens': len(added_tokens),
            'removed_tokens': len(removed_tokens),
            'added_token_details': added_tokens,
            'removed_token_details': removed_tokens
        }
        
        return analysis
    
    def generate_change_report(self, analysis: Dict) -> str:
        """Generate a human-readable change report."""
        if 'error' in analysis:
            return f"❌ Analysis Error: {analysis['error']}"
        
        report_lines = [
            "=" * 60,
            "PORTFOLIO CHANGE ANALYSIS",
            "=" * 60,
            f"Period: {analysis['period_days']} days",
            f"Snapshots analyzed: {analysis['snapshots_analyzed']}",
            f"From: {analysis['oldest_snapshot']}",
            f"To: {analysis['newest_snapshot']}",
            "",
            "💰 VALUE CHANGES",
            "-" * 30,
            f"Change: {analysis['value_change_formatted']}",
            f"Percentage: {analysis['value_change_percentage']:+.2f}%",
            "",
            "🪙 TOKEN CHANGES",
            "-" * 30,
            f"Token count change: {analysis['token_count_change']:+d}",
            f"Tokens added: {analysis['added_tokens']}",
            f"Tokens removed: {analysis['removed_tokens']}",
        ]
        
        if analysis['added_token_details']:
            report_lines.extend([
                "",
                "➕ ADDED TOKENS",
                "-" * 30
            ])
            for token in analysis['added_token_details'][:5]:  # Show top 5
                report_lines.append(f"   {token['Token']}: {token['Value']}")
        
        if analysis['removed_token_details']:
            report_lines.extend([
                "",
                "➖ REMOVED TOKENS",
                "-" * 30
            ])
            for token in analysis['removed_token_details'][:5]:  # Show top 5
                report_lines.append(f"   {token['Token']}: {token['Value']}")
        
        report_lines.append("=" * 60)
        
        return "\n".join(report_lines)
    
    def cleanup_old_data(self, keep_days: int = 30):
        """Clean up old data files to save space."""
        cutoff_date = datetime.now() - timedelta(days=keep_days)
        
        # Clean up CSV and JSON files
        for pattern in ["zapper_wallet_data_*.csv", "zapper_wallet_data_*.json"]:
            for file_path in self.data_dir.glob(pattern):
                try:
                    file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_time < cutoff_date:
                        file_path.unlink()
                        logger.info(f"🗑️  Deleted old file: {file_path.name}")
                except Exception as e:
                    logger.warning(f"Could not delete {file_path}: {e}")
        
        # Clean up old snapshots from history
        original_count = len(self.history['snapshots'])
        self.history['snapshots'] = [
            s for s in self.history['snapshots']
            if datetime.fromisoformat(s['timestamp']) > cutoff_date
        ]
        
        removed_count = original_count - len(self.history['snapshots'])
        if removed_count > 0:
            self.save_history()
            logger.info(f"🗑️  Removed {removed_count} old snapshots from history")


async def main():
    """Main function for automated tracking."""
    logger.info("🤖 Starting Automated Zapper Portfolio Tracker")
    
    # Initialize tracker
    tracker = AutomatedZapperTracker()
    
    # SS DAO bundle URL
    url = "https://zapper.xyz/bundle/0x90a48d5cf7343b08da12e067680b4c6dbfe551be,0x6268d07327f4fb7380732dc6d63d95f88c0e083b,0x74d63f31c2335b5b3ba7ad2812357672b2624ced,0xb5f944600785724e31edb90f9dfa16dbf01af000,0xb0e3175341794d1dc8e5f02a02f9d26989ebedb3,0x8b92b1698b57bedf2142297e9397875adbb2297e,0x38276553f8fbf2a027d901f8be45f00373d8dd48,0x5c59d0ec51729e40c413903be6a4612f4e2452da,0x9c9aa90363630d4ab1d9dbf416cc3bbc8d3ed502,C7RTJbss7R1r7j8NUNYbasUXfbPJR99PMhqznvCiU43N?id=0x4e4c9e7717da5bd1e98a5d723b6b1f964dd30861&label=SS%20DAO&icon=%F0%9F%98%83&tab=wallet"
    
    try:
        # Capture new snapshot
        snapshot = await tracker.capture_snapshot(url)
        
        if snapshot:
            # Analyze changes
            analysis = tracker.analyze_changes(days_back=7)
            report = tracker.generate_change_report(analysis)
            
            print("\n" + report)
            
            # Cleanup old data
            tracker.cleanup_old_data(keep_days=30)
            
            logger.info("✅ Automated tracking completed successfully!")
        else:
            logger.error("❌ Automated tracking failed!")
            
    except Exception as e:
        logger.error(f"❌ Error in automated tracking: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main()) 