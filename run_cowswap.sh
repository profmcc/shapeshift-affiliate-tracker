#!/bin/bash

# CoW Swap Listener Launcher Script
# Run this to easily start the listener with common options

echo "🚀 CoW Swap Affiliate Listener"
echo "================================"
echo ""

# Check if Python script exists
if [ ! -f "cowswap_listener.py" ]; then
    echo "❌ Error: cowswap_listener.py not found!"
    echo "   Make sure you're in the right directory"
    exit 1
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found!"
    echo "   You may need to set up your API keys"
    echo ""
fi

echo "📋 Available Commands:"
echo "  1. Test connection"
echo "  2. Scan recent blocks"
echo "  3. Scan specific block range"
echo "  4. Find specific transaction"
echo "  5. Download all CoW transactions"
echo "  6. Custom command"
echo ""

read -p "Choose option (1-6): " choice

case $choice in
    1)
        echo "🧪 Testing connection..."
        python cowswap_listener.py --test-connection
        ;;
    2)
        read -p "How many blocks to scan? (default: 200): " blocks
        blocks=${blocks:-200}
        echo "🔍 Scanning last $blocks blocks..."
        python cowswap_listener.py --max-blocks $blocks
        ;;
    3)
        read -p "Start block: " start_block
        read -p "End block: " end_block
        echo "🔍 Scanning blocks $start_block to $end_block..."
        python cowswap_listener.py --block-range $start_block $end_block
        ;;
    4)
        read -p "Transaction hash: " tx_hash
        echo "🔍 Finding transaction $tx_hash..."
        python cowswap_listener.py --find-tx $tx_hash
        ;;
    5)
        read -p "How many blocks to scan? (default: 100): " blocks
        blocks=${blocks:-100}
        echo "🔍 Downloading all CoW transactions from last $blocks blocks..."
        python cowswap_listener.py --any-affiliate --max-blocks $blocks
        ;;
    6)
        echo "💻 Enter custom command (e.g., --test-connection --check-contracts):"
        read -p "Command: " custom_cmd
        echo "🔍 Running: python cowswap_listener.py $custom_cmd"
        python cowswap_listener.py $custom_cmd
        ;;
    *)
        echo "❌ Invalid option. Exiting."
        exit 1
        ;;
esac

echo ""
echo "✅ Command completed!"
echo "📁 Check cowswap_affiliate_transactions.csv for results"


