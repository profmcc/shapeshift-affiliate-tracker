#!/usr/bin/env python3
"""
Chainflip API Explorer
Explores the Chainflip API to find the correct endpoints for querying broker information
"""

import requests
import json
import time
from typing import Dict, List, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class ChainflipAPIExplorer:
    def __init__(self):
        """Initialize the Chainflip API explorer"""
        self.api_base_url = "https://api.chainflip.io"
        
        # ShapeShift affiliate addresses on Chainflip
        self.shapeshift_brokers = [
            'cFMeDPtPHccVYdBSJKTtCYuy7rewFNpro3xZBKaCGbSS2xhRi',
            'cFK6mYjpajcwPDZ7JUsac8XUoVSJnhjL43ZMZW7YoN8HE4dD8'
        ]
    
    def test_basic_endpoints(self):
        """Test basic API endpoints"""
        logger.info("🔧 Testing basic API endpoints...")
        
        basic_endpoints = [
            "/",
            "/health",
            "/status",
            "/info",
            "/version",
            "/docs",
            "/swagger",
            "/openapi"
        ]
        
        for endpoint in basic_endpoints:
            try:
                response = requests.get(f"{self.api_base_url}{endpoint}", timeout=10)
                logger.info(f"{endpoint}: {response.status_code} - {len(response.text)} chars")
                
                if response.status_code == 200 and len(response.text) < 1000:
                    try:
                        data = response.json()
                        logger.info(f"  JSON response: {json.dumps(data, indent=2)}")
                    except:
                        logger.info(f"  Text response: {response.text[:200]}...")
                        
            except Exception as e:
                logger.error(f"{endpoint}: Error - {e}")
    
    def test_chainflip_specific_endpoints(self):
        """Test Chainflip-specific endpoints"""
        logger.info("\n🔧 Testing Chainflip-specific endpoints...")
        
        # Try different endpoint patterns
        endpoints = [
            "/api/v1/health",
            "/api/v1/status",
            "/api/v1/brokers",
            "/api/v1/swaps",
            "/api/v1/transactions",
            "/api/v1/assets",
            "/api/v1/chains",
            "/v1/health",
            "/v1/status",
            "/v1/brokers",
            "/v1/swaps",
            "/v1/transactions",
            "/v1/assets",
            "/v1/chains",
            "/broker",
            "/swap",
            "/transaction",
            "/asset",
            "/chain"
        ]
        
        for endpoint in endpoints:
            try:
                response = requests.get(f"{self.api_base_url}{endpoint}", timeout=10)
                logger.info(f"{endpoint}: {response.status_code}")
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        logger.info(f"  ✅ Success: {json.dumps(data, indent=2)}")
                    except:
                        logger.info(f"  ✅ Success (non-JSON): {response.text[:200]}...")
                        
            except Exception as e:
                logger.error(f"{endpoint}: Error - {e}")
    
    def test_broker_endpoints(self):
        """Test broker-specific endpoints"""
        logger.info("\n🔧 Testing broker-specific endpoints...")
        
        for broker_address in self.shapeshift_brokers:
            logger.info(f"\n🔍 Testing endpoints for broker: {broker_address}")
            
            # Try different broker endpoint patterns
            broker_endpoints = [
                f"/broker/{broker_address}",
                f"/brokers/{broker_address}",
                f"/api/v1/broker/{broker_address}",
                f"/api/v1/brokers/{broker_address}",
                f"/v1/broker/{broker_address}",
                f"/v1/brokers/{broker_address}",
                f"/broker/{broker_address}/info",
                f"/broker/{broker_address}/balance",
                f"/broker/{broker_address}/swaps",
                f"/broker/{broker_address}/transactions",
                f"/brokers/{broker_address}/info",
                f"/brokers/{broker_address}/balance",
                f"/brokers/{broker_address}/swaps",
                f"/brokers/{broker_address}/transactions"
            ]
            
            for endpoint in broker_endpoints:
                try:
                    response = requests.get(f"{self.api_base_url}{endpoint}", timeout=10)
                    logger.info(f"  {endpoint}: {response.status_code}")
                    
                    if response.status_code == 200:
                        try:
                            data = response.json()
                            logger.info(f"    ✅ Success: {json.dumps(data, indent=2)}")
                        except:
                            logger.info(f"    ✅ Success (non-JSON): {response.text[:200]}...")
                    elif response.status_code == 404:
                        logger.info(f"    ⚠️ Not found")
                    else:
                        logger.info(f"    ⚠️ Status: {response.status_code}")
                        
                except Exception as e:
                    logger.error(f"    ❌ Error: {e}")
    
    def test_swap_endpoints(self):
        """Test swap-related endpoints"""
        logger.info("\n🔧 Testing swap-related endpoints...")
        
        swap_endpoints = [
            "/swaps",
            "/api/v1/swaps",
            "/v1/swaps",
            "/swap",
            "/api/v1/swap",
            "/v1/swap",
            "/recent-swaps",
            "/api/v1/recent-swaps",
            "/v1/recent-swaps"
        ]
        
        for endpoint in swap_endpoints:
            try:
                response = requests.get(f"{self.api_base_url}{endpoint}", timeout=10)
                logger.info(f"{endpoint}: {response.status_code}")
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        logger.info(f"  ✅ Success: {json.dumps(data, indent=2)}")
                    except:
                        logger.info(f"  ✅ Success (non-JSON): {response.text[:200]}...")
                        
            except Exception as e:
                logger.error(f"{endpoint}: Error - {e}")
    
    def test_alternative_apis(self):
        """Test alternative Chainflip API endpoints"""
        logger.info("\n🔧 Testing alternative Chainflip APIs...")
        
        # Try different Chainflip API domains
        alternative_apis = [
            "https://api.chainflip.io",
            "https://api.chainflip.network",
            "https://api.chainflip.com",
            "https://chainflip.io/api",
            "https://chainflip.network/api",
            "https://chainflip.com/api",
            "https://indexer.chainflip.io",
            "https://indexer.chainflip.network",
            "https://indexer.chainflip.com"
        ]
        
        for api_url in alternative_apis:
            try:
                logger.info(f"\n🔍 Testing: {api_url}")
                
                # Test health endpoint
                response = requests.get(f"{api_url}/health", timeout=10)
                logger.info(f"  /health: {response.status_code}")
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        logger.info(f"    ✅ Health check: {json.dumps(data, indent=2)}")
                    except:
                        logger.info(f"    ✅ Health check (non-JSON): {response.text[:200]}...")
                
                # Test basic info
                response = requests.get(f"{api_url}/", timeout=10)
                logger.info(f"  /: {response.status_code}")
                
                if response.status_code == 200:
                    logger.info(f"    ✅ Root response: {response.text[:200]}...")
                        
            except Exception as e:
                logger.error(f"  ❌ Error: {e}")
    
    def search_for_broker_data(self):
        """Search for broker data using different approaches"""
        logger.info("\n🔧 Searching for broker data...")
        
        # Try to find any data that might contain broker information
        search_endpoints = [
            "/search",
            "/api/v1/search",
            "/v1/search",
            "/query",
            "/api/v1/query",
            "/v1/query",
            "/data",
            "/api/v1/data",
            "/v1/data"
        ]
        
        for endpoint in search_endpoints:
            try:
                # Try with different query parameters
                params_list = [
                    {"q": "broker"},
                    {"q": "cFMeDPtPHccVYdBSJKTtCYuy7rewFNpro3xZBKaCGbSS2xhRi"},
                    {"type": "broker"},
                    {"category": "broker"},
                    {"search": "broker"}
                ]
                
                for params in params_list:
                    response = requests.get(f"{self.api_base_url}{endpoint}", params=params, timeout=10)
                    logger.info(f"{endpoint} with {params}: {response.status_code}")
                    
                    if response.status_code == 200:
                        try:
                            data = response.json()
                            logger.info(f"  ✅ Success: {json.dumps(data, indent=2)}")
                        except:
                            logger.info(f"  ✅ Success (non-JSON): {response.text[:200]}...")
                            
            except Exception as e:
                logger.error(f"{endpoint}: Error - {e}")
    
    def run_exploration(self):
        """Run the complete API exploration"""
        logger.info("🚀 Starting Chainflip API exploration...")
        
        # Test basic endpoints
        self.test_basic_endpoints()
        
        # Test Chainflip-specific endpoints
        self.test_chainflip_specific_endpoints()
        
        # Test broker endpoints
        self.test_broker_endpoints()
        
        # Test swap endpoints
        self.test_swap_endpoints()
        
        # Test alternative APIs
        self.test_alternative_apis()
        
        # Search for broker data
        self.search_for_broker_data()
        
        logger.info("\n✅ API exploration completed!")

def main():
    """Main function"""
    explorer = ChainflipAPIExplorer()
    explorer.run_exploration()

if __name__ == "__main__":
    main()


