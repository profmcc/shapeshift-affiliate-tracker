# ShapeShift Fee Listener System

## 🎯 Overview

The ShapeShift Fee Listener System is a comprehensive multi-protocol, multi-chain infrastructure designed to track, monitor, and analyze affiliate fee transactions across the entire ShapeShift ecosystem. This system provides real-time visibility into revenue streams, enabling the ShapeShift DAO to make informed decisions about treasury management and rFOX token distribution.

## 🏗️ System Architecture

### Core Components

1. **Protocol Listeners**: Real-time blockchain event listeners for each supported protocol
2. **Fee Aggregators**: Collectors that consolidate fees across multiple chains
3. **Treasury Safes**: Multi-signature wallets that securely hold collected fees
4. **Analytics Engine**: Data processing and reporting system for business intelligence
5. **Alert System**: Real-time notifications for significant fee events

### Supported Protocols

| Protocol | Status | Chains | Fee Collection |
|----------|--------|--------|----------------|
| **CoW Swap** | ✅ Active | Ethereum, Gnosis | Real-time |
| **Portals** | ✅ Active | Ethereum | Real-time |
| **Relay** | ✅ Active | Ethereum, Base | Real-time |
| **ButterSwap** | ✅ Active | Base | Monitoring |
| **THORChain** | ✅ Active | THORChain | Real-time |
| **Chainflip** | ✅ Active | Chainflip | Real-time |
| **0x Protocol** | ✅ Active | Ethereum | Real-time |

## 💰 Fee Collection Structure

### Revenue Streams

- **Affiliate Fees**: Percentage-based fees from protocol integrations
- **Swap Fees**: Transaction fees from DEX operations
- **Bridge Fees**: Cross-chain transfer fees
- **Liquidity Fees**: LP position management fees

### Fee Distribution

```
Total Fees Collected
├── 75% → ShapeShift DAO Treasury
└── 25% → rFOX Stakers (Monthly Distribution)
```

## 🏦 Treasury Management

### Multi-Chain Treasury Safes

The system maintains dedicated treasury safes across multiple blockchain networks:

#### **Ethereum Mainnet**
- **Address**: `0x90A48D5CF7343B08dA12E067680B4C6dbfE551Be`
- **Purpose**: Primary treasury for Ethereum-based protocols
- **Protocols**: CoW Swap, Portals, Relay, 0x

#### **Base Chain**
- **Address**: `0x9c9aA90363630d4ab1D9dbF416cc3BBC8d3Ed502`
- **Purpose**: Treasury for Base-based protocols
- **Protocols**: Relay, ButterSwap

#### **Additional Chains**
- **Optimism**: `0x6268d07327f4fb7380732dc6d63d95F88c0E083b`
- **Avalanche**: `0x74d63F31C2335b5b3BA7ad2812357672b2624cEd`
- **Polygon**: `0xB5F944600785724e31Edb90F9DFa16dBF01Af000`
- **BSC**: `0x8b92b1698b57bEDF2142297e9397875ADBb2297E`
- **Arbitrum**: `0x38276553F8fbf2A027D901F8be45f00373d8Dd48`
- **Solana**: `Bh7R3MeJ98D7Ersxh7TgVQVQUSmDMqwrFVHH9DLfb4u3`

### Multi-Signature Security

**Base Chain Treasury**: 2-of-3 multisig configuration
- **Owner 1**: `0x35339070f178dC4119732982C23F5a8d88D3f8a3`
- **Owner 2**: `0x47f11EB6ab5B41857EA8616aDeAf205248b5C55c`
- **Owner 3**: `0xF5AA59151bE6515C4Ca68A0282CF68B3eA4846fC`
- **Threshold**: 2 signatures required for any transaction

## 🔍 Fee Detection & Monitoring

### Event Types Monitored

1. **Affiliate Fee Events**
   - `AffiliateFeeCollected` events from protocol contracts
   - Real-time fee amount tracking
   - Source protocol identification

2. **Treasury Balance Changes**
   - Safe balance monitoring
   - Incoming/outgoing transaction tracking
   - Multi-chain balance aggregation

3. **rFOX Distribution Events**
   - Monthly distribution triggers
   - Staking contract interactions
   - Distribution amount calculations

### Monitoring Frequency

- **Fee Collection**: Real-time (block-by-block)
- **Balance Updates**: Every block
- **Aggregation**: Daily and monthly
- **Reporting**: Daily summaries + monthly analytics

## 📊 Data Collection & Storage

### Storage Strategy

