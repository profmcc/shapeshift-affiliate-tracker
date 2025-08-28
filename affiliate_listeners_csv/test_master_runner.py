#!/usr/bin/env python3
"""
Test Master Runner - Runs all test listeners sequentially
Collects real transactions from all protocols to verify functionality
"""

import os
import sys
import time
import logging
import subprocess
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestMasterRunner:
    def __init__(self):
        self.test_listeners = [
            'test_chainflip_listener.py',
            'test_cowswap_listener.py', 
            'test_portals_listener.py',
            'test_butterswap_listener.py'
        ]
        
        self.csv_files = [
            'csv_data/test_chainflip_transactions.csv',
            'csv_data/test_cowswap_transactions.csv',
            'csv_data/test_portals_transactions.csv',
            'csv_data/test_butterswap_transactions.csv'
        ]
        
        self.results = {}
    
    def run_test_listener(self, listener_name: str) -> dict:
        """Run a single test listener and return results"""
        logger.info(f"🔄 Running {listener_name}...")
        
        start_time = time.time()
        result = {
            'listener': listener_name,
            'start_time': start_time,
            'success': False,
            'transactions_found': 0,
            'error': None,
            'execution_time': 0
        }
        
        try:
            # Run the listener with appropriate arguments
            if 'chainflip' in listener_name:
                cmd = ['python', f'affiliate_listeners_csv/{listener_name}', '--hours', '24', '--max-swaps', '100']
            else:
                cmd = ['python', f'affiliate_listeners_csv/{listener_name}', '--blocks', '1000']
            
            # Run with timeout
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                cwd=os.getcwd()
            )
            
            execution_time = time.time() - start_time
            result['execution_time'] = execution_time
            
            if process.returncode == 0:
                result['success'] = True
                logger.info(f"✅ {listener_name} completed successfully in {execution_time:.2f}s")
                
                # Count transactions in CSV - extract protocol name from listener filename
                protocol_name = listener_name.replace('test_', '').replace('_listener.py', '')
                csv_file = f"csv_data/test_{protocol_name}_transactions.csv"
                if os.path.exists(csv_file):
                    with open(csv_file, 'r') as f:
                        lines = f.readlines()
                        # Subtract 1 for header
                        result['transactions_found'] = max(0, len(lines) - 1)
                        logger.info(f"📊 Found {result['transactions_found']} transactions in {csv_file}")
                else:
                    logger.warning(f"⚠️ CSV file {csv_file} not found")
                    
            else:
                result['error'] = f"Process failed with return code {process.returncode}"
                logger.error(f"❌ {listener_name} failed: {result['error']}")
                if process.stderr:
                    logger.error(f"Stderr: {process.stderr}")
                    
        except subprocess.TimeoutExpired:
            result['error'] = "Process timed out after 5 minutes"
            logger.error(f"⏰ {listener_name} timed out")
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"💥 {listener_name} crashed: {e}")
        
        return result
    
    def check_csv_files(self) -> dict:
        """Check the status of all CSV files"""
        csv_status = {}
        
        for csv_file in self.csv_files:
            status = {
                'exists': False,
                'size_bytes': 0,
                'line_count': 0,
                'has_data': False
            }
            
            if os.path.exists(csv_file):
                status['exists'] = True
                status['size_bytes'] = os.path.getsize(csv_file)
                
                with open(csv_file, 'r') as f:
                    lines = f.readlines()
                    status['line_count'] = len(lines)
                    status['has_data'] = len(lines) > 1  # More than just header
                    
                    if status['has_data']:
                        # Show sample data
                        sample_lines = lines[1:min(3, len(lines))]  # First 2 data rows
                        status['sample_data'] = [line.strip() for line in sample_lines]
            
            csv_status[csv_file] = status
        
        return csv_status
    
    def generate_summary_report(self) -> str:
        """Generate a summary report of all test results"""
        report = []
        report.append("=" * 80)
        report.append("TEST MASTER RUNNER SUMMARY REPORT")
        report.append("=" * 80)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Test Results Summary
        report.append("TEST RESULTS SUMMARY:")
        report.append("-" * 40)
        
        total_success = sum(1 for r in self.results.values() if r['success'])
        total_transactions = sum(r['transactions_found'] for r in self.results.values())
        
        for listener_name, result in self.results.items():
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            report.append(f"{listener_name}: {status}")
            if result['success']:
                report.append(f"  - Transactions: {result['transactions_found']}")
                report.append(f"  - Execution time: {result['execution_time']:.2f}s")
            else:
                report.append(f"  - Error: {result['error']}")
        
        report.append("")
        report.append(f"Overall: {total_success}/{len(self.results)} listeners passed")
        report.append(f"Total transactions collected: {total_transactions}")
        report.append("")
        
        # CSV Files Status
        report.append("CSV FILES STATUS:")
        report.append("-" * 40)
        
        csv_status = self.check_csv_files()
        for csv_file, status in csv_status.items():
            file_name = os.path.basename(csv_file)
            if status['exists']:
                report.append(f"{file_name}: ✅ {status['line_count']} lines, {status['size_bytes']} bytes")
                if status['has_data']:
                    report.append(f"  Sample data:")
                    for i, sample in enumerate(status.get('sample_data', [])[:2]):
                        report.append(f"    {i+1}. {sample[:100]}...")
            else:
                report.append(f"{file_name}: ❌ File not found")
        
        report.append("")
        
        # Recommendations
        report.append("RECOMMENDATIONS:")
        report.append("-" * 40)
        
        if total_success == len(self.results):
            report.append("🎉 All test listeners are working correctly!")
            report.append("✅ Ready for production use")
        else:
            failed_listeners = [name for name, result in self.results.items() if not result['success']]
            report.append(f"⚠️ {len(failed_listeners)} listeners need attention:")
            for name in failed_listeners:
                report.append(f"  - {name}: {self.results[name]['error']}")
        
        if total_transactions == 0:
            report.append("⚠️ No transactions found - consider:")
            report.append("  - Scanning more recent blocks")
            report.append("  - Checking affiliate addresses")
            report.append("  - Verifying RPC endpoints")
        
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def run_all_tests(self):
        """Run all test listeners sequentially"""
        logger.info("🚀 Starting Test Master Runner")
        logger.info(f"Will test {len(self.test_listeners)} listeners")
        logger.info("")
        
        # Run each test listener
        for listener_name in self.test_listeners:
            result = self.run_test_listener(listener_name)
            self.results[listener_name] = result
            
            # Small delay between tests
            time.sleep(2)
        
        # Generate and display summary
        logger.info("")
        logger.info("📋 Generating summary report...")
        summary = self.generate_summary_report()
        
        # Save report to file
        report_file = f"csv_data/test_run_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w') as f:
            f.write(summary)
        
        logger.info(f"📄 Report saved to: {report_file}")
        logger.info("")
        
        # Display summary
        print(summary)
        
        return self.results

def main():
    """Main entry point"""
    runner = TestMasterRunner()
    
    try:
        results = runner.run_all_tests()
        
        # Exit with error code if any tests failed
        failed_tests = sum(1 for r in results.values() if not r['success'])
        if failed_tests > 0:
            logger.error(f"❌ {failed_tests} tests failed")
            sys.exit(1)
        else:
            logger.info("🎉 All tests completed successfully!")
            sys.exit(0)
            
    except KeyboardInterrupt:
        logger.info("⏹️ Test run interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"💥 Test master runner crashed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
