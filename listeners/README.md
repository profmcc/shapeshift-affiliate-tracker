# Portals Affiliate Fee Listener

## Setup

1. Install dependencies:
   ```sh
   pip install web3 pyyaml python-dotenv
   ```
   - `web3` for Ethereum RPC
   - `pyyaml` for YAML config support
   - `python-dotenv` for loading secrets from .env

2. Add your Infura (or other RPC) key to a `.env` file in the project root:
   ```
   INFURA_API_KEY=your_actual_key_here
   ```

3. Edit `portals_listener_config.yaml` to use `${INFURA_API_KEY}` in the RPC URLs.

4. Run the listener:
   ```sh
   python listeners/portals_listener.py --resume
   ```

## Features
- Parallel, resumable, config-driven scanning of all supported chains
- Progress is stored in `listeners/portals_progress.json`
- Results are stored in `databases/portals_transactions.db` 