#!/usr/bin/env python3
"""
Final Trade Pair Summary
Provides a comprehensive summary of the top 5 trade pairs across all platforms.
"""

import json
import pandas as pd
from collections import defaultdict


def load_analysis_results():
    """Load the detailed analysis results"""
    try:
        with open("detailed_trade_analysis_results.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print(
            "❌ Analysis results file not found. Run detailed_trade_analysis.py first."
        )
        return None


def create_trade_pair_summary():
    """Create a comprehensive summary of trade pairs"""
    results = load_analysis_results()
    if not results:
        return

    print("=" * 80)
    print("🏆 TOP 5 TRADE PAIRS ACROSS ALL PLATFORMS")
    print("=" * 80)

    # Get top 5 overall
    top_pairs = list(results["top_pairs"].items())[:5]

    print(f"\n📊 OVERALL TOP 5 TRADE PAIRS:")
    print("-" * 50)
    for i, (pair, count) in enumerate(top_pairs, 1):
        print(f"{i}. {pair}: {count:,} transactions")

    # Platform breakdown
    print(f"\n📋 PLATFORM BREAKDOWN FOR TOP 5:")
    print("-" * 50)

    for pair, _ in top_pairs:
        print(f"\n{pair}:")
        found_in_platforms = []

        for platform, pairs in results["platform_stats"].items():
            if pair in pairs:
                found_in_platforms.append(f"{platform}: {pairs[pair]:,}")

        if found_in_platforms:
            for platform_info in found_in_platforms:
                print(f"   {platform_info}")
        else:
            print("   (Not found in individual platform data)")

    # Platform totals
    print(f"\n📊 PLATFORM SUMMARY:")
    print("-" * 40)
    for platform, pairs in results["platform_stats"].items():
        total = sum(pairs.values())
        unique_pairs = len(pairs)
        print(
            f"{platform:15s}: {total:6,} transactions, {unique_pairs:3d} unique pairs"
        )

    # Volume analysis
    if "token_volume" in results and results["token_volume"]:
        print(f"\n💰 TOP TOKENS BY VOLUME:")
        print("-" * 40)
        top_volume = list(results["token_volume"].items())[:5]
        for i, (token, volume) in enumerate(top_volume, 1):
            print(f"{i}. {token}: {volume:,.2f}")

    # Key insights
    print(f"\n🔍 KEY INSIGHTS:")
    print("-" * 30)

    # Most active platform
    platform_totals = {}
    for platform, pairs in results["platform_stats"].items():
        platform_totals[platform] = sum(pairs.values())

    most_active = max(platform_totals.items(), key=lambda x: x[1])
    print(f"• Most active platform: {most_active[0]} ({most_active[1]:,} transactions)")

    # Most diverse platform
    most_diverse = max(results["platform_stats"].items(), key=lambda x: len(x[1]))
    print(
        f"• Most diverse platform: {most_diverse[0]} ({len(most_diverse[1])} unique pairs)"
    )

    # Most common token
    token_counts = defaultdict(int)
    for pair, count in results["top_pairs"].items():
        if "/" in pair:
            tokens = pair.split("/")
            for token in tokens:
                token_counts[token] += count
        else:
            token_counts[pair] += count

    if token_counts:
        most_common_token = max(token_counts.items(), key=lambda x: x[1])
        print(
            f"• Most common token: {most_common_token[0]} ({most_common_token[1]:,} appearances)"
        )

    print(f"\n💾 Full results available in: detailed_trade_analysis_results.json")


def analyze_cross_platform_pairs():
    """Analyze pairs that appear across multiple platforms"""
    results = load_analysis_results()
    if not results:
        return

    print(f"\n🔄 CROSS-PLATFORM ANALYSIS:")
    print("-" * 40)

    # Find pairs that appear in multiple platforms
    pair_platforms = defaultdict(set)
    for platform, pairs in results["platform_stats"].items():
        for pair in pairs.keys():
            pair_platforms[pair].add(platform)

    # Show pairs that appear in multiple platforms
    cross_platform_pairs = {
        pair: platforms
        for pair, platforms in pair_platforms.items()
        if len(platforms) > 1
    }

    if cross_platform_pairs:
        print("Pairs appearing in multiple platforms:")
        for pair, platforms in sorted(
            cross_platform_pairs.items(), key=lambda x: len(x[1]), reverse=True
        ):
            print(f"   {pair}: {', '.join(platforms)}")
    else:
        print("No pairs found across multiple platforms")


def main():
    """Main function"""
    create_trade_pair_summary()
    analyze_cross_platform_pairs()


if __name__ == "__main__":
    main()