- **Primary**: CSV files for historical data
- **Real-time**: In-memory processing for live monitoring
- **Backup**: Database snapshots for critical data
- **Analytics**: Aggregated metrics for business intelligence

### Data Points Collected

- Transaction hash and block number
- Fee amount and token type
- Source protocol and chain
- Affiliate address involved
- Treasury safe destination
- Timestamp and gas costs

## 🚨 Alert System

### Alert Types

1. **High-Value Transactions**
   - Threshold: >$10,000 USD equivalent
   - Notification: Immediate to treasury team
   - Action: Manual verification required

2. **Anomaly Detection**
   - Unusual fee patterns
   - Unexpected protocol activity
   - Chain-specific issues

3. **Balance Alerts**
   - Low treasury balances
   - Failed transactions
   - Multi-sig threshold issues

### Notification Channels

- **Slack**: Real-time alerts for critical events
- **Email**: Daily summaries and monthly reports
- **Dashboard**: Live monitoring interface
- **API**: Webhook notifications for integrations

## 🔧 Technical Implementation

### Technology Stack

- **Blockchain Interaction**: Web3.py, ethers.js
- **Event Processing**: Custom event listeners
- **Data Storage**: CSV, SQLite, JSON
- **Monitoring**: Custom alerting system
- **Analytics**: Pandas, NumPy for data processing

### Key Features

- **Multi-Provider RPC**: Fallback support for reliability
- **Rate Limiting**: Intelligent request throttling
- **Error Handling**: Graceful degradation and retry logic
- **Block Tracking**: Persistent checkpointing
- **Cross-Chain Support**: Unified interface for multiple chains

## 📈 Business Intelligence

### Key Metrics

1. **Revenue Performance**
   - Daily/monthly fee collection totals
   - Protocol-specific revenue breakdown
   - Chain-specific performance metrics

2. **Treasury Health**
   - Multi-chain balance overview
   - Fee collection efficiency
   - Distribution timing and amounts

3. **Protocol Analytics**
   - Usage patterns and trends
   - Fee optimization opportunities
   - Integration performance metrics

### Reporting

- **Daily Reports**: Fee collection summaries
- **Monthly Reports**: Comprehensive treasury analysis
- **Quarterly Reviews**: Strategic insights and recommendations
- **Annual Planning**: Revenue projections and budget planning

## 🛡️ Security & Compliance

### Security Measures

- **Multi-Signature Wallets**: Required for all treasury operations
- **Access Control**: Role-based permissions for system access
- **Audit Logging**: Complete transaction history tracking
- **Encryption**: Sensitive data encryption at rest and in transit

### Compliance Features

- **Regulatory Reporting**: Automated compliance reporting
- **Audit Trails**: Complete transaction history
- **Tax Documentation**: Fee collection documentation
- **Legal Entity Tracking**: Multi-entity support

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- Web3.py library
- Access to blockchain RPC endpoints
- Treasury safe addresses and configurations

### Quick Start

```bash
# Clone the repository
git clone https://github.com/profmcc/shapeshift-affiliate-tracker.git
cd shapeshift-affiliate-tracker

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp env.example .env
# Add your RPC endpoints and API keys

# Start fee listening
python run_fee_listener.py --protocols all --chains all
```

### Configuration

1. **Environment Variables**: Set RPC endpoints and API keys
2. **Treasury Addresses**: Configure safe addresses in `treasury_safes.yaml`
3. **Protocol Settings**: Adjust listener parameters per protocol
4. **Alert Configuration**: Set up notification preferences

## 📚 Documentation

### Additional Resources

- **API Documentation**: REST API endpoints and usage
- **Configuration Guide**: Detailed setup instructions
- **Troubleshooting**: Common issues and solutions
- **Development Guide**: Contributing to the system

### Support

- **Technical Issues**: GitHub Issues repository
- **Business Questions**: ShapeShift DAO team
- **Emergency Contacts**: Treasury team direct line

## 🔮 Future Enhancements

### Planned Features

1. **Advanced Analytics**
   - Machine learning for fee prediction
   - Automated optimization recommendations
   - Real-time market analysis

2. **Integration Expansion**
   - Additional DeFi protocols
   - Cross-chain bridge monitoring
   - NFT marketplace fee tracking

3. **Automation**
   - Automated treasury rebalancing
   - Smart contract-based fee distribution
   - AI-powered anomaly detection

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.

---

**Last Updated**: August 28, 2025  
**Version**: 1.0.0  
**Maintainer**: ShapeShift DAO Team  
**Status**: Production Ready ✅
