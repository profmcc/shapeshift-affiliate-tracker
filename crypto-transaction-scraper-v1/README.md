# Crypto Transaction Web Scraper v1

A powerful web scraper specifically designed for crypto transactions using the [Firecrawl API](https://docs.firecrawl.dev/introduction). This scraper can handle abbreviated transaction hashes and wallet addresses, extract full addresses from hover elements, and parse various crypto explorer formats.

## 🚀 Features

- **Smart Address Detection**: Automatically detects and extracts crypto addresses from various blockchain networks
- **Hover Element Extraction**: Uses Firecrawl's Actions API to interact with hover elements and extract full addresses
- **Multi-Network Support**: Supports Ethereum, Polygon, BSC, Arbitrum, Bitcoin, Solana, and more
- **Abbreviated Address Handling**: Recognizes and processes shortened address formats (e.g., `0x1234...5678`)
- **Transaction Data Extraction**: Extracts transaction details like hash, block number, amount, gas fees, and status
- **Batch Processing**: Process multiple URLs with rate limiting and error handling
- **Flexible Output**: Save results in JSON format with comprehensive metadata

## 🛠️ Installation

### Prerequisites

- Python 3.8 or higher
- Firecrawl API key ([Get one here](https://firecrawl.dev))

### Setup

1. **Clone or download the scraper files**
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set your Firecrawl API key**:
   ```bash
   export FIRECRAWL_API_KEY="fc-YOUR-API-KEY"
   ```
   
   Or create a `.env` file:
   ```bash
   echo "FIRECRAWL_API_KEY=fc-YOUR-API-KEY" > .env
   ```

## 📖 Usage

### Command Line Interface

The scraper provides a comprehensive CLI with multiple commands:

#### 1. Scrape a Single URL

```bash
# Basic scraping
python crypto_scraper_cli.py scrape https://etherscan.io/tx/0x123...

# With custom selectors
python crypto_scraper_cli.py scrape https://etherscan.io/tx/0x123... --selectors .address,.hash

# Show extracted addresses
python crypto_scraper_cli.py scrape https://etherscan.io/tx/0x123... --show-addresses

# Save results to file
python crypto_scraper_cli.py scrape https://etherscan.io/tx/0x123... --output results.json

# Verbose output
python crypto_scraper_cli.py scrape https://etherscan.io/tx/0x123... --verbose
```

#### 2. Batch Scraping

```bash
# Scrape URLs from a file
python crypto_scraper_cli.py batch sample_urls.txt

# With custom delay between requests
python crypto_scraper_cli.py batch sample_urls.txt --delay 3.0

# Save to specific output file
python crypto_scraper_cli.py batch sample_urls.txt --output batch_results.json
```

#### 3. Extract Addresses Only

```bash
# Quick address extraction without full scraping
python crypto_scraper_cli.py extract https://etherscan.io/tx/0x123...
```

#### 4. Configuration Information

```bash
# Show current configuration
python crypto_scraper_cli.py config

# Use custom config file
python crypto_scraper_cli.py config --config custom_config.yaml
```

### Programmatic Usage

```python
from crypto_transaction_scraper import CryptoTransactionScraper

# Initialize scraper
scraper = CryptoTransactionScraper(api_key="fc-YOUR-API-KEY")

# Scrape a single URL
result = scraper.scrape_with_hover_extraction(
    "https://etherscan.io/tx/0x0840bba848e991cdcfbf2b71b8e1cb94fb72d6343ad4bb182f7ee1c48612221d"
)

# Extract addresses from text
addresses = scraper.extract_addresses_from_text("Some text with 0x1234...5678")

# Batch processing
urls = ["https://etherscan.io/tx/0x123...", "https://polygonscan.com/tx/0x456..."]
results = scraper.batch_scrape_transactions(urls, delay=2.0)

# Save results
scraper.save_results(results, "output.json")
```

## 🔧 Configuration

The scraper uses a YAML configuration file (`config.yaml`) for customization:

```yaml
# API Configuration
api:
  firecrawl_api_key: "${FIRECRAWL_API_KEY}"
  timeout: 120000
  rate_limit_delay: 2.0

# Scraping Configuration
scraping:
  target_selectors:
    - '[title*="0x"]'
    - '[data-tooltip*="0x"]'
    - '.address'
    - '.hash'
  
  wait_times:
    page_load: 2000
    hover_delay: 500

# Network Detection
networks:
  ethereum:
    domains: ['etherscan.io', 'etherscan.com']
    address_pattern: '0x[a-fA-F0-9]{40}'
```

## 🌐 Supported Networks

The scraper automatically detects and supports these blockchain networks:

- **Ethereum**: etherscan.io, etherscan.com
- **Polygon**: polygonscan.com
- **BSC**: bscscan.com
- **Arbitrum**: arbiscan.io
- **Optimism**: optimistic.etherscan.io
- **Avalanche**: snowtrace.io
- **Fantom**: ftmscan.com
- **Bitcoin**: blockchain.com, blockstream.info, mempool.space
- **Solana**: solscan.io, explorer.solana.com

## 📊 Output Format

The scraper outputs structured JSON data:

```json
{
  "scraped_at": "2025-01-27T10:30:00",
  "total_urls": 1,
  "successful_scrapes": 1,
  "failed_scrapes": 0,
  "results": [
    {
      "success": true,
      "url": "https://etherscan.io/tx/0x123...",
      "network": "ethereum",
      "addresses": [
        {
          "address": "0x1234567890abcdef1234567890abcdef1234567890",
          "address_type": "ethereum",
          "network": "ethereum",
          "abbreviated": "0x123456...7890",
          "full_address": "0x1234567890abcdef1234567890abcdef1234567890",
          "confidence": 0.9,
          "source_element": "text_content"
        }
      ],
      "transaction_data": {
        "tx_hash": "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
        "block_number": 12345678,
        "amount": "1.5",
        "token": "ETH",
        "gas_fee": "0.002 ETH",
        "status": "confirmed",
        "network": "ethereum"
      }
    }
  ]
}
```

## 🎯 Address Detection Features

### Full Address Patterns

- **Ethereum**: `0x[a-fA-F0-9]{40}`
- **Bitcoin**: `[13][a-km-zA-HJ-NP-Z1-9]{25,34}` and `bc1[a-z0-9]{39,59}`
- **Solana**: `[1-9A-HJ-NP-Za-km-z]{32,44}`
- **Transaction Hashes**: `0x[a-fA-F0-9]{64}`

### Abbreviated Address Patterns

- **Ethereum Short**: `0x[a-fA-F0-9]{4}...[a-fA-F0-9]{4}`
- **Ethereum Medium**: `0x[a-fA-F0-9]{6}...[a-fA-F0-9]{6}`
- **Generic Short**: `[a-zA-Z0-9]{4,8}...[a-zA-Z0-9]{4,8}`

### Hover Element Detection

The scraper automatically detects and interacts with:
- Elements with `title` attributes containing addresses
- `data-tooltip` attributes
- `data-address` attributes
- Common CSS classes like `.address`, `.hash`, `.tx-hash`
- Mouse event handlers

## ⚡ Performance & Rate Limiting

- **Default delay**: 2 seconds between requests
- **Configurable timeouts**: 120 seconds for full scraping
- **Smart rate limiting**: Prevents API abuse
- **Batch processing**: Efficient handling of multiple URLs
- **Error handling**: Graceful failure and retry logic

## 🧪 Testing

Use the included sample URLs file for testing:

```bash
# Test with sample URLs
python crypto_scraper_cli.py batch sample_urls.txt --delay 3.0

# Test single URL extraction
python crypto_scraper_cli.py extract https://etherscan.io/tx/0x0840bba848e991cdcfbf2b71b8e1cb94fb72d6343ad4bb182f7ee1c48612221d
```

## 🔍 Troubleshooting

### Common Issues

1. **API Key Error**:
   ```
   Error: Firecrawl API key required
   ```
   Solution: Set `FIRECRAWL_API_KEY` environment variable

2. **Rate Limiting**:
   ```
   Error: Rate limit exceeded
   ```
   Solution: Increase delay between requests with `--delay` flag

3. **Timeout Errors**:
   ```
   Error: Request timeout
   ```
   Solution: Increase timeout in config or use `--verbose` for debugging

### Debug Mode

Enable verbose logging for detailed information:

```bash
python crypto_scraper_cli.py scrape <url> --verbose
```

## 📝 Examples

### Real Transaction Example

```bash
# Scrape a real ShapeShift affiliate transaction
python crypto_scraper_cli.py scrape \
  "https://etherscan.io/tx/0x0840bba848e991cdcfbf2b71b8e1cb94fb72d6343ad4bb182f7ee1c48612221d" \
  --show-addresses --output shapeshift_tx.json
```

This will extract:
- Transaction hash: `0x0840bba848e991cdcfbf2b71b8e1cb94fb72d6343ad4bb182f7ee1c48612221d`
- From/To addresses
- Transaction amount and token
- Gas fees
- Block information

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- [Firecrawl](https://firecrawl.dev) for providing the powerful web scraping API
- The crypto community for feedback and testing
- Open source contributors who helped improve the scraper

## 🔗 Links

- [Firecrawl Documentation](https://docs.firecrawl.dev/introduction)
- [Firecrawl GitHub](https://github.com/firecrawl/firecrawl)
- [Get Firecrawl API Key](https://firecrawl.dev)

---

**Note**: This scraper is designed for educational and research purposes. Please respect website terms of service and implement appropriate rate limiting for production use.

