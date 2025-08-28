import matplotlib.pyplot as plt

# Grouped ETH family (including WETH, stETH, rETH, ETH on chains, and added WETH amounts)
eth_family_total = (
    21251.57
    + 21238.06
    + 13692.85
    + 10612.66
    + 7125.70
    + 379.03
    + 174.81
    + 750000  # previous ETH values
    + 6000
    + 34000
    + 21000  # new WETH + stETH amounts
)

# Grouped BTC family (WBTC + cbBTC + small WBTC from Arbitrum)
btc_family_total = 69525.08 + 626.02 + 85.57

# Other tokens with their values
other_tokens = {
    "ATOM": 52000,
    "RUNE": 80000,
    "OP": 11008.09,
    "GIV": 6940.63,
    "ARB": 4456.25,
    "ENS": 2376.37,
    "PEPE": 379.04,
    "EURC": 51024.85,
    "MOR": 134.51,
    "POL": 96.97,
    "GRT": 96.15,
    "ONDO": 95.81,
    "RLB": 143.23,
    "TRX": 148.67,
    "XRP": 148.76,
    "AAVE": 357.29,
    "AIOZ": 212.62,
    "SHIB": 183.05,
    "USDGLO": 129.78,
    "DOT": 119.56,
    "LUSD": 777.54,
    "DAI": 748.74,
    "USDC (various)": 1827.72,  # sum of small USDC balances (92.18 + 879.54 + 1225.93 + 334.04 + 558.53 + 78.21 + 8549.49 + 1225.83)
}

# Sum USDC total from listed small USDC balances
usdc_total = 92.18 + 879.54 + 1225.93 + 334.04 + 558.53 + 78.21 + 8549.49 + 1225.83

# Replace USDC placeholder with actual sum
other_tokens["USDC (various)"] = usdc_total

# Split other tokens into "minor" for the pie chart
minor_tokens = {k: v for k, v in other_tokens.items() if v < 2000}

# Sum of minor tokens
minor_total = sum(minor_tokens.values())

# Major tokens (everything else)
major_tokens = {
    "ETH Family": eth_family_total,
    "BTC Family": btc_family_total,
    "ATOM": other_tokens["ATOM"],
    "RUNE": other_tokens["RUNE"],
    "OP": other_tokens["OP"],
    "Others (combined)": minor_total,
}

# Labels and values for major pie chart
major_labels = [f"{k}\n${v:,.0f}" for k, v in major_tokens.items()]
major_values = list(major_tokens.values())

# Labels and values for minor pie chart
minor_labels = [f"{k}\n${v:,.0f}" for k, v in minor_tokens.items()]
minor_values = list(minor_tokens.values())

# Plotting
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 9))

# Major pie chart
ax1.pie(
    major_values,
    labels=major_labels,
    autopct="%1.1f%%",
    startangle=140,
    textprops=dict(color="black", fontsize=10),
)
ax1.set_title("Major Portfolio Holdings", fontsize=14)

# Minor pie chart
ax2.pie(
    minor_values,
    labels=minor_labels,
    autopct="%1.1f%%",
    startangle=140,
    textprops=dict(color="black", fontsize=10),
)
ax2.set_title("Minor Portfolio Holdings", fontsize=14)

# Calculate total portfolio value
total_value = sum(major_values)

# Display total below the charts
fig.text(
    0.5, 0.01, f"Total Portfolio Value: ${total_value:,.2f}", ha="center", fontsize=14
)

plt.tight_layout(rect=[0, 0.05, 1, 1])
plt.show()
