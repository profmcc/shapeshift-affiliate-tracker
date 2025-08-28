#!/bin/bash

# ButterSwap Listener Installation Script

echo "🚀 Installing ButterSwap Affiliate Transaction Listener..."
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+ first."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed. Please install pip first."
    exit 1
fi

echo "✅ pip3 found: $(pip3 --version)"

# Create virtual environment (optional)
read -p "🤔 Create virtual environment? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    echo "✅ Virtual environment activated"
fi

# Install dependencies
echo "📥 Installing dependencies..."
pip3 install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✅ Dependencies installed successfully"
else
    echo "❌ Failed to install dependencies"
    exit 1
fi

# Test the listener
echo "🧪 Testing listener..."
python3 test_listener.py

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Installation complete!"
    echo ""
    echo "💡 Next steps:"
    echo "   1. Test connection: python3 butterswap_listener.py --test-connection"
    echo "   2. Check affiliate address: python3 butterswap_listener.py --check-address"
    echo "   3. Start scanning: python3 butterswap_listener.py --max-blocks 100"
    echo ""
    echo "📚 See README.md for detailed usage instructions"
else
    echo "⚠️ Installation completed but tests failed. Check the errors above."
fi


