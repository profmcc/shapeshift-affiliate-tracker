#!/bin/bash

echo "🚀 Relay Affiliate Fee Listener - Quick Start"
echo "=============================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+ first."
    exit 1
fi

# Check Python version
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python $python_version is installed, but Python $required_version+ is required."
    exit 1
fi

echo "✅ Python $python_version detected"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Create data directory
echo "📁 Creating data directory..."
mkdir -p data

# Copy example environment file
if [ ! -f .env ]; then
    echo "🔑 Creating .env file from template..."
    cp env.example .env
    echo "⚠️  Please edit .env file with your API keys before running!"
fi

# Copy example config
if [ ! -f config/config.yaml ]; then
    echo "⚙️  Creating config.yaml from template..."
    cp config/config.example.yaml config/config.yaml
    echo "⚠️  Please review config.yaml and customize if needed!"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your Alchemy API key"
echo "2. Review config/config.yaml for customization"
echo "3. Run the listener: python relay_listener.py"
echo "4. Or use the quick runner: python run.py"
echo ""
echo "For help: python relay_listener.py --help"
