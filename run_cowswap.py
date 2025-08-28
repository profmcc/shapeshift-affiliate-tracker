#!/usr/bin/env python3
"""
CoW Swap Listener Launcher Script
Run this to easily start the listener with common options
"""

import os
import sys
import subprocess

def main():
    """Main launcher function."""
    print("🚀 CoW Swap Affiliate Listener")
    print("================================")
    print("")
    
    # Check if Python script exists
    if not os.path.exists("cowswap_listener.py"):
        print("❌ Error: cowswap_listener.py not found!")
        print("   Make sure you're in the right directory")
        return
    
    # Check if .env exists
    if not os.path.exists(".env"):
        print("⚠️  Warning: .env file not found!")
        print("   You may need to set up your API keys")
        print("")
    
    print("📋 Available Commands:")
    print("  1. Test connection")
    print("  2. Scan recent blocks")
    print("  3. Scan specific block range")
    print("  4. Find specific transaction")
    print("  5. Download all CoW transactions")
    print("  6. Custom command")
    print("  7. Show help")
    print("")
    
    try:
        choice = input("Choose option (1-7): ").strip()
        
        if choice == "1":
            print("🧪 Testing connection...")
            subprocess.run([sys.executable, "cowswap_listener.py", "--test-connection"])
            
        elif choice == "2":
            blocks = input("How many blocks to scan? (default: 200): ").strip()
            blocks = blocks if blocks else "200"
            print(f"🔍 Scanning last {blocks} blocks...")
            subprocess.run([sys.executable, "cowswap_listener.py", "--max-blocks", blocks])
            
        elif choice == "3":
            start_block = input("Start block: ").strip()
            end_block = input("End block: ").strip()
            print(f"🔍 Scanning blocks {start_block} to {end_block}...")
            subprocess.run([sys.executable, "cowswap_listener.py", "--block-range", start_block, end_block])
            
        elif choice == "4":
            tx_hash = input("Transaction hash: ").strip()
            print(f"🔍 Finding transaction {tx_hash}...")
            subprocess.run([sys.executable, "cowswap_listener.py", "--find-tx", tx_hash])
            
        elif choice == "5":
            blocks = input("How many blocks to scan? (default: 100): ").strip()
            blocks = blocks if blocks else "100"
            print(f"🔍 Downloading all CoW transactions from last {blocks} blocks...")
            subprocess.run([sys.executable, "cowswap_listener.py", "--any-affiliate", "--max-blocks", blocks])
            
        elif choice == "6":
            custom_cmd = input("Enter custom command (e.g., --test-connection --check-contracts): ").strip()
            print(f"🔍 Running: python cowswap_listener.py {custom_cmd}")
            cmd_parts = custom_cmd.split()
            subprocess.run([sys.executable, "cowswap_listener.py"] + cmd_parts)
            
        elif choice == "7":
            print("📖 Help:")
            print("")
            subprocess.run([sys.executable, "cowswap_listener.py", "--help"])
            
        else:
            print("❌ Invalid option. Exiting.")
            return
            
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        return
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    print("")
    print("✅ Command completed!")
    print("📁 Check cowswap_affiliate_transactions.csv for results")

if __name__ == "__main__":
    main()


