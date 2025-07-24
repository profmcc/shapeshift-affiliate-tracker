# ShapeShift Affiliate Tracker

## Overview
This project tracks affiliate fees from various protocols (Portals, 0x, Relay, Chainflip) across EVM chains. It is organized for maintainability and clean code, with shared modules for config, logging, and database access.

## Directory Structure
- `listeners/` — Main event listeners for each protocol
- `shared/` — Shared helpers for config, logging, and database
- `tests/` — Test scripts
- `old files/` — Deprecated or legacy code

## Shared Modules
- `shared/config.py`: Centralized config and .env loader
- `shared/logging.py`: Consistent logger setup (`setup_logger`)
- `shared/db.py`: SQLite helpers (`connect_db`, `ensure_schema`)

## Setup
1. **Install dependencies:**
   ```sh
   pip install web3 pyyaml python-dotenv
   ```
2. **.env file:**
   Place your API keys and secrets in a `.env` file in the project root. Example:
   ```env
   INFURA_API_KEY=your_infura_key
   ALCHEMY_API_KEY=your_alchemy_key
   ```
3. **Config YAML:**
   Each listener requires a config YAML (see `listeners/portals_listener_config.yaml` for example).

## Usage
Run a listener with:
```sh
PYTHONPATH=. python listeners/portals_listener.py
```

## Troubleshooting
- If you see `ModuleNotFoundError`, ensure you use `PYTHONPATH=.`
- If config or .env values are missing, check your YAML and `.env` files.
- For DB schema errors, ensure your config and schema match the code.

## Contributing
- Add new listeners in `listeners/`, using shared modules for config/log/db.
- Write docstrings and type hints for all functions.
- Place tests in `tests/`. 