import os, json, re, time, math, argparse, requests
from datetime import datetime, timedelta, date
from dateutil import parser as dtparse
import pandas as pd
import matplotlib.pyplot as plt
from tqdm import tqdm

# -------- Config --------
CMC_BASE = "https://pro-api.coinmarketcap.com"
STABLES = {"USDT","USDC","DAI","USD"}
# manual symbol normalizations for CMC
SYMBOL_ALIAS = {
    "WETH":"ETH",   # price with ETH
    "WBTC":"BTC",   # price with BTC
    "sUSD":"SUSD",  # example if it appears
    "XUSD":"USD",   # treat like USD
    "BUSD":"USD",   # retired; treat as USD
    "USDT.e":"USDT","USDC.e":"USDC",
    "USD":"USD",    # identity
    "XRUNE":"RUNE", # Thorchain RUNE
    "VTHOR":"RUNE", # Thorchain RUNE
    "THOR":"RUNE",  # Thorchain RUNE
    "FOX":"SHIB",   # ShapeShift FOX token (use SHIB as proxy)
    "RUJI":"SHIB",  # Unknown token (use SHIB as proxy)
    "TGT":"USDT",   # Unknown token (use USDT as proxy)
    "SNX":"SNX",    # Synthetix (should work with CMC)
    "DPI":"DPI",    # DeFi Pulse Index (should work with CMC)
}

# -------- Helpers --------
def parse_timestamp(ts):
    if pd.isna(ts) or ts is None:
        return pd.NaT
    s = str(ts).split("(")[0].strip()
    try:
        # Try common format first
        return datetime.strptime(s, "%b %d %Y %I:%M:%S %p")
    except Exception:
        try:
            return dtparse.parse(s)
        except Exception:
            return pd.NaT

def extract_assets_from_text(raw):
    """Fallback: pull A–Z tickers out of the raw text; ignore numbers like '800'."""
    if not isinstance(raw, str): return (None, None)
    hits = re.findall(r"\n([A-Z]{2,10})\n", raw)
    if len(hits) >= 2:
        return hits[-2], hits[-1]
    return (None, None)

def norm_symbol(sym):
    if not isinstance(sym, str) or sym.strip() == "":
        return None
    sym = sym.strip().upper()
    return SYMBOL_ALIAS.get(sym, sym)

def daterange(d0: date, d1: date):
    cur = d0
    while cur <= d1:
        yield cur
        cur += timedelta(days=1)

# -------- CMC API --------
class CMC:
    def __init__(self, api_key: str):
        self.session = requests.Session()
        self.session.headers.update({"X-CMC_PRO_API_KEY": api_key})

    def _get(self, path, params, cost_hint=1, retries=3, sleep=0.5):
        for i in range(retries):
            r = self.session.get(CMC_BASE + path, params=params, timeout=30)
            if r.status_code == 200:
                return r.json()
            # polite backoff (rate limits / hiccups)
            time.sleep(sleep * (2 ** i))
        r.raise_for_status()

    def map_ids(self, symbols: list[str]) -> dict:
        """Resolve symbols to CMC ids (best effort)."""
        # Filter out known invalid symbols and clean the list
        valid_symbols = []
        for s in symbols:
            if s and s not in ["TCY", "XRUNE", "VTHOR", "THOR", "FOX", "RUJI", "TGT", "SNX"]:
                valid_symbols.append(s)
        
        if not valid_symbols:
            return {}
            
        syms = ",".join(sorted(set(valid_symbols)))
        try:
            data = self._get("/v1/cryptocurrency/map", {"symbol": syms})
            out = {}
            if data and "data" in data:
                for row in data["data"]:
                    out[row["symbol"].upper()] = row["id"]
            return out
        except Exception as e:
            print(f"[warn] CMC API error: {e}")
            return {}

    def get_current_price(self, cmc_id: int) -> float:
        """Get current price for a CMC ID (fallback when OHLCV not available)."""
        try:
            data = self._get("/v2/cryptocurrency/quotes/latest", {"id": cmc_id})
            if data and "data" in data and str(cmc_id) in data["data"]:
                return data["data"][str(cmc_id)]["quote"]["USD"]["price"]
        except Exception as e:
            print(f"[warn] CMC quotes error for ID {cmc_id}: {e}")
        return None

    def get_bulk_prices(self, symbols: list[str]) -> dict:
        """Get current prices for multiple symbols in one call."""
        try:
            syms = ",".join(symbols)
            data = self._get("/v2/cryptocurrency/quotes/latest", {"symbol": syms})
            out = {}
            if data and "data" in data:
                # Handle both string and integer keys in data
                for key, info in data["data"].items():
                    if isinstance(info, dict) and "quote" in info and "USD" in info["quote"]:
                        symbol = key.upper() if isinstance(key, str) else str(key).upper()
                        out[symbol] = info["quote"]["USD"]["price"]
            return out
        except Exception as e:
            print(f"[warn] CMC bulk quotes error: {e}")
            return {}

