import pandas as pd

# Load daily volume data
daily_df = pd.read_csv('daily_volume_usd.csv')
routes_df = pd.read_csv('top_routes_usd.csv')

print("=== SHAPESHIFT VOLUME ANALYSIS RESULTS ===\n")

# Daily volume summary
print("📊 DAILY VOLUME SUMMARY:")
print(f"Total volume: ${daily_df['usd_value'].sum():,.2f}")
print(f"Average daily volume: ${daily_df['usd_value'].mean():,.2f}")
print(f"Peak day: {daily_df.loc[daily_df['usd_value'].idxmax(), 'date']} - ${daily_df['usd_value'].max():,.2f}")
print(f"Total days with data: {len(daily_df)}")
print(f"Days with >$10k volume: {len(daily_df[daily_df['usd_value'] > 10000])}")
print(f"Days with >$50k volume: {len(daily_df[daily_df['usd_value'] > 50000])}")

print("\n🏆 TOP TRADING ROUTES:")
for i, (_, row) in enumerate(routes_df.head(10).iterrows(), 1):
    print(f"{i:2d}. {row['route']:<20} ${row['usd_volume']:>12,.2f}")

print("\n📈 VOLUME TRENDS:")
# Group by month
daily_df['date'] = pd.to_datetime(daily_df['date'])
daily_df['month'] = daily_df['date'].dt.to_period('M')
monthly = daily_df.groupby('month')['usd_value'].sum()
print("Monthly volumes:")
for month, volume in monthly.items():
    print(f"  {month}: ${volume:>12,.2f}")

print(f"\n✅ Analysis complete! Check the generated PNG files for visualizations.")
