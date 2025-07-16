#!/usr/bin/env python3
"""
Setup script for Chainflip Scraper

Installs required dependencies and sets up the environment.
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(command: str, description: str):
    """Run a command and handle errors."""
    print(f"\n{description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"Error: {e.stderr}")
        return False


def main():
    """Main setup function."""
    print("🚀 Setting up Chainflip Scraper...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    
    # Install pip dependencies
    dependencies = [
        "playwright==1.42.0",
        "beautifulsoup4==4.12.3", 
        "pandas==2.1.4",
        "typing-extensions==4.8.0"
    ]
    
    for dep in dependencies:
        if not run_command(f"pip install {dep}", f"Installing {dep}"):
            print(f"❌ Failed to install {dep}")
            sys.exit(1)
    
    # Install Playwright browsers
    if not run_command("playwright install chromium", "Installing Playwright Chromium browser"):
        print("❌ Failed to install Playwright browser")
        sys.exit(1)
    
    print("\n🎉 Setup completed successfully!")
    print("\nTo run the scraper:")
    print("  python chainflip_scraper.py")
    print("  python chainflip_scraper_enhanced.py")
    
    print("\nThe scraper will:")
    print("  - Load the Chainflip broker page")
    print("  - Extract the swaps table")
    print("  - Capture full 0x addresses from tooltips")
    print("  - Save data to CSV and JSON files")


if __name__ == "__main__":
    main() 