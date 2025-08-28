import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from datetime import datetime, timedelta
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
import warnings
warnings.filterwarnings('ignore')

# Set professional financial chart styling
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

def setup_financial_style():
    """Apply professional financial chart styling."""
    plt.rcParams['figure.facecolor'] = 'white'
    plt.rcParams['axes.facecolor'] = 'white'
    plt.rcParams['axes.grid'] = True
    plt.rcParams['grid.alpha'] = 0.3
    plt.rcParams['axes.spines.top'] = False
    plt.rcParams['axes.spines.right'] = False
    plt.rcParams['font.size'] = 10
    plt.rcParams['axes.titlesize'] = 14
    plt.rcParams['axes.labelsize'] = 11

def create_candlestick_style_volume(df, save_path="enhanced_daily_volume.png"):
    """
    Create a professional candlestick-style volume chart with best practices:
    - Volume bars with color coding (green/red)
    - Moving averages
    - Volume trend analysis
    - Professional styling
    """
    setup_financial_style()
    
    # Prepare data
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    
    # Calculate moving averages
    df['MA7'] = df['usd_value'].rolling(window=7).mean()
    df['MA30'] = df['usd_value'].rolling(window=30).mean()
    
    # Color coding based on volume changes
    df['volume_change'] = df['usd_value'].pct_change()
    df['color'] = np.where(df['volume_change'] >= 0, '#2E8B57', '#DC143C')  # Green/Red
    
    # Create figure with subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10), 
                                   gridspec_kw={'height_ratios': [3, 1]})
    
    # Main volume chart
    bars = ax1.bar(df['date'], df['usd_value'], color=df['color'], alpha=0.7, width=0.8)
    ax1.plot(df['date'], df['MA7'], color='#FF6B6B', linewidth=2, label='7-Day MA')
    ax1.plot(df['date'], df['MA30'], color='#4ECDC4', linewidth=2, label='30-Day MA')
    
    # Highlight peak days
    peak_threshold = df['usd_value'].quantile(0.9)
    peak_days = df[df['usd_value'] >= peak_threshold]
    for _, row in peak_days.iterrows():
        ax1.annotate(f'${row["usd_value"]:,.0f}', 
                     xy=(row['date'], row['usd_value']),
                     xytext=(0, 10), textcoords='offset points',
                     ha='center', va='bottom', fontsize=8,
                     bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7))
    
    ax1.set_title('ShapeShift Daily Trading Volume with Moving Averages', 
                  fontsize=16, fontweight='bold', pad=20)
    ax1.set_ylabel('Daily Volume (USD)', fontsize=12)
    ax1.legend(loc='upper left')
    ax1.grid(True, alpha=0.3)
    
    # Volume change subplot
    ax2.fill_between(df['date'], df['volume_change']*100, 0, 
                     color=df['color'], alpha=0.5)
    ax2.axhline(y=0, color='black', linestyle='-', alpha=0.5)
    ax2.set_ylabel('Volume Change (%)', fontsize=12)
    ax2.set_xlabel('Date', fontsize=12)
    ax2.grid(True, alpha=0.3)
    
    # Format x-axis
    for ax in [ax1, ax2]:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
        ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✅ Enhanced volume chart saved: {save_path}")

