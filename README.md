# ShapeShift Affiliate Tracker

A comprehensive multi-protocol, multi-chain system for tracking ShapeShift affiliate transactions and revenue across the DeFi ecosystem.

## 🎯 Project Goals

- **Real-time Monitoring**: Track ShapeShift affiliate transactions across multiple protocols and chains
- **Revenue Intelligence**: Provide business intelligence for ShapeShift DAO treasury and rFOX distribution (25% of fees streamed monthly to stakers)
- **Protocol Coverage**: Monitor Relay, Portals, CoW Swap, ButterSwap, and other integrations
- **Address Verification**: Maintain protocol-specific affiliate address mapping for auditing

## 🏗️ Architecture Evolution

### 1. Monolithic Repository (Initial)
- **Approach**: All protocols combined in a single service
- **Pros**: Shared utilities, single deployment
- **Cons**: Brittle architecture, difficult debugging, tight coupling

### 2. Modular Repository (Intermediate)
- **Approach**: Separate directories per protocol with shared utilities
- **Pros**: Cleaner separation of logic, better organization
- **Cons**: Still coupled deployments, shared dependency issues

### 3. Standalone Services (Current)
- **Approach**: Independent services for each protocol
- **Pros**: Easier debugging, reliability per protocol, independent scaling
- **Cons**: More infrastructure overhead, code duplication

## 🚨 Key Technical Challenges

### 1. Event Log Parsing
- **Error**: `'bytes' object has no attribute 'encode'`
- **Cause**: Web3.py compatibility issues with log objects
- **Impact**: Relay listener failures, incomplete data capture
- **Solution**: Explicit handling of Web3 AttributeDict and bytes objects

### 2. RPC Provider Limitations
- **Issue**: Free-tier caps (Infura, Alchemy) blocking large block scans
- **Solution**: Provider rotation + block chunking + retry backoff
- **Current**: Using Alchemy API key from .env file

### 3. Event Detection Variance
- **Challenge**: Protocols emit affiliate events differently
- **Solution**: Custom ABIs per chain/protocol, event signature detection

### 4. Cross-Chain Consistency
- **Challenge**: Different EVM chain quirks (Base, Arbitrum, Optimism)
- **Solution**: Schema normalization before CSV storage

## 🔧 Technical Implementation

- **Event Detection**: Keccak256 hashing + topic filtering
- **RPC Strategy**: Multi-provider fallback with rate limiting
- **Block Tracking**: Persistent checkpointing via CSV files
- **Data Storage**: CSV-first approach (no premature database complexity)
- **Type Safety**: Explicit handling of Web3 objects and runtime validation

## 📊 Protocol Coverage & Status

### ✅ CoW Swap
- **Status**: Fully working
- **Chains**: Ethereum, Gnosis
- **Affiliate Addresses**:
  - **Ethereum**: `0x2a79a3c28fc49447b6d3f89d2a2bfb91e7b6976a`
  - **Gnosis**: `0xd1d6040d9b905f4a83e6b6d2a6a09f2f5f2f3d06`
- **Performance**: 1000+ block scans successful

### ✅ Portals
- **Status**: Working (leverages CoW Swap listener design)
- **Chain**: Ethereum
- **Affiliate Address**: `0x4d8cEdeB69466299e27A7f2C3eB7d5d23d846F9d`
- **Performance**: Smooth data capture, mirroring CoW Swap success

### ⚠️ Relay
- **Status**: Partially working, parsing errors recently fixed
- **Chains**: Ethereum, Base
- **Affiliate Addresses**:
  - **Ethereum**: `0x0a7a93ae54c3a44a471a65f7a6d47671e3f6c43d`
  - **Base**: `0x8f6226D2D5f29367dC1bA53C70c58d23992b77b9`
- **Issues**: Recent `'bytes' object has no attribute 'encode'` error fixed
- **Performance**: Requires testing after ABI fix

### ✅ ButterSwap
- **Status**: Working, no affiliate activity detected
- **Chain**: Base
- **Affiliate Address**: `0x9A7fC46A6932CDe0A1Ab74e36bE1b6d8E6AFA1F2`
- **Performance**: Listener operational, idle due to no activity

## 📈 Current Results & Performance

- **CoW Swap**: 1000+ block scans successful across Ethereum and Gnosis
- **Portals**: Mirroring CoW Swap performance, smooth data capture
- **Relay**: Recently fixed parsing errors, requires testing
- **ButterSwap**: Listener operational, monitoring for affiliate activity
- **Data Storage**: CSV-based system with persistent block tracking

## 💡 Key Learnings & Best Practices

1. **Architecture Evolution**: Monolith → Modular → Microservices approach proved most reliable
2. **CSV-First Strategy**: Outperforms premature database complexity for this use case
3. **Protocol-Specific Configs**: Despite shared framework, each protocol requires separate configuration
4. **Affiliate Address Registry**: Critical for on-chain fee validation and auditing
5. **Web3 Compatibility**: Explicit handling of Web3 objects prevents runtime errors

## 🛣️ Next Steps & Roadmap

### Immediate (Next 2 weeks)
- [x] Fix Relay ABI parsing errors
- [ ] Test Relay listener with real data
- [ ] Integrate affiliate address registry as YAML config
- [ ] Add unit tests with known affiliate transactions

### Short-term (Next month)
- [ ] Extend support for THORChain integration
- [ ] Add Chainflip protocol support
- [ ] Implement 0x protocol monitoring
- [ ] Multi-chain ButterSwap expansion

### Medium-term (Next quarter)
- [ ] Build dashboard layer (Dune/Flipside integration)
- [ ] Internal CSV pivot and analytics
- [ ] Real-time alerting system
- [ ] Performance optimization and scaling

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Web3.py
- Alchemy API key (stored in `.env`)

### Installation
```bash
# Clone repository
git clone https://github.com/profmcc/shapeshift-affiliate-tracker.git
cd shapeshift-affiliate-tracker

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp env.example .env
# Add your Alchemy API key to .env

# Run specific protocol listener
python relay_listener.py --chains base
python cowswap_listener.py --chains ethereum
```

### Configuration
- **Environment Variables**: API keys and RPC endpoints in `.env`
- **Protocol Configs**: Protocol-specific settings in `config/` directory
- **Affiliate Addresses**: Maintained in configuration files

## 📁 Project Structure

```
shapeshift-affiliate-tracker/
├── config/                 # Configuration files
├── listeners/             # Protocol-specific listeners
├── data/                  # CSV data storage
├── abis/                  # Contract ABIs
├── scripts/               # Utility scripts
├── tests/                 # Test suite
└── docs/                  # Documentation
```

## 🔍 Monitoring & Debugging

- **Logs**: Comprehensive logging for all protocol listeners
- **Block Tracking**: Persistent CSV-based block progress tracking
- **Error Handling**: Graceful degradation and retry mechanisms
- **Performance Metrics**: Block processing rates and success metrics

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Links

- **Repository**: https://github.com/profmcc/shapeshift-affiliate-tracker
- **ShapeShift DAO**: https://shapeshift.com/
- **Documentation**: See `docs/` directory for detailed technical specifications

---

*Last updated: August 28, 2025*
*Status: Relay listener parsing errors fixed, ready for testing*