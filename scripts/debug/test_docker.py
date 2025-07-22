#!/usr/bin/env python3
"""
Simple test script to verify Docker environment
"""

import os
import sys
import time
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/test.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

def main():
    logging.info("=== Docker Environment Test ===")
    logging.info(f"Python version: {sys.version}")
    logging.info(f"Working directory: {os.getcwd()}")
    logging.info(f"Files in current directory: {len(os.listdir('.'))}")
    
    # Check environment variables
    logging.info("Environment variables:")
    for key, value in os.environ.items():
        if 'API' in key.upper() or 'RPC' in key.upper() or 'KEY' in key.upper():
            logging.info(f"  {key}: {value[:10]}..." if len(value) > 10 else f"  {key}: {value}")
    
    # Test database access
    try:
        import sqlite3
        db_path = 'shapeshift_affiliate_fees_comprehensive.db'
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            logging.info(f"Database tables: {[table[0] for table in tables]}")
            conn.close()
        else:
            logging.warning(f"Database file {db_path} not found")
    except Exception as e:
        logging.error(f"Database test failed: {e}")
    
    # Test web3 import
    try:
        import web3
        logging.info(f"Web3 version: {web3.__version__}")
    except ImportError as e:
        logging.error(f"Web3 import failed: {e}")
    
    logging.info("=== Test completed ===")
    
    # Keep running for a bit to see logs
    for i in range(10):
        logging.info(f"Test iteration {i+1}/10")
        time.sleep(1)

if __name__ == "__main__":
    main() 