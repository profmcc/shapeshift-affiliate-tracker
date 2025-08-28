#!/usr/bin/env python3
"""
Simple runner script for the Relay Affiliate Fee Listener
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from relay_listener import main

if __name__ == "__main__":
    main()
