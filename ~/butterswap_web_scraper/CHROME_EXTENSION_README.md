# 🦋 ButterSwap Web Scraper - Chrome Extension

A Chrome extension that scrapes transaction data from the [ButterSwap Explorer](https://explorer.butterswap.io/en) with copy-paste address handling.

## 🚀 **Installation**

### **Method 1: Load Unpacked Extension (Recommended)**

1. **Download/Clone** this repository to your computer
2. **Open Chrome** and go to `chrome://extensions/`
3. **Enable "Developer mode"** (toggle in top right)
4. **Click "Load unpacked"** and select the `~/butterswap_web_scraper` folder
5. **Pin the extension** to your toolbar for easy access

### **Method 2: From Chrome Web Store**
*Coming soon - extension will be published to the Chrome Web Store*

## 🎯 **How to Use**

### **1. Navigate to ButterSwap Explorer**
- Go to [https://explorer.butterswap.io/en](https://explorer.butterswap.io/en)
- Or click the extension icon to open it automatically

### **2. Open the Extension**
- **Click the extension icon** in your Chrome toolbar
- **Select blockchain network** (Ethereum, Polygon, Optimism, etc.)
- **Set max transactions** to scrape (1-1000)

### **3. Start Scraping**
- **Click "🚀 Start Scraping"**
- Watch real-time progress and logs
- **Stop anytime** with the stop button

### **4. Export Data**
- **Click "📊 Export Data"** when scraping is complete
- Data downloads as CSV file
- Includes all transaction details and addresses

## 🔧 **Features**

- ✅ **Web scraping** directly from Butterswap explorer
- ✅ **Copy-paste address handling** for full addresses
- ✅ **Multi-chain support** (7 blockchain networks)
- ✅ **ShapeShift affiliate detection**
- ✅ **Real-time progress tracking**
- ✅ **CSV data export**
- ✅ **Context menu integration**
- ✅ **Automatic chain detection**

## 🌐 **Supported Chains**

| Chain | Affiliate Address |
|-------|-------------------|
| Ethereum | `0x90A48D5CF7343B08dA12E067680B4C6dbfE551Be` |
| Polygon | `0xB5F944600785724e31Edb90F9DFa16dBF01Af000` |
| Optimism | `0x6268d07327f4fb7380732dc6d63d95F88c0E083b` |
| Arbitrum | `0x38276553F8fbf2A027D901F8be45f00373d8Dd48` |
| Base | `0x9c9aA90363630d4ab1D9dbF416cc3BBC8d3Ed502` |
| Avalanche | `0x74d63F31C2335b5b3BA7ad2812357672b2624cEd` |
| BSC | `0x8b92b1698b57bEDF2142297e9397875ADBb2297E` |

## 📁 **Extension Files**

```
~/butterswap_web_scraper/
├── manifest.json                    ← Extension configuration
├── popup.html                      ← Extension popup interface
├── popup.js                        ← Popup logic
├── content.js                      ← Content script (runs on page)
├── background.js                   ← Background service worker
├── icons/                          ← Extension icons
├── CHROME_EXTENSION_README.md      ← This file
└── [other Python files]            ← Original Python scraper
```

## 🎮 **Usage Tips**

### **Best Practices**
1. **Wait for page to fully load** before starting scraping
2. **Start with small transaction counts** (50-100) to test
3. **Use headless mode** for large scraping jobs
4. **Export data regularly** to avoid losing progress

### **Troubleshooting**
- **Extension not working?** Check if you're on the correct Butterswap page
- **No transactions found?** Wait for page to load completely
- **Copy-paste not working?** Some pages may restrict clipboard access
- **Extension crashes?** Reload the page and try again

## 🔍 **How Address Copy-Paste Works**

1. **Extension finds** address elements on the page
2. **Clicks on addresses** to select them
3. **Uses keyboard shortcuts** (Cmd+C/Ctrl+C) to copy
4. **Retrieves full addresses** from clipboard
5. **Falls back** to direct text extraction if needed

## 🎯 **What Gets Scraped**

- **Transaction hashes** (full 64-character hex)
- **From/To addresses** (full 42-character addresses)
- **Token information** (input/output tokens)
- **Amounts** (exact values)
- **Timestamps** (when transactions occurred)
- **Status** (success, pending, failed)
- **Affiliate detection** (ShapeShift transactions)

## 🚨 **Important Notes**

- **Only works on** `explorer.butterswap.io` pages
- **Requires page access** to scrape data
- **Respects rate limits** to avoid overwhelming the site
- **Data is stored locally** in the extension
- **No data is sent** to external servers

## 🆘 **Support**

### **Common Issues**
1. **"Extension not working"** → Make sure you're on the right page
2. **"No transactions found"** → Wait for page to load completely
3. **"Copy-paste failed"** → Some pages restrict clipboard access

### **Getting Help**
- Check the console logs (F12 → Console)
- Verify you're on the correct Butterswap explorer page
- Try refreshing the page and starting over
- Check if the extension has the necessary permissions

## 🎉 **You're All Set!**

Your ButterSwap web scraper Chrome extension is ready to use! It will:
1. **Scrape transaction data** from the explorer
2. **Handle copy-paste operations** for full addresses
3. **Detect ShapeShift affiliate transactions**
4. **Export everything** to CSV files

Start scraping and discover all the affiliate transactions on Butterswap! 🚀