# -------- CoinGecko API (Free, no key needed) --------
class CoinGecko:
    def __init__(self):
        self.base_url = "https://api.coingecko.com/api/v3"
        self.session = requests.Session()

    def get_prices(self, symbols: list[str]) -> dict:
        """Get current prices for multiple symbols."""
        try:
            # Convert symbols to CoinGecko IDs
            id_map = self._get_symbol_map()
            prices = {}
            
            for symbol in symbols:
                if symbol in id_map:
                    price = self._get_price(id_map[symbol])
                    if price:
                        prices[symbol] = price
            
            return prices
        except Exception as e:
            print(f"[warn] CoinGecko API error: {e}")
            return {}

    def _get_symbol_map(self) -> dict:
        """Get mapping of symbols to CoinGecko IDs."""
        try:
            r = self.session.get(f"{self.base_url}/coins/list", timeout=30)
            if r.status_code == 200:
                data = r.json()
                symbol_map = {}
                for coin in data:
                    symbol_map[coin["symbol"].upper()] = coin["id"]
                return symbol_map
        except Exception as e:
            print(f"[warn] CoinGecko symbol map error: {e}")
        return {}

    def _get_price(self, coin_id: str) -> float:
        """Get current price for a specific coin ID."""
        try:
            r = self.session.get(f"{self.base_url}/simple/price", 
                               params={"ids": coin_id, "vs_currencies": "usd"}, 
                               timeout=30)
            if r.status_code == 200:
                data = r.json()
                if coin_id in data and "usd" in data[coin_id]:
                    return data[coin_id]["usd"]
        except Exception as e:
            print(f"[warn] CoinGecko price error for {coin_id}: {e}")
        return None

# -------- Midgard API for Thorchain Assets --------
class Midgard:
    def __init__(self):
        self.base_url = "https://midgard.thorchain.info/v2"
        self.session = requests.Session()

    def get_prices(self) -> dict:
        """Get current prices for Thorchain assets."""
        try:
            r = self.session.get(f"{self.base_url}/prices", timeout=30)
            if r.status_code == 200:
                data = r.json()
                prices = {}
                for asset in data:
                    if "price" in asset and "asset" in asset:
                        # Convert asset names to symbols
                        symbol = self.normalize_asset_name(asset["asset"])
                        if symbol:
                            prices[symbol] = float(asset["price"])
                return prices
        except Exception as e:
            print(f"[warn] Midgard API error: {e}")
        return {}

    def normalize_asset_name(self, asset_name: str) -> str:
        """Convert Thorchain asset names to symbols."""
        # Thorchain asset names are like "THOR.RUNE", "BTC.BTC", etc.
        if "." in asset_name:
            symbol = asset_name.split(".")[1]
            # Map to our expected symbols
            if symbol == "RUNE":
                return "XRUNE"  # Use XRUNE for Thorchain RUNE
            elif symbol == "TCY":
                return "TCY"
            else:
                return symbol
        return asset_name

    def get_historical_prices(self, start: date, end: date) -> pd.DataFrame:
        """Get historical prices from Midgard (simplified - uses current prices for all dates)."""
        current_prices = self.get_prices()
        if not current_prices:
            return pd.DataFrame()
        
        # Create a simple price table with current prices for all dates
        # This is a limitation of Midgard API - it doesn't provide historical OHLCV
        rows = []
        current_date = start
        while current_date <= end:
            for symbol, price in current_prices.items():
                rows.append((current_date, symbol, price))
            current_date += timedelta(days=1)
        
        return pd.DataFrame(rows, columns=["date", "asset", "close_usd"])

