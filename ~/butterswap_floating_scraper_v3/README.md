# 🦋 ButterSwap Floating Scraper v3.0

**Advanced transaction scraper with enhanced debugging, auto-pagination, and comprehensive data collection**

## ✨ **New in v3.0**

- 🔍 **Enhanced Debug Tools** - Debug page structure and framework detection
- 🧪 **Test Scraping** - Test data extraction without pagination
- 🏗️ **Framework Detection** - Auto-detect UI frameworks (Material-UI, Ant Design, etc.)
- 📊 **Improved Logging** - Better transaction extraction feedback
- 🎯 **Smart Selectors** - Multiple fallback strategies for element detection
- 🚀 **Performance Optimized** - Faster and more reliable scraping

## 🚀 **Features**

### **Core Functionality**
- **Auto-pagination** through all transaction pages
- **Configurable delays** and page limits
- **Real-time progress** tracking
- **ShapeShift affiliate** detection
- **Draggable floating** interface
- **CSV export** functionality

### **Enhanced Debugging**
- **Debug Page Button** - Analyze page structure and framework
- **Test Scraping Button** - Test extraction on current page
- **Framework Detection** - Identify UI frameworks automatically
- **Element Analysis** - Detailed logging of detected elements
- **Extraction Testing** - Validate data extraction before full scraping

### **Smart Data Collection**
- **Multiple Selector Strategies** - Fallback methods for element detection
- **Framework-Aware** - Optimized for Material-UI, Ant Design, etc.
- **Error Handling** - Comprehensive error reporting and recovery
- **Data Validation** - Ensure extracted data quality

## 📦 **Installation**

### **1. Download Extension**
```bash
# Navigate to the extension directory
cd ~/butterswap_floating_scraper_v3
```

### **2. Load in Chrome**
1. **Open Chrome** and go to `chrome://extensions/`
2. **Enable "Developer mode"** (top right toggle)
3. **Click "Load unpacked"** and select this directory
4. **Extension should load** without errors

### **3. Navigate to ButterSwap**
```
https://explorer.butterswap.io/en
```

## 🎮 **Usage**

### **Quick Start**
1. **Click the extension icon** in your toolbar
2. **Floating UI appears** on the page
3. **Click 🧪 Test Scraping** to test current page
4. **Click 🚀 Start Auto-Scraping** for full pagination

### **Debug Tools**

#### **🔍 Debug Page Button**
- Analyzes page structure
- Detects UI frameworks
- Lists all table-like elements
- Shows element counts by type

#### **🧪 Test Scraping Button**
- Tests data extraction on current page
- Shows detailed extraction results
- Logs HTML structure for debugging
- No pagination - just current page analysis

### **Scraping Controls**
- **Page Delay** - Time between page requests (ms)
- **Max Pages** - Safety limit to prevent infinite loops
- **Start/Stop** - Control scraping process
- **Export CSV** - Download collected data

## 🔧 **Configuration**

### **Settings**
- **Page Delay**: 2000ms (2 seconds) - Adjustable 500-10000ms
- **Max Pages**: 1000 - Safety limit for pagination
- **Auto-save**: Settings automatically saved to Chrome storage

### **Customization**
- **Draggable UI** - Move floating interface anywhere
- **Minimize** - Collapse UI to save space
- **Close** - Hide UI completely

## 📊 **Data Output**

### **CSV Export Format**
```csv
page,index,timestamp,txHash,fromAddress,toAddress,tokenIn,tokenOut,amountIn,amountOut,status,chain,isAffiliate,extractedAt
1,1,2024-08-12T...,0x1234...,0xabcd...,0x5678...,UNI,USDC,100,95,success,ethereum,true,2024-08-12T...
```

### **Data Fields**
- **page**: Current page number
- **index**: Transaction index on page
- **timestamp**: When scraping occurred
- **txHash**: Transaction hash
- **fromAddress**: Sender address
- **toAddress**: Recipient address
- **tokenIn**: Input token symbol
- **tokenOut**: Output token symbol
- **amountIn**: Input amount
- **amountOut**: Output amount
- **status**: Transaction status
- **chain**: Detected blockchain
- **isAffiliate**: ShapeShift affiliate flag
- **extractedAt**: Extraction timestamp

## 🐛 **Troubleshooting**

### **No Data Collected**
1. **Click 🔍 Debug Page** - Check page structure
2. **Click 🧪 Test Scraping** - Test extraction
3. **Check Console Logs** - Look for error messages
4. **Verify Page URL** - Must be `explorer.butterswap.io`

### **Common Issues**
- **Extension not loading**: Check manifest.json and file permissions
- **UI not appearing**: Click extension icon on ButterSwap page
- **Scraping stuck**: Use stop button and check logs
- **Export empty**: Ensure transactions were collected first

### **Debug Steps**
1. **Always test first** - Use Test Scraping button
2. **Check logs** - Look for element detection info
3. **Review page structure** - Debug button shows what's detected
4. **Monitor extraction** - Test button shows data extraction

## 🏗️ **Technical Details**

### **Architecture**
- **Manifest V3** - Latest Chrome extension standard
- **Content Scripts** - Injected into web pages
- **Background Service Worker** - Handles extension lifecycle
- **Chrome Storage API** - Persistent settings storage

### **Framework Support**
- **Material-UI** - `.MuiTableRow-root` selectors
- **Ant Design** - `.ant-table-row` selectors
- **Element UI** - `.el-table__row` selectors
- **Vuetify** - `.v-data-table__tr` selectors
- **Quasar** - `.q-table__row` selectors
- **Generic Tables** - Standard `<table>` and `<tr>` elements

### **Selector Strategy**
1. **Framework-specific** selectors first
2. **Data-testid** attributes
3. **Class-based** selectors
4. **Attribute-based** selectors
5. **Text pattern** matching
6. **Generic table** structure fallback

## 📈 **Performance**

### **Optimizations**
- **Efficient selectors** - Minimal DOM queries
- **Batch processing** - Process multiple elements together
- **Memory management** - Clean up after each page
- **Error recovery** - Continue on individual failures

### **Limits**
- **Max Pages**: 1000 (configurable)
- **Page Delay**: 500ms minimum
- **Memory Usage**: Optimized for long-running sessions
- **CPU Usage**: Minimal impact on page performance

## 🔒 **Security & Privacy**

### **Permissions**
- **activeTab** - Access current tab
- **storage** - Save settings locally
- **scripting** - Inject content scripts

### **Data Handling**
- **Local storage only** - No external data transmission
- **User control** - Export data manually
- **No tracking** - Completely private

## 📝 **Changelog**

### **v3.0.0** (Current)
- ✨ Enhanced debugging tools
- 🧪 Test scraping functionality
- 🏗️ Framework detection
- 📊 Improved logging
- 🎯 Smart selector strategies
- 🚀 Performance optimizations

### **v2.0.0**
- 🎨 Modern floating UI
- 📄 Auto-pagination
- 🔄 Progress tracking
- 📈 Statistics display

### **v1.0.0**
- 🚀 Basic scraping functionality
- 📱 Chrome extension
- 📊 CSV export

## 🤝 **Support**

### **Issues**
- **Check logs** - Use debug tools first
- **Test functionality** - Use test button before reporting
- **Verify setup** - Ensure proper installation

### **Development**
- **Source code** - All files included
- **Modifiable** - Easy to customize
- **Extensible** - Add new features easily

## 📄 **License**

This extension is provided as-is for educational and personal use. Use responsibly and in accordance with website terms of service.

---

**🦋 Happy Scraping! ✨🚀**
