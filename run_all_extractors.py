#!/usr/bin/env python3
"""
Master Affiliate Data Extractor
Runs all platform-specific data extractors for debugging purposes
"""

import subprocess
import sys
import os

def run_extractor(platform, script_path):
    """Run a platform-specific extractor"""
    print(f"\n{'='*80}")
    print(f"RUNNING {platform.upper()} EXTRACTOR")
    print(f"{'='*80}")
    
    try:
        result = subprocess.run([sys.executable, script_path], 
                              capture_output=True, text=True, cwd=os.path.dirname(script_path))
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
    except Exception as e:
        print(f"Error running {platform} extractor: {e}")

def main():
    """Run all platform extractors"""
    
    print("AFFILIATE FEE LISTENER 2 - PLATFORM-SPECIFIC DATA EXTRACTION")
    print("=" * 80)
    
    # Define platform extractors
    extractors = [
        ("Portals", "portals/extract_portals_data.py"),
        ("0x Protocol", "0x_protocol/extract_0x_data.py"),
        ("CowSwap", "cowswap/extract_cowswap_data.py")
    ]
    
    # Run each extractor
    for platform, script_path in extractors:
        if os.path.exists(script_path):
            run_extractor(platform, script_path)
        else:
            print(f"\nWarning: {script_path} not found")
    
    print(f"\n{'='*80}")
    print("ALL EXTRACTORS COMPLETED")
    print("=" * 80)

if __name__ == "__main__":
    main() 