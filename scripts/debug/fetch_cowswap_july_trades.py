import requests
from datetime import datetime

# Set your date range for July
from_date = "2024-07-01T00:00:00Z"
to_date = "2024-07-31T23:59:59Z"

url = f"https://api.cow.fi/mainnet/api/v1/trades?from={from_date}&to={to_date}"

response = requests.get(url)
response.raise_for_status()
trades = response.json().get("trades", [])

print(f"Total trades in July: {len(trades)}\n")

app_codes = set()

for t in trades:
    uid = t.get("uid")
    tx_hash = t.get("txHash")
    app_code = t.get("appCode")
    print(f"Trade UID: {uid}\n  Tx: {tx_hash}\n  appCode: {app_code}\n")
    if app_code:
        app_codes.add(app_code)

print("Unique appCodes found in July trades:")
for code in sorted(app_codes):
    print(f"- {code}")
