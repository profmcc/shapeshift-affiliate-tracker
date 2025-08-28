# 🦋 ButterSwap Web Scraper - Multi-Chain Chrome Extension

A Chrome extension that scrapes transaction data from **ALL chains** on the [ButterSwap Explorer](https://explorer.butterswap.io/en) simultaneously.

## 🚀 **Installation**

1. **Open Chrome** and go to `chrome://extensions/`
2. **Enable "Developer mode"** (toggle in top right)
3. **Click "Load unpacked"** and select this folder
4. **Pin the extension** to your toolbar

## 🎯 **How to Use**

1. **Navigate to** [https://explorer.butterswap.io/en](https://explorer.butterswap.io/en)
2. **Click the extension icon** in your toolbar
3. **Set max transactions per chain** (1-1000)
4. **Click "🚀 Start Multi-Chain Scraping"**
5. **Watch real-time progress** for each chain
6. **Click "📊 Export All Data"** to download combined CSV

## 🔧 **Features**

- ✅ **Multi-chain scraping** - All 7 chains simultaneously
- ✅ **Real-time progress tracking** for each chain
- ✅ **ShapeShift affiliate detection** across all networks
- ✅ **Combined CSV export** with all chain data
- ✅ **Chain-specific transaction counts** and affiliate counts
- ✅ **Simple, clean interface**

## 🌐 **Supported Chains (All Scraped Simultaneously)**

| Chain | Affiliate Address | Status |
|-------|-------------------|---------|
| Ethereum | `0x90A48D5CF7343B08dA12E067680B4C6dbfE551Be` | ✅ |
| Polygon | `0xB5F944600785724e31Edb90F9DFa16dBF01Af000` | ✅ |
| Optimism | `0x6268d07327f4fb7380732dc6d63d95F88c0E083b` | ✅ |
| Arbitrum | `0x38276553F8fbf2A027D901F8be45f00373d8Dd48` | ✅ |
| Base | `0x9c9aA90363630d4ab1D9dbF416cc3BBC8d3Ed502` | ✅ |
| Avalanche | `0x74d63F31C2335b5b3BA7ad2812357672b2624cEd` | ✅ |
| BSC | `0x8b92b1698b57bEDF2142297e9397875ADBb2297E` | ✅ |

## 📁 **Files**

- `manifest.json` - Extension configuration
- `popup.html` - Multi-chain popup interface
- `popup.js` - Multi-chain popup logic
- `content.js` - Multi-chain scraping logic
- `background.js` - Background service worker
- `icon*.png` - Extension icons
- `README.md` - This file

## 🎮 **Usage Tips**

### **Best Practices**
1. **Wait for page to fully load** before starting scraping
2. **Start with small transaction counts** (50-100 per chain) to test
3. **Check the console** (F12) for detailed progress for each chain
4. **Use the stop button** if you need to interrupt all chains

### **What Happens During Scraping**
1. **Extension automatically switches** between all 7 chains
2. **Scrapes transactions** from each chain sequentially
3. **Updates progress** for each chain in real-time
4. **Combines all data** into one comprehensive dataset
5. **Exports everything** to a single CSV file

## 🎉 **Ready to Use!**

The extension now scrapes **ALL chains simultaneously** instead of just one! You'll get comprehensive data from every blockchain network in one go.

Just load the extension and start multi-chain scraping! 🚀
