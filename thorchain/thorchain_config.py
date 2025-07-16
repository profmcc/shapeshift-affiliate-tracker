#!/usr/bin/env python3
"""
THORChain Configuration for ShapeShift Affiliate Tracking
"""

import os

# THORChain Midgard API configuration
THORCHAIN_CONFIG = {
    'midgard_url': os.getenv('THORCHAIN_MIDGARD_URL', 'https://midgard.ninerealms.com'),
    'affiliate_address': 'thor1z8s0yk6q86nqwsc2gagv4n9yt9c0hk9qtszt0p',  # ShapeShift affiliate
    'chain_name': 'THORChain',
    'chain_id': 'thorchain',
    'supported_assets': [
        'THOR.RUNE',
        'ETH.ETH',
        'BTC.BTC',
        'BNB.BNB',
        'BSC.BUSD',
        'BSC.USDT',
        'ETH.USDC',
        'ETH.USDT',
        'AVAX.AVAX',
        'POLYGON.MATIC'
    ]
}

# THORChain affiliate fee tracking configuration
THORCHAIN_AFFILIATE_CONFIG = {
    'enabled': True,
    'polling_interval': 60,  # seconds
    'batch_size': 100,
    'max_retries': 3,
    'timeout': 30,
    'rate_limit_delay': 1,  # seconds between requests
}

# Database configuration for THORChain
THORCHAIN_DB_CONFIG = {
    'database_path': 'shapeshift_thorchain_fees.db',
    'table_name': 'thorchain_affiliate_fees',
    'backup_enabled': True,
    'backup_interval': 3600,  # 1 hour
}

# Logging configuration for THORChain
THORCHAIN_LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file': 'thorchain_listener.log',
    'max_size': 10 * 1024 * 1024,  # 10MB
    'backup_count': 5
} 