#!/bin/bash

# Portals Affiliate Listener - Installation Script
# This script sets up the Portals listener with all dependencies

echo "🌉 Portals Affiliate Listener - Installation Script"
echo "=================================================="

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+ first."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed. Please install pip3 first."
    exit 1
fi

echo "✅ pip3 found: $(pip3 --version)"

# Create virtual environment (optional but recommended)
echo ""
echo "🔧 Creating virtual environment..."
if [ ! -d "venv-portals" ]; then
    python3 -m venv venv-portals
    echo "✅ Virtual environment created: venv-portals"
else
    echo "ℹ️ Virtual environment already exists: venv-portals"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv-portals/bin/activate

# Upgrade pip
echo "🔧 Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "🔧 Installing dependencies..."
pip install -r requirements_portals.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo ""
    echo "⚠️  No .env file found!"
    echo "🔑 You need to create a .env file with your API key:"
    echo ""
    echo "   # Option 1: Alchemy (Recommended)"
    echo "   ALCHEMY_API_KEY=your_alchemy_api_key_here"
    echo ""
    echo "   # Option 2: Infura"
    echo "   INFURA_API_KEY=your_infura_api_key_here"
    echo ""
    echo "📝 Create .env file and add your API key, then run:"
    echo "   python portals_listener.py --test-connection"
else
    echo "✅ .env file found"
    echo ""
    echo "🔍 Checking API keys..."
    if grep -q "ALCHEMY_API_KEY" .env || grep -q "INFURA_API_KEY" .env; then
        echo "✅ API keys found in .env"
        echo ""
        echo "🧪 Testing connection..."
        python portals_listener.py --test-connection
    else
        echo "⚠️  .env file exists but no API keys found"
        echo "🔑 Add ALCHEMY_API_KEY or INFURA_API_KEY to your .env file"
    fi
fi

echo ""
echo "🎉 Installation complete!"
echo ""
echo "📚 Next steps:"
echo "1. Get API key from Alchemy (alchemy.com) or Infura (infura.io)"
echo "2. Create .env file with your API key"
echo "3. Test connection: python portals_listener.py --test-connection"
echo "4. Check affiliate addresses: python portals_listener.py --check-addresses"
echo "5. Start scanning: python portals_listener.py --max-blocks 200"
echo ""
echo "📖 Read README_PORTALS.md for detailed usage instructions"
echo ""
echo "🔧 To activate virtual environment in future:"
echo "   source venv-portals/bin/activate"