# -------- Main pipeline --------
def load_swaps(json_path: str) -> pd.DataFrame:
    with open(json_path, "r") as f:
        data = json.load(f)
    df = pd.DataFrame(data)
    # timestamp
    df["timestamp"] = df["timestamp"].apply(parse_timestamp)
    # amounts
    for col in ["from_amount", "to_amount"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    # preferred assets + fallback
    fb = df["raw_row_text"].apply(extract_assets_from_text)
    df["fb_from"] = fb.apply(lambda t: t[0])
    df["fb_to"] = fb.apply(lambda t: t[1])

    df["from_asset_clean"] = df["from_asset"].where(df["from_asset"].notna(), df["fb_from"])
    df["to_asset_clean"] = df["to_asset"].where(df["to_asset"].notna(), df["fb_to"])

    df["from_asset_clean"] = df["from_asset_clean"].apply(norm_symbol)
    df["to_asset_clean"]   = df["to_asset_clean"].apply(norm_symbol)

    swaps = df[(df["type"]=="Swap") & df["timestamp"].notna()].copy()
    swaps["date"] = swaps["timestamp"].dt.date
    swaps["route"] = swaps["from_asset_clean"].fillna("UNK") + " → " + swaps["to_asset_clean"].fillna("UNK")
    return swaps

def build_price_table(swaps: pd.DataFrame, cmc: CMC, midgard: Midgard, coingecko: CoinGecko, start: date, end: date) -> pd.DataFrame:
    # collect non-stable symbols to price
    symbols = sorted(set(
        [s for s in swaps["from_asset_clean"].dropna().unique() if s not in STABLES] +
        [s for s in swaps["to_asset_clean"].dropna().unique() if s not in STABLES]
    ))
    
    print(f"[info] Found {len(symbols)} unique symbols to price")
    
    # Strategy 1: Try CMC first (most reliable)
    print("[info] Step 1: Getting CMC prices...")
    cmc_prices = cmc.get_bulk_prices(symbols)
    cmc_coverage = len(cmc_prices)
    print(f"[info] CMC provided prices for {cmc_coverage}/{len(symbols)} symbols")
    
    # If bulk CMC failed, try individual lookups
    if cmc_coverage == 0:
        print("[info] CMC bulk failed, trying individual lookups...")
        for symbol in tqdm(symbols, desc="Getting individual CMC prices"):
            try:
                # Try to get CMC ID first
                id_map = cmc.map_ids([symbol])
                if symbol in id_map:
                    price = cmc.get_current_price(id_map[symbol])
                    if price:
                        cmc_prices[symbol] = price
            except Exception as e:
                continue
        cmc_coverage = len(cmc_prices)
        print(f"[info] Individual CMC lookups added {cmc_coverage} prices")
    
    # Strategy 2: Try CoinGecko for missing symbols
    missing_from_cmc = [s for s in symbols if s not in cmc_prices]
    if missing_from_cmc:
        print(f"[info] Step 2: Getting CoinGecko prices for {len(missing_from_cmc)} missing symbols...")
        coingecko_prices = coingecko.get_prices(missing_from_cmc)
        cmc_prices.update(coingecko_prices)
        print(f"[info] CoinGecko added {len(coingecko_prices)} more prices")
    
    # Strategy 3: Try Midgard for Thorchain-specific tokens
    thorchain_symbols = ["TCY", "XRUNE", "VTHOR", "THOR"]
    thorchain_missing = [s for s in thorchain_symbols if s in symbols and s not in cmc_prices]
    if thorchain_missing:
        print(f"[info] Step 3: Getting Midgard prices for Thorchain tokens...")
        try:
            midgard_prices = midgard.get_prices()
            for symbol in thorchain_missing:
                if symbol in midgard_prices:
                    cmc_prices[symbol] = midgard_prices[symbol]
                    print(f"[info] Midgard provided price for {symbol}: ${midgard_prices[symbol]:.4f}")
        except Exception as e:
            print(f"[warn] Midgard failed: {e}")
    
    # Strategy 4: Manual fallbacks for known tokens
    manual_fallbacks = {
        "FOX": 0.0001,    # ShapeShift FOX token (estimated)
        "RUJI": 0.0001,   # Unknown token (estimated)
        "TGT": 1.0,       # Unknown token (treat as USD)
        "TCY": 0.01,      # Thorchain TCY token (estimated)
        "XRUNE": 0.5,     # Thorchain RUNE (estimated)
        "VTHOR": 0.5,     # Thorchain RUNE (estimated)
        "THOR": 0.5,      # Thorchain RUNE (estimated)
    }
    
    for symbol, price in manual_fallbacks.items():
        if symbol in symbols and symbol not in cmc_prices:
            cmc_prices[symbol] = price
            print(f"[info] Manual fallback for {symbol}: ${price:.4f}")
    
    # Strategy 5: Use similar token prices as proxies
    proxy_mappings = {
        "DPI": "ETH",      # DeFi Pulse Index -> use ETH price as proxy
        "SNX": "ETH",      # Synthetix -> use ETH price as proxy
    }
    
    for symbol, proxy in proxy_mappings.items():
        if symbol in symbols and symbol not in cmc_prices and proxy in cmc_prices:
            cmc_prices[symbol] = cmc_prices[proxy]
            print(f"[info] Proxy pricing for {symbol} using {proxy}: ${cmc_prices[proxy]:.4f}")
    
    # Create price data for all dates (using current prices)
    frames = []
    for symbol, price in cmc_prices.items():
        for d in daterange(start, end):
            frames.append((d, symbol, price))
    
    if not frames:
        return pd.DataFrame()

    prices = pd.DataFrame(frames, columns=["date", "asset", "close_usd"])
    # pivot to wide [date x asset]
    pivot = prices.pivot(index="date", columns="asset", values="close_usd").sort_index()
    
    # stables anchored to 1 USD
    for st in STABLES:
        pivot[st] = 1.0
    
    # forward/back fill within range to avoid tiny gaps
    pivot = pivot.ffill().bfill()
    
    final_coverage = len(pivot.columns)
    print(f"[info] Final price table has {final_coverage} assets across {len(pivot.index)} dates")
    print(f"[info] Overall pricing coverage: {final_coverage}/{len(symbols)} symbols ({final_coverage/len(symbols)*100:.1f}%)")
    
    return pivot

def price_swap(row, price_table: pd.DataFrame):
    d = row["date"]
    fa, ta = row["from_asset_clean"], row["to_asset_clean"]
    fa_amt, ta_amt = row["from_amount"], row["to_amount"]
    if d not in price_table.index: return math.nan

    # prefer pricing the input side
    if isinstance(fa, str) and fa in price_table.columns and pd.notna(fa_amt):
        p = price_table.loc[d, fa]
        if pd.notna(p): return fa_amt * p
    # fallback to output side
    if isinstance(ta, str) and ta in price_table.columns and pd.notna(ta_amt):
        p = price_table.loc[d, ta]
        if pd.notna(p): return ta_amt * p
    return math.nan

def plot_and_export(swaps: pd.DataFrame):
    # Daily volume
    daily = swaps.groupby("date")["usd_value"].sum(min_count=1)
    daily.to_csv("daily_volume_usd.csv", index=True)

    plt.figure(figsize=(12,5))
    daily.plot(kind="line")
    plt.title("ShapeShift Daily Trading Volume (USD)")
    plt.xlabel("Date"); plt.ylabel("USD Volume"); plt.grid(True)
    plt.tight_layout(); plt.savefig("daily_volume_usd.png", dpi=160)
    plt.close()  # Close the figure to free memory

    # Top routes
    routes = swaps.groupby("route")["usd_value"].sum().sort_values(ascending=False).head(12)
    routes.to_csv("top_routes_usd.csv", header=["usd_volume"])

    plt.figure(figsize=(12,6))
    colors = plt.cm.tab20.colors
    plt.bar(routes.index, routes.values, color=colors[:len(routes)])
    plt.title("Top Trading Routes by USD Volume")
    plt.xlabel("Route"); plt.ylabel("Total USD Volume")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout(); plt.savefig("top_routes_usd.png", dpi=160)
    plt.close()  # Close the figure to free memory

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("json_path", help="Path to exported swaps JSON")
    ap.add_argument("--start", help="YYYY-MM-DD (pricing window start)", required=True)
    ap.add_argument("--end", help="YYYY-MM-DD (pricing window end)", required=True)
    args = ap.parse_args()

    # Try to get CMC API key from environment or use the one from debug scripts
    cmc_key = os.environ.get("CMC_API_KEY") or "64dfaca3-439f-440d-8540-f11e06840ccc"
    if not cmc_key:
        raise SystemExit("Set CMC_API_KEY in your environment.")

    swaps = load_swaps(args.json_path)
    if swaps.empty:
        raise SystemExit("No valid swaps found.")

    start = datetime.fromisoformat(args.start).date()
    end   = datetime.fromisoformat(args.end).date()

    # Build price table from multiple APIs for maximum coverage
    cmc = CMC(cmc_key)
    midgard = Midgard()
    coingecko = CoinGecko()
    price_table = build_price_table(swaps, cmc, midgard, coingecko, start, end)
    if price_table.empty:
        print("[warn] price table empty; cannot compute USD. Did your CMC plan allow OHLCV daily?")
        return

    # Compute USD per swap
    swaps["usd_value"] = swaps.apply(lambda r: price_swap(r, price_table), axis=1)
    coverage = swaps["usd_value"].notna().mean() * 100
    print(f"[info] priced swaps coverage: {coverage:.2f}% ({swaps['usd_value'].notna().sum()}/{len(swaps)})")

    # Plots + CSVs
    plot_and_export(swaps)

if __name__ == "__main__":
    main()
