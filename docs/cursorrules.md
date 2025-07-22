# Cursor Rules for ShapeShift Affiliate Tracker

## Core Principles

### Accuracy Over Speed
- **Never make up data** - if information is unavailable, clearly state "UNKNOWN" or "NOT FOUND"
- **Verify all token addresses** against official sources before using
- **Cross-reference transaction data** with blockchain explorers when possible
- **Use real-time price feeds** from reputable sources (CoinGecko, CoinMarketCap)
- **Validate affiliate addresses** against official ShapeShift documentation

### Comprehensive Transaction Tracking
- **Track ALL transactions** involving ShapeShift affiliate contracts, not just high-value ones
- **Include failed transactions** in logs (with status indicators)
- **Record full transaction details**: hash, block, timestamp, from/to addresses, token amounts, USD values
- **Store raw transaction data** for debugging and verification
- **Use human-readable token names** and correct decimal places for all amounts

## Multi-Chain Support

### Supported Chains
ShapeShift supports affiliate tracking on these chains:

1. **Ethereum Mainnet** (Chain ID: 1)
   - Affiliate: `0x90A48D5CF7343B08dA12E067680B4C6dbfE551Be`
   - Protocols: CowSwap, 0x Protocol, Portals

2. **Arbitrum** (Chain ID: 42161)
   - Affiliate: `0x38276553F8fbf2A027D901F8be45f00373d8Dd48`
   - Protocols: Relay, CowSwap, 0x Protocol

3. **Polygon** (Chain ID: 137)
   - Affiliate: `0xB5F944600785724e31Edb90F9DFa16dBF01Af000`
   - Protocols: CowSwap, 0x Protocol

4. **Optimism** (Chain ID: 10)
   - Affiliate: `0x6268d07327f4fb7380732dc6d63d95F88c0E083b`
   - Protocols: CowSwap, 0x Protocol

5. **Base** (Chain ID: 8453)
   - Affiliate: `0x9c9aA90363630d4ab1D9dbF416cc3BBC8d3Ed502`
   - Protocols: CowSwap, 0x Protocol

6. **Avalanche** (Chain ID: 43114)
   - Affiliate: `0x74d63F31C2335b5b3BA7ad2812357672b2624cEd`
   - Protocols: CowSwap, 0x Protocol

7. **BSC** (Chain ID: 56)
   - Affiliate: `0x8b92b1698b57bEDF2142297e9397875ADBb2297E`
   - Protocols: CowSwap, 0x Protocol

8. **THORChain** (Native)
   - Affiliate: ShapeShift DAO address
   - Protocols: Native swaps

9. **Chainflip** (Native)
   - Affiliate: ShapeShift DAO address
   - Protocols: Native swaps

### Protocol Contracts by Chain

#### CowSwap (GPv2Settlement)
- Ethereum: `0x9008D19f58AAbD9eD0D60971565AA8510560ab41`
- Arbitrum: `0x9008D19f58AAbD9eD0D60971565AA8510560ab41`
- Polygon: `0x9008D19f58AAbD9eD0D60971565AA8510560ab41`
- Optimism: `0x9008D19f58AAbD9eD0D60971565AA8510560ab41`
- Base: `0x9008D19f58AAbD9eD0D60971565AA8510560ab41`
- Avalanche: `0x9008D19f58AAbD9eD0D60971565AA8510560ab41`
- BSC: `0x9008D19f58AAbD9eD0D60971565AA8510560ab41`

#### 0x Protocol (ExchangeProxy)
- Ethereum: `0xDef1C0ded9bec7F1a1670819833240f027b25EfF`
- Arbitrum: `0xDef1C0ded9bec7F1a1670819833240f027b25EfF`
- Polygon: `0xDef1C0ded9bec7F1a1670819833240f027b25EfF`
- Optimism: `0xDef1C0ded9bec7F1a1670819833240f027b25EfF`
- Base: `0xDef1C0ded9bec7F1a1670819833240f027b25EfF`
- Avalanche: `0xDef1C0ded9bec7F1a1670819833240f027b25EfF`
- BSC: `0xDef1C0ded9bec7F1a1670819833240f027b25EfF`

#### Portals (Router)
- Ethereum: `0xbf5A7F3629fB325E2a8453D595AB103465F75E62`

#### Relay (Aggregator)
- Arbitrum: `0xBBbfD134E9b44BfB5123898BA36b01dE7ab93d98`

## Listener Requirements

### Each Listener Must:
1. **Track block ranges** using the shared block tracking system
2. **Store all transactions** in a dedicated database table
3. **Include these fields**:
   - `tx_hash` (unique identifier)
   - `block_number`
   - `timestamp`
   - `from_address`
   - `to_address`
   - `protocol` (cowswap, zerox, portals, relay, thorchain, chainflip)
   - `chain_id`
   - `affiliate_address`
   - `volume_usd`
   - `tokens_involved` (JSON array of token symbols)
   - `raw_data` (full transaction data for debugging)
   - `status` (success/failed)
   - `created_at`

