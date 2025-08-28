#!/usr/bin/env python3
"""
Extract Comprehensive July 2025 Analysis Results
"""

import json


def main():
    with open("comprehensive_july_2025_analysis_results.json", "r") as f:
        data = json.load(f)

    analysis = data["comprehensive_july_2025_analysis"]
    pairs = analysis["top_pairs"]
    affiliates = analysis["affiliate_totals"]
    breakdown = analysis["affiliate_breakdown"]

    print("=" * 80)
    print("📊 COMPREHENSIVE JULY 2025 TRADE PAIR ANALYSIS")
    print("=" * 80)

    print(f"\n🏆 TOP 10 TRADE PAIRS:")
    print("-" * 50)

    # Sort pairs by volume
    sorted_pairs = sorted(pairs.items(), key=lambda x: x[1], reverse=True)

    for i, (pair, volume) in enumerate(sorted_pairs[:10], 1):
        print(f"{i:2d}. {pair:20s}: {volume:10.2f} volume")

    print(f"\n📊 OVERALL AFFILIATE STATISTICS:")
    print("-" * 50)

    # Sort affiliates by volume
    sorted_affiliates = sorted(affiliates.items(), key=lambda x: x[1], reverse=True)
    total_volume = sum(affiliates.values())

    for affiliate, volume in sorted_affiliates:
        percentage = (volume / total_volume * 100) if total_volume > 0 else 0
        print(f"{affiliate:20s}: {volume:10.2f} ({percentage:5.1f}%)")

    # FOX-specific analysis
    fox_pairs = {k: v for k, v in pairs.items() if "FOX" in k}
    if fox_pairs:
        print(f"\n🦊 FOX TRADE PAIRS ANALYSIS:")
        print("-" * 40)
        total_fox_volume = sum(fox_pairs.values())
        print(f"Total FOX volume: {total_fox_volume:,.2f}")

        for pair, volume in sorted(fox_pairs.items(), key=lambda x: x[1], reverse=True):
            print(f"{pair:20s}: {volume:10.2f}")

        # FOX affiliate breakdown
        fox_affiliate_volumes = {}
        for pair in fox_pairs.keys():
            if pair in breakdown:
                for affiliate, volume in breakdown[pair].items():
                    if affiliate not in fox_affiliate_volumes:
                        fox_affiliate_volumes[affiliate] = 0
                    fox_affiliate_volumes[affiliate] += volume

        print(f"\nFOX Affiliate Breakdown:")
        for affiliate, volume in sorted(
            fox_affiliate_volumes.items(), key=lambda x: x[1], reverse=True
        ):
            percentage = (
                (volume / total_fox_volume * 100) if total_fox_volume > 0 else 0
            )
            print(f"   {affiliate:15s}: {volume:10.2f} ({percentage:5.1f}%)")

    print(f"\n📈 SUMMARY:")
    print("-" * 30)
    print(f"Total unique pairs: {len(pairs)}")
    print(f"Total volume: {total_volume:.2f}")
    print(f"Total affiliates: {len(affiliates)}")


if __name__ == "__main__":
    main()
