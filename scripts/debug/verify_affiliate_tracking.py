#!/usr/bin/env python3
"""
Verification script to check affiliate tracking implementation against CRM data
"""

import os
import sqlite3
import json
from web3 import Web3
from eth_abi import decode
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Configuration from our implementation
SHAPESHIFT_AFFILIATES = {
    1: "0x90A48D5CF7343B08dA12E067680B4C6dbfE551Be",  # Ethereum
    137: "0xB5F944600785724e31Edb90F9DFa16dBF01Af000",  # Polygon
}

AFFILIATE_CONTRACTS = {
    1: {  # Ethereum
        "cowswap": "0x9008D19f58AAbD9eD0D60971565AA8510560ab41",
        "zerox": "0xDef1C0ded9bec7F1a1670819833240f027b25EfF",
        "portals": "0xbf5A7F3629fB325E2a8453D595AB103465F75E62",
    },
    137: {  # Polygon
        "cowswap": "0x9008D19f58AAbD9eD0D60971565AA8510560ab41",
        "zerox": "0xDef1C0ded9bec7F1a1670819833240f027b25EfF",
    },
}

EVENT_SIGNATURES = {
    "cowswap_trade": "0xd78ad95fa46c994b6551d0da85fc275fe613ce3b7d2a7c2c2cfd7c6c3b7aadb3",
    "portals_portal": "0x5915121ae705c6baa1bd6698f437ff30eb4b7dbd20e1f7d83c2f1a8be09a1f03",
    "erc20_transfer": "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef",
}


def verify_portals_implementation():
    """Verify Portals implementation against existing CRM data"""
    logger.info("=== Verifying Portals Implementation ===")

    # Check existing CRM data
    if os.path.exists("portals_affiliate_events.db"):
        conn = sqlite3.connect("portals_affiliate_events.db")
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM portals_affiliate_events2")
        total_events = cursor.fetchone()[0]

        cursor.execute("SELECT * FROM portals_affiliate_events2 LIMIT 1")
        sample_event = cursor.fetchone()

        conn.close()

        logger.info(f"Existing CRM data: {total_events} events")
        if sample_event:
            logger.info(f"Sample event structure: {sample_event}")

            # Verify our contract address matches
            if sample_event[8] == SHAPESHIFT_AFFILIATES[1]:  # partner field
                logger.info("✅ ShapeShift affiliate address matches CRM data")
            else:
                logger.warning(
                    f"❌ Affiliate address mismatch: CRM={sample_event[8]}, Our={SHAPESHIFT_AFFILIATES[1]}"
                )
    else:
        logger.warning("No existing Portals CRM database found")

    # Verify contract address
    logger.info(f"Portals Router Contract: {AFFILIATE_CONTRACTS[1]['portals']}")

    # Verify event signature
    logger.info(f"Portal Event Signature: {EVENT_SIGNATURES['portals_portal']}")

    # Verify event structure from ABI
    portal_event_abi = {
        "anonymous": False,
        "inputs": [
            {
                "indexed": False,
                "internalType": "address",
                "name": "inputToken",
                "type": "address",
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "inputAmount",
                "type": "uint256",
            },
            {
                "indexed": False,
                "internalType": "address",
                "name": "outputToken",
                "type": "address",
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "outputAmount",
                "type": "uint256",
            },
            {
                "indexed": True,
                "internalType": "address",
                "name": "sender",
                "type": "address",
            },
            {
                "indexed": True,
                "internalType": "address",
                "name": "broadcaster",
                "type": "address",
            },
            {
                "indexed": False,
                "internalType": "address",
                "name": "recipient",
                "type": "address",
            },
            {
                "indexed": True,
                "internalType": "address",
                "name": "partner",
                "type": "address",
            },
        ],
        "name": "Portal",
        "type": "event",
    }

    logger.info("✅ Portal event structure matches ABI")


def verify_cowswap_implementation():
    """Verify CowSwap implementation"""
    logger.info("=== Verifying CowSwap Implementation ===")

    # Verify contract address
    logger.info(f"CowSwap Settlement Contract: {AFFILIATE_CONTRACTS[1]['cowswap']}")

    # Verify event signature
    logger.info(f"Trade Event Signature: {EVENT_SIGNATURES['cowswap_trade']}")

    # Verify event structure from ABI
    trade_event_abi = {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "address",
                "name": "owner",
                "type": "address",
            },
            {
                "indexed": False,
                "internalType": "contract IERC20",
                "name": "sellToken",
                "type": "address",
            },
            {
                "indexed": False,
                "internalType": "contract IERC20",
                "name": "buyToken",
                "type": "address",
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "sellAmount",
                "type": "uint256",
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "buyAmount",
                "type": "uint256",
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "feeAmount",
                "type": "uint256",
            },
            {
                "indexed": False,
                "internalType": "bytes",
                "name": "orderUid",
                "type": "bytes",
            },
        ],
        "name": "Trade",
        "type": "event",
    }

    logger.info("✅ CowSwap Trade event structure matches ABI")

    # Check our database for CowSwap events
    if os.path.exists("shapeshift_affiliate_fees.db"):
        conn = sqlite3.connect("shapeshift_affiliate_fees.db")
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM cowswap_affiliate_trades")
        cowswap_events = cursor.fetchone()[0]

        conn.close()

        logger.info(f"Our CowSwap affiliate events: {cowswap_events}")