def create_route_analysis_chart(routes_df, save_path="enhanced_routes_analysis.png"):
    """
    Create a comprehensive route analysis chart with:
    - Horizontal bar chart (easier to read long labels)
    - Color coding by volume tiers
    - Percentage breakdowns
    - Professional styling
    """
    setup_financial_style()
    
    # Prepare data
    routes_df = routes_df.sort_values('usd_volume', ascending=True)
    total_volume = routes_df['usd_volume'].sum()
    routes_df['percentage'] = (routes_df['usd_volume'] / total_volume * 100).round(1)
    
    # Color coding by volume tiers
    volume_tiers = pd.cut(routes_df['usd_volume'], 
                          bins=[0, 50000, 200000, 500000, float('inf')],
                          labels=['Low', 'Medium', 'High', 'Very High'])
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 10), 
                                   gridspec_kw={'width_ratios': [2, 1]})
    
    # Main horizontal bar chart
    bars = ax1.barh(routes_df['route'], routes_df['usd_volume'], 
                     color=[colors[i] for i in volume_tiers.cat.codes], alpha=0.8)
    
    # Add value labels on bars
    for i, (bar, value, pct) in enumerate(zip(bars, routes_df['usd_volume'], routes_df['percentage'])):
        ax1.text(value + value*0.01, bar.get_y() + bar.get_height()/2, 
                f'${value:,.0f}\n({pct}%)', 
                va='center', ha='left', fontsize=9, fontweight='bold')
    
    ax1.set_title('Top Trading Routes by Volume', fontsize=16, fontweight='bold', pad=20)
    ax1.set_xlabel('Volume (USD)', fontsize=12)
    ax1.grid(True, alpha=0.3, axis='x')
    
    # Volume distribution pie chart
    volume_tier_counts = volume_tiers.value_counts()
    ax2.pie(volume_tier_counts.values, labels=volume_tier_counts.index, 
            autopct='%1.1f%%', startangle=90, colors=colors[:len(volume_tier_counts)])
    ax2.set_title('Volume Distribution by Tier', fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✅ Enhanced routes analysis saved: {save_path}")

def create_heatmap_analysis(daily_df, save_path="volume_heatmap.png"):
    """
    Create a heatmap showing volume patterns:
    - Day of week vs month patterns
    - Volume intensity visualization
    - Professional heatmap styling
    """
    setup_financial_style()
    
    # Prepare data for heatmap
    daily_df['date'] = pd.to_datetime(daily_df['date'])
    daily_df['day_of_week'] = daily_df['date'].dt.day_name()
    daily_df['month'] = daily_df['date'].dt.month_name()
    
    # Create pivot table for heatmap
    heatmap_data = daily_df.pivot_table(
        values='usd_value', 
        index='day_of_week', 
        columns='month', 
        aggfunc='mean'
    ).fillna(0)
    
    # Reorder days and months
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    month_order = ['June', 'July', 'August']
    
    heatmap_data = heatmap_data.reindex(day_order)
    heatmap_data = heatmap_data.reindex(columns=month_order)
    
    # Create heatmap
    plt.figure(figsize=(12, 8))
    sns.heatmap(heatmap_data, annot=True, fmt='.0f', cmap='YlOrRd', 
                cbar_kws={'label': 'Average Daily Volume (USD)'})
    
    plt.title('Trading Volume Patterns: Day of Week vs Month', 
              fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('Month', fontsize=12)
    plt.ylabel('Day of Week', fontsize=12)
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✅ Volume heatmap saved: {save_path}")

def create_cumulative_volume_chart(daily_df, save_path="cumulative_volume.png"):
    """
    Create a cumulative volume chart showing:
    - Running total volume over time
    - Growth rate analysis
    - Milestone markers
    - Professional styling
    """
    setup_financial_style()
    
    # Prepare data
    daily_df['date'] = pd.to_datetime(daily_df['date'])
    daily_df = daily_df.sort_values('date')
    daily_df['cumulative_volume'] = daily_df['usd_value'].cumsum()
    
    # Calculate growth rate
    daily_df['growth_rate'] = daily_df['cumulative_volume'].pct_change() * 100
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10), 
                                   gridspec_kw={'height_ratios': [2, 1]})
    
    # Cumulative volume chart
    ax1.plot(daily_df['date'], daily_df['cumulative_volume'], 
             color='#2E8B57', linewidth=3, alpha=0.8)
    
    # Add milestone markers
    milestones = [1000000, 2000000, 3000000]  # $1M, $2M, $3M
    for milestone in milestones:
        if daily_df['cumulative_volume'].max() >= milestone:
            milestone_date = daily_df[daily_df['cumulative_volume'] >= milestone]['date'].iloc[0]
            ax1.axhline(y=milestone, color='red', linestyle='--', alpha=0.7)
            ax1.annotate(f'${milestone:,}', 
                         xy=(milestone_date, milestone),
                         xytext=(10, 10), textcoords='offset points',
                         bbox=dict(boxstyle='round,pad=0.3', facecolor='red', alpha=0.7),
                         color='white', fontweight='bold')
    
    ax1.set_title('Cumulative Trading Volume Over Time', 
                  fontsize=16, fontweight='bold', pad=20)
    ax1.set_ylabel('Cumulative Volume (USD)', fontsize=12)
    ax1.grid(True, alpha=0.3)
    
    # Growth rate chart
    ax2.plot(daily_df['date'], daily_df['growth_rate'], 
             color='#4ECDC4', linewidth=2, alpha=0.8)
    ax2.axhline(y=0, color='black', linestyle='-', alpha=0.5)
    ax2.set_ylabel('Daily Growth Rate (%)', fontsize=12)
    ax2.set_xlabel('Date', fontsize=12)
    ax2.grid(True, alpha=0.3)
    
    # Format x-axis
    for ax in [ax1, ax2]:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
        ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✅ Cumulative volume chart saved: {save_path}")

