#!/usr/bin/env python3
"""
Setup script for ButterSwap Web Scraper
Installs required dependencies and sets up the environment.
"""

import subprocess
import sys
import os

def install_dependencies():
    """Install required Python packages"""
    print("🔧 Installing ButterSwap Web Scraper dependencies...")
    
    requirements = [
        "selenium>=4.15.0",
        "pyperclip>=1.8.0",
        "web3>=6.11.0",
        "eth-abi>=4.2.0",
        "requests>=2.31.0"
    ]
    
    for package in requirements:
        try:
            print(f"   Installing {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"   ✅ {package} installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"   ❌ Failed to install {package}: {e}")
            return False
    
    return True

def check_chrome():
    """Check if Chrome browser is available"""
    print("\n🌐 Checking Chrome browser...")
    
    # Check for Chrome on macOS
    chrome_paths = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium"
    ]
    
    chrome_found = False
    for path in chrome_paths:
        if os.path.exists(path):
            print(f"   ✅ Chrome found at: {path}")
            chrome_found = True
            break
    
    if not chrome_found:
        print("   ⚠️  Chrome not found in standard locations")
        print("   💡 Please ensure Chrome is installed")
    
    return chrome_found

def create_directories():
    """Create necessary directories"""
    print("\n📁 Creating directories...")
    
    dirs = ["databases", "logs"]
    for dir_name in dirs:
        os.makedirs(dir_name, exist_ok=True)
        print(f"   ✅ Created {dir_name}/ directory")
    
    return True

def main():
    """Main setup function"""
    print("🚀 ButterSwap Web Scraper Setup")
    print("=" * 40)
    
    # Install dependencies
    if not install_dependencies():
        print("\n❌ Setup failed during dependency installation")
        return False
    
    # Check Chrome
    check_chrome()
    
    # Create directories
    if not create_directories():
        print("\n❌ Setup failed during directory creation")
        return False
    
    print("\n✅ Setup completed successfully!")
    print("\n💡 Next steps:")
    print("   1. Test the scraper: python test_butterswap_scraper.py")
    print("   2. Run the demo: python demo_butterswap_scraper.py")
    print("   3. Start scraping: python butterswap_web_scraper.py --chains ethereum --max-tx 50")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