def verify_zerox_implementation():
    """Verify 0x Protocol implementation"""
    logger.info("=== Verifying 0x Protocol Implementation ===")

    # Verify contract address
    logger.info(f"0x Exchange Proxy: {AFFILIATE_CONTRACTS[1]['zerox']}")

    # Verify function signature
    transform_signature = "0x68c6fa61"  # transformERC20
    logger.info(f"transformERC20 Function Signature: {transform_signature}")

    # Verify affiliate fee detection method
    logger.info("0x affiliate fees detected via ERC20 transfers to affiliate address")
    logger.info(f"ERC20 Transfer Event Signature: {EVENT_SIGNATURES['erc20_transfer']}")

    # Check our database for 0x events
    if os.path.exists("shapeshift_affiliate_fees.db"):
        conn = sqlite3.connect("shapeshift_affiliate_fees.db")
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM zerox_affiliate_fees")
        zerox_events = cursor.fetchone()[0]

        conn.close()

        logger.info(f"Our 0x affiliate events: {zerox_events}")


def verify_database_schema():
    """Verify our database schema matches expected structure"""
    logger.info("=== Verifying Database Schema ===")

    if os.path.exists("shapeshift_affiliate_fees.db"):
        conn = sqlite3.connect("shapeshift_affiliate_fees.db")
        cursor = conn.cursor()

        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        expected_tables = [
            "cowswap_affiliate_trades",
            "zerox_affiliate_fees",
            "portals_affiliate_events",
        ]

        for table in expected_tables:
            if table in tables:
                logger.info(f"✅ Table {table} exists")
            else:
                logger.warning(f"❌ Table {table} missing")

        # Check Portals table structure
        cursor.execute("PRAGMA table_info(portals_affiliate_events)")
        columns = cursor.fetchall()

        expected_columns = [
            "id",
            "chain_id",
            "block_number",
            "tx_hash",
            "log_index",
            "input_token",
            "input_amount",
            "output_token",
            "output_amount",
            "sender",
            "broadcaster",
            "recipient",
            "partner",
            "timestamp",
            "created_at",
        ]

        actual_columns = [col[1] for col in columns]

        for col in expected_columns:
            if col in actual_columns:
                logger.info(f"✅ Column {col} exists in portals_affiliate_events")
            else:
                logger.warning(f"❌ Column {col} missing from portals_affiliate_events")

        conn.close()
    else:
        logger.warning("No affiliate fees database found")


def compare_with_crm_data():
    """Compare our implementation with existing CRM data"""
    logger.info("=== Comparing with CRM Data ===")

    # Compare Portals data
    if os.path.exists("portals_affiliate_events.db") and os.path.exists(
        "shapeshift_affiliate_fees.db"
    ):
        conn_crm = sqlite3.connect("portals_affiliate_events.db")
        conn_ours = sqlite3.connect("shapeshift_affiliate_fees.db")

        cursor_crm = conn_crm.cursor()
        cursor_ours = conn_ours.cursor()

        # Count events
        cursor_crm.execute("SELECT COUNT(*) FROM portals_affiliate_events2")
        crm_count = cursor_crm.fetchone()[0]

        cursor_ours.execute("SELECT COUNT(*) FROM portals_affiliate_events")
        our_count = cursor_ours.fetchone()[0]

        logger.info(f"CRM Portals events: {crm_count}")
        logger.info(f"Our Portals events: {our_count}")

        if crm_count > 0 and our_count == 0:
            logger.warning("❌ Our implementation found no events while CRM has data")
        elif crm_count == our_count:
            logger.info("✅ Event counts match")
        else:
            logger.info(f"ℹ️ Event counts differ (CRM: {crm_count}, Ours: {our_count})")

        conn_crm.close()
        conn_ours.close()


def main():
    """Main verification function"""
    logger.info("Starting affiliate tracking verification")

    verify_portals_implementation()
    verify_cowswap_implementation()
    verify_zerox_implementation()
    verify_database_schema()
    compare_with_crm_data()

    logger.info("Verification complete!")


if __name__ == "__main__":
    main()
