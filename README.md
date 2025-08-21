# ShapeShift Affiliate Fee Listener

Collects and validates affiliate-fee events (CoW Swap, THORChain, Portals, Relay, …), normalizes them, and emits structured records for analytics.

## Quickstart
- Python 3.11+
- `uv pip install -r requirements.txt`  # or `poetry install`
- Copy `.env.example` → `.env` and fill provider/API keys
- Run one listener:
  ```bash
  python -m shapeshift_listener.affiliate_fee \
    --chain arbitrum --from-block 22222222 --sink stdout
  ```

## Design

```
Event Source → ABI Decoder → Normalizer → Sink (stdout|S3|DB)
```

- **Idempotency**: (tx_hash, log_index), reorg window: 25 blocks
- **Retries**: exponential backoff + jitter on 429/5xx
- **Logs**: JSON (includes chain, listener, tx_hash)

## Status

**Stable**: ETH/ARB affiliate-fee decode & emit  
**Experimental**: Multi-chain expansion, real-time streaming

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Protocol      │    │   Data          │    │   Analysis      │
│   Listeners     │───▶│   Storage       │───▶│   & Reporting   │
│                 │    │                 │    │                 │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ • ButterSwap    │    │ • CSV Files     │    │ • Revenue       │
│ • Relay         │    │ • Databases     │    │   Analytics     │
│ • CoW Swap      │    │ • Block         │    │ • Protocol      │
│ • Portals       │    │   Tracking      │    │   Performance   │
│ • ThorChain     │    │ • Event Logs    │    │ • Cross-Chain   │
└─────────────────┘    └─────────────────┘    │   Correlation   │
                                              └─────────────────┘
```

## Supported Protocols

- **DEX Aggregators**: ButterSwap, CoW Swap, 0x Protocol
- **Cross-Chain**: Relay, Portals, ThorChain
- **Chains**: Ethereum, Polygon, Base, Arbitrum, Optimism, Avalanche, BSC

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest

# Lint code
ruff check .

# Format code
black .

# Type check
mypy .
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Test thoroughly with real blockchain data
4. Submit a pull request with clear documentation

## License

MIT License - see [LICENSE](LICENSE) file for details.