4. **Use proper token metadata**:
   - Symbol (e.g., "WETH", "USDC")
   - Name (e.g., "Wrapped Ether", "USD Coin")
   - Decimals (e.g., 18, 6)
   - Contract address (checksummed)

5. **Calculate accurate USD volumes**:
   - Use real-time price feeds
   - Apply correct decimal places
   - Handle failed transactions (volume = 0)

### Listener Status Tracking
Create a dashboard that shows:
- **Per-chain status**: Last block processed, transactions found, total volume
- **Per-protocol status**: Which protocols are active on which chains
- **Cross-validation**: Compare transaction counts across similar time periods
- **Error tracking**: Failed transactions, missing token data, API errors

## Data Quality Standards

### Token Information
- **Always verify token addresses** against official sources
- **Use standardized symbols** (WETH not wETH, USDC not USDC.e unless specifically different)
- **Include token names** for human readability
- **Handle unknown tokens** gracefully (show address, mark as "UNKNOWN")

### Transaction Data
- **Store complete transaction receipts** for debugging
- **Include all transfer events** in the transaction
- **Record affiliate fee amounts** separately from swap amounts
- **Track gas costs** for cost analysis

### Price Data
- **Use multiple price sources** for validation
- **Handle price feed failures** gracefully
- **Store price timestamps** with transactions
- **Cross-reference prices** across sources when possible

## Validation and Cross-Checking

### Automated Checks
1. **Block range validation**: Ensure no gaps in block scanning
2. **Transaction count validation**: Compare daily transaction counts across chains
3. **Volume validation**: Flag unusually high/low volumes
4. **Token validation**: Verify all token addresses are valid contracts
5. **Affiliate validation**: Ensure transactions involve correct affiliate addresses

### Manual Verification
1. **Sample transaction verification**: Randomly check transactions against blockchain explorers
2. **Protocol-specific validation**: Verify protocol contract addresses are correct
3. **Cross-chain consistency**: Ensure similar protocols show similar patterns across chains

## Error Handling

### Graceful Degradation
- **Continue processing** if individual transactions fail
- **Log all errors** with context for debugging
- **Retry failed API calls** with exponential backoff
- **Handle network timeouts** and rate limiting

### Data Recovery
- **Backup transaction data** regularly
- **Store intermediate results** to avoid losing progress
- **Implement checkpointing** for long-running scans
- **Provide data export** capabilities for analysis

## Performance Considerations

### Block Scanning
- **Use efficient RPC endpoints** with high rate limits
- **Implement parallel processing** where possible
- **Cache frequently accessed data** (token metadata, prices)
- **Use batch requests** for multiple transactions

### Database Optimization
- **Index frequently queried fields** (tx_hash, block_number, timestamp)
- **Partition large tables** by date or chain
- **Archive old data** to maintain performance
- **Use appropriate data types** (INTEGER for block numbers, TEXT for addresses)

## Documentation Requirements

### Code Documentation
- **Document all affiliate addresses** and their sources
- **Explain protocol contract addresses** and their purposes
- **Document token metadata sources** and update procedures
- **Include setup instructions** for each chain and protocol

### Data Documentation
- **Document database schema** and field meanings
- **Explain volume calculation methods** for each protocol
- **Document error codes** and their meanings
- **Include troubleshooting guides** for common issues

## Security Considerations

### API Key Management
- **Use environment variables** for all API keys
- **Rotate API keys** regularly
- **Monitor API usage** for rate limiting
- **Implement key backup** procedures

### Data Security
- **Encrypt sensitive data** in transit and at rest
- **Implement access controls** for database
- **Audit data access** regularly
- **Backup data securely** with encryption

## Monitoring and Alerting

### Health Checks
- **Monitor listener status** (running/stopped)
- **Track block processing rates** (blocks per minute)
- **Monitor transaction discovery rates** (transactions per hour)
- **Alert on data quality issues** (missing tokens, failed transactions)

### Performance Monitoring
- **Track API response times** for price feeds
- **Monitor database performance** (query times, storage usage)
- **Track memory usage** for long-running processes
- **Monitor network connectivity** to RPC endpoints

## Compliance and Reporting

### Data Retention
- **Retain transaction data** for at least 2 years
- **Archive old data** to cost-effective storage
- **Implement data deletion** procedures for compliance
- **Document data retention policies**

### Reporting Requirements
- **Generate daily volume reports** by chain and protocol
- **Track affiliate fee distributions** over time
- **Monitor protocol adoption** across chains
- **Report data quality metrics** (completeness, accuracy)

---

**Remember**: This system tracks real financial transactions. Accuracy and reliability are paramount. When in doubt, err on the side of caution and document any assumptions or limitations clearly.
