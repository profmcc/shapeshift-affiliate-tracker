#!/bin/bash

# Portals Affiliate Fee Tracker - Installation Script
echo "🚀 Setting up Portals Affiliate Fee Tracker..."

# Check if Python 3.8+ is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3.8+ is required but not installed."
    echo "Please install Python 3.8+ and try again."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.8"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Python $REQUIRED_VERSION+ is required, but you have Python $PYTHON_VERSION"
    exit 1
fi

echo "✅ Python $PYTHON_VERSION detected"

# Create virtual environment
echo "🔧 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "🔧 Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "🔧 Installing dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "🔧 Creating .env file..."
    cat > .env << EOF
# Portals Affiliate Fee Tracker Configuration
# Add your API keys here

# Alchemy API Key (required)
ALCHEMY_API_KEY=your_alchemy_api_key_here

# Infura API Key (optional, fallback)
INFURA_API_KEY=your_infura_api_key_here

# RPC Rate Limiting (requests per second)
RPC_RATE_LIMIT=10

# Block processing settings
BLOCK_CHUNK_SIZE=100
CONFIRMATION_BLOCKS=12
EOF
    echo "📝 Please edit .env file and add your API keys"
else
    echo "✅ .env file already exists"
fi

# Create csv_data directory if it doesn't exist
mkdir -p csv_data

# Make scripts executable
chmod +x portals
chmod +x install.sh

echo ""
echo "🎉 Installation complete!"
echo ""
echo "📋 Next steps:"
echo "1. Edit .env file and add your Alchemy API key"
echo "2. Run: python run_portals.py"
echo "3. Or use quick command: ./portals"
echo ""
echo "📚 For more information, see README.md"
echo ""
echo "🚀 Happy tracking! 🎯"