def create_summary_dashboard(daily_df, routes_df, save_path="summary_dashboard.png"):
    """
    Create a comprehensive summary dashboard with multiple insights:
    - Key metrics
    - Volume distribution
    - Top routes summary
    - Professional dashboard layout
    """
    setup_financial_style()
    
    # Calculate key metrics
    total_volume = daily_df['usd_value'].sum()
    avg_daily = daily_df['usd_value'].mean()
    peak_day = daily_df.loc[daily_df['usd_value'].idxmax()]
    total_days = len(daily_df)
    
    # Create dashboard
    fig = plt.figure(figsize=(20, 12))
    gs = fig.add_gridspec(3, 4, hspace=0.3, wspace=0.3)
    
    # Title
    fig.suptitle('ShapeShift Trading Volume Analysis Dashboard', 
                 fontsize=20, fontweight='bold', y=0.95)
    
    # Key metrics (top row)
    ax1 = fig.add_subplot(gs[0, :])
    ax1.axis('off')
    
    metrics_text = f"""
    📊 KEY METRICS
    Total Volume: ${total_volume:,.0f} | Average Daily: ${avg_daily:,.0f} | Peak Day: {peak_day['date']} (${peak_day['usd_value']:,.0f})
    Total Days: {total_days} | High Volume Days (>$50k): {len(daily_df[daily_df['usd_value'] > 50000])}
    """
    ax1.text(0.5, 0.5, metrics_text, transform=ax1.transAxes, 
             ha='center', va='center', fontsize=14, fontweight='bold',
             bbox=dict(boxstyle='round,pad=0.5', facecolor='lightblue', alpha=0.7))
    
    # Volume trend (middle left)
    ax2 = fig.add_subplot(gs[1, :2])
    daily_df['date'] = pd.to_datetime(daily_df['date'])
    ax2.plot(daily_df['date'], daily_df['usd_value'], color='#2E8B57', linewidth=2)
    ax2.set_title('Daily Volume Trend', fontweight='bold')
    ax2.set_ylabel('Volume (USD)')
    ax2.grid(True, alpha=0.3)
    
    # Top routes (middle right)
    ax3 = fig.add_subplot(gs[1, 2:])
    top_5 = routes_df.head(5)
    bars = ax3.barh(range(len(top_5)), top_5['usd_volume'], color='#4ECDC4', alpha=0.8)
    ax3.set_yticks(range(len(top_5)))
    ax3.set_yticklabels([route[:20] + '...' if len(route) > 20 else route for route in top_5['route']])
    ax3.set_title('Top 5 Trading Routes', fontweight='bold')
    ax3.set_xlabel('Volume (USD)')
    
    # Volume distribution (bottom)
    ax4 = fig.add_subplot(gs[2, :])
    volume_bins = [0, 10000, 50000, 100000, float('inf')]
    volume_labels = ['<$10k', '$10k-$50k', '$50k-$100k', '>$100k']
    daily_df['volume_bin'] = pd.cut(daily_df['usd_value'], bins=volume_bins, labels=volume_labels)
    volume_dist = daily_df['volume_bin'].value_counts().sort_index()
    
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
    bars = ax4.bar(volume_dist.index, volume_dist.values, color=colors[:len(volume_dist)])
    ax4.set_title('Volume Distribution by Daily Tiers', fontweight='bold')
    ax4.set_ylabel('Number of Days')
    
    # Add value labels on bars
    for bar, value in zip(bars, volume_dist.values):
        ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, 
                str(value), ha='center', va='bottom', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✅ Summary dashboard saved: {save_path}")

def main():
    """Generate all enhanced visualizations."""
    print("🚀 Generating Enhanced Financial Visualizations...")
    
    try:
        # Load data
        daily_df = pd.read_csv('daily_volume_usd.csv')
        routes_df = pd.read_csv('top_routes_usd.csv')
        
        print(f"📊 Loaded data: {len(daily_df)} daily records, {len(routes_df)} routes")
        
        # Generate all visualizations
        create_candlestick_style_volume(daily_df)
        create_route_analysis_chart(routes_df)
        create_heatmap_analysis(daily_df)
        create_cumulative_volume_chart(daily_df)
        create_summary_dashboard(daily_df, routes_df)
        
        print("\n🎉 All enhanced visualizations generated successfully!")
        print("📁 Files created:")
        print("  • enhanced_daily_volume.png - Professional volume chart")
        print("  • enhanced_routes_analysis.png - Route analysis with pie chart")
        print("  • volume_heatmap.png - Day/month volume patterns")
        print("  • cumulative_volume.png - Growth over time")
        print("  • summary_dashboard.png - Comprehensive overview")
        
    except Exception as e:
        print(f"❌ Error generating visualizations: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
