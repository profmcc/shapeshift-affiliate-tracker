#!/usr/bin/env python3
"""
Extract July 2025 Analysis Results
"""

import json


def main():
    with open("july_2025_analysis_results.json", "r") as f:
        data = json.load(f)

    analysis = data["july_2025_analysis"]
    pairs = analysis["top_pairs"]
    affiliates = analysis["affiliate_totals"]

    print("=" * 80)
    print("📊 JULY 2025 TRADE PAIR ANALYSIS")
    print("=" * 80)

    print(f"\n🏆 TOP 10 TRADE PAIRS:")
    print("-" * 50)

    # Sort pairs by volume
    sorted_pairs = sorted(pairs.items(), key=lambda x: x[1], reverse=True)

    for i, (pair, volume) in enumerate(sorted_pairs[:10], 1):
        print(f"{i:2d}. {pair:20s}: {volume:10.2f} volume")

    print(f"\n📊 AFFILIATE BREAKDOWN:")
    print("-" * 50)

    # Sort affiliates by volume
    sorted_affiliates = sorted(affiliates.items(), key=lambda x: x[1], reverse=True)

    for affiliate, volume in sorted_affiliates:
        print(f"{affiliate:20s}: {volume:10.2f} volume")

    # Check for FOX pairs specifically
    fox_pairs = {k: v for k, v in pairs.items() if "FOX" in k}

    if fox_pairs:
        print(f"\n🦊 FOX TRADE PAIRS:")
        print("-" * 30)
        for pair, volume in sorted(fox_pairs.items(), key=lambda x: x[1], reverse=True):
            print(f"{pair:20s}: {volume:10.2f} volume")

    print(f"\n📈 SUMMARY:")
    print("-" * 30)
    print(f"Total unique pairs: {len(pairs)}")
    print(f"Total volume: {sum(pairs.values()):.2f}")
    print(f"Total affiliates: {len(affiliates)}")


if __name__ == "__main__":
    main()
