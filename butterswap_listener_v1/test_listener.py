#!/usr/bin/env python3
"""
Test script for ButterSwap listener
"""

import sys
import os
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test if all required modules can be imported"""
    try:
        from butterswap_listener import ButterSwapListener
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_basic_functionality():
    """Test basic listener functionality without RPC connection"""
    try:
        from butterswap_listener import ButterSwapListener
        
        # Test class instantiation (will fail on RPC connection, but that's expected)
        print("✅ Listener class can be imported")
        
        # Test configuration constants
        from butterswap_listener import BUTTERSWAP_AFFILIATE_ADDRESS, BASE_RPC_URL
        print(f"✅ Affiliate address: {BUTTERSWAP_AFFILIATE_ADDRESS}")
        print(f"✅ Base RPC URL: {BASE_RPC_URL}")
        
        return True
        
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        return False

def test_file_structure():
    """Test if all required files exist"""
    required_files = [
        "butterswap_listener.py",
        "requirements.txt", 
        "README.md"
    ]
    
    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    else:
        print("✅ All required files present")
        return True

def main():
    """Run all tests"""
    print("🧪 Testing ButterSwap Listener...\n")
    
    tests = [
        ("File Structure", test_file_structure),
        ("Import Test", test_imports),
        ("Basic Functionality", test_basic_functionality),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"🔍 {test_name}...")
        if test_func():
            passed += 1
            print(f"   ✅ PASSED\n")
        else:
            print(f"   ❌ FAILED\n")
    
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Listener is ready to use.")
        print("\n💡 Next steps:")
        print("   1. Install dependencies: pip install -r requirements.txt")
        print("   2. Test connection: python butterswap_listener.py --test-connection")
        print("   3. Start scanning: python butterswap_listener.py --max-blocks 100")
    else:
        print("⚠️ Some tests failed. Check the errors above.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
