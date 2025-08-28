// Content Script for ButterSwap Web Scraper Chrome Extension
// This script runs on the Butterswap explorer page

class ButterSwapContentScraper {
  constructor() {
    this.isScraping = false;
    this.stopRequested = false;
    this.scrapedData = [];
    this.currentChain = 'ethereum';
    this.maxTransactions = 100;
    
    // ShapeShift affiliate addresses by chain
    this.shapeshiftAffiliates = {
      'ethereum': "0x90A48D5CF7343B08dA12E067680B4C6dbfE551Be",
      'polygon': "0xB5F944600785724e31Edb90F9DFa16dBF01Af000",
      'optimism': "0x6268d07327f4fb7380732dc6d63d95F88c0E083b",
      'arbitrum': "0x38276553F8fbf2A027D901F8be45f00373d8Dd48",
      'base': "0x9c9aA90363630d4ab1D9dbF416cc3BBC8d3Ed502",
      'avalanche': "0x74d63F31C2335b5b3BA7ad2812357672b2624cEd",
      'bsc': "0x8b92b1698b57bEDF2142297e9397875ADBb2297E"
    };
    
    this.initializeMessageListener();
    this.log('Content script loaded and ready');
  }
  
  initializeMessageListener() {
    chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
      switch (request.action) {
        case 'startScraping':
          this.startScraping(request.chain, request.maxTx, sendResponse);
          return true; // Keep message channel open for async response
          
        case 'stopScraping':
          this.stopScraping(sendResponse);
          return true;
          
        case 'getStatus':
          this.getStatus(sendResponse);
          return true;
      }
    });
  }
  
  async startScraping(chain, maxTx, sendResponse) {
    try {
      this.currentChain = chain;
      this.maxTransactions = maxTx;
      this.isScraping = true;
      this.stopRequested = false;
      this.scrapedData = [];
      
      this.log(`🚀 Starting scraping for ${chain} chain, max ${maxTx} transactions`);
      
      // Navigate to the correct chain if needed
      await this.navigateToChain(chain);
      
      // Start the scraping process
      const result = await this.scrapeTransactions();
      
      sendResponse({
        success: true,
        message: 'Scraping started successfully',
        data: result
      });
      
    } catch (error) {
      this.log(`❌ Error starting scraping: ${error.message}`, 'error');
      sendResponse({
        success: false,
        error: error.message
      });
    }
  }
  
  stopScraping(sendResponse) {
    this.stopRequested = true;
    this.isScraping = false;
    this.log('⏹️ Scraping stopped by user');
    sendResponse({ success: true });
  }
  
  getStatus(sendResponse) {
    const totalTx = this.scrapedData.length;
    const affiliateTx = this.scrapedData.filter(tx => tx.isAffiliate).length;
    const progress = this.maxTransactions > 0 ? Math.min(100, (totalTx / this.maxTransactions) * 100) : 0;
    
    sendResponse({
      progress: Math.round(progress),
      totalTx,
      affiliateTx,
      completed: !this.isScraping && totalTx > 0,
      data: this.scrapedData
    });
  }
  
  async navigateToChain(chain) {
    try {
      // Look for chain selector
      const chainSelectors = [
        '[data-testid="chain-selector"]',
        '.chain-selector',
        'select[data-testid*="chain"]',
        'select'
      ];
      
      let chainSelector = null;
      for (const selector of chainSelectors) {
        chainSelector = document.querySelector(selector);
        if (chainSelector) break;
      }
      
      if (chainSelector) {
        if (chainSelector.tagName === 'SELECT') {
          // Handle dropdown select
          const options = Array.from(chainSelector.options);
          const targetOption = options.find(option => 
            option.text.toLowerCase().includes(chain.toLowerCase()) ||
            option.value.toLowerCase().includes(chain.toLowerCase())
          );
          
          if (targetOption) {
            chainSelector.value = targetOption.value;
            chainSelector.dispatchEvent(new Event('change'));
            this.log(`✅ Switched to ${chain} chain`);
            await this.wait(2000); // Wait for page to update
          }
        } else {
          // Handle clickable chain selector
          chainSelector.click();
          await this.wait(1000);
          
          // Look for chain option
          const chainOption = document.querySelector(`[data-value="${chain}"], [data-chain="${chain}"]`) ||
                             Array.from(document.querySelectorAll('*')).find(el => 
                               el.textContent.toLowerCase().includes(chain.toLowerCase())
                             );
          
          if (chainOption) {
            chainOption.click();
            this.log(`✅ Switched to ${chain} chain`);
            await this.wait(2000);
          }
        }
      } else {
        this.log(`⚠️ Chain selector not found, assuming ${chain} chain`);
      }
      
    } catch (error) {
      this.log(`⚠️ Error navigating to chain: ${error.message}`, 'warning');
    }
  }
  
  async scrapeTransactions() {
    try {
      this.log('🔍 Looking for transaction elements...');
      
      // Wait for transactions to load
      await this.waitForTransactions();
      
      // Find transaction elements
      const txElements = this.findTransactionElements();
      this.log(`📊 Found ${txElements.length} transaction elements`);
      
      if (txElements.length === 0) {
        throw new Error('No transaction elements found');
      }
      
      // Scrape transactions
      const maxToScrape = Math.min(this.maxTransactions, txElements.length);
      this.log(`🎯 Scraping ${maxToScrape} transactions...`);
      
      for (let i = 0; i < maxToScrape; i++) {
        if (this.stopRequested) {
          this.log('⏹️ Scraping stopped by user');
          break;
        }
        
        try {
          const txData = await this.extractTransactionData(txElements[i], i + 1);
          if (txData) {
            this.scrapedData.push(txData);
            
            // Update progress
            if (i % 10 === 0) {
              this.log(`📈 Progress: ${i + 1}/${maxToScrape} transactions scraped`);
            }
          }
          
          // Small delay to avoid overwhelming the page
          await this.wait(100);
          
        } catch (error) {
          this.log(`⚠️ Error scraping transaction ${i + 1}: ${error.message}`, 'warning');
        }
      }
      
      this.log(`✅ Scraping completed! Found ${this.scrapedData.length} transactions`);
      this.isScraping = false;
      
      return this.scrapedData;
      
    } catch (error) {
      this.log(`❌ Error during scraping: ${error.message}`, 'error');
      this.isScraping = false;
      throw error;
    }
  }
  
  async waitForTransactions() {
    const maxWait = 10000; // 10 seconds
    const startTime = Date.now();
    
    while (Date.now() - startTime < maxWait) {
      const elements = this.findTransactionElements();
      if (elements.length > 0) {
        return;
      }
      await this.wait(500);
    }
    
    throw new Error('Timeout waiting for transactions to load');
  }
  
  findTransactionElements() {
    const selectors = [
      '[data-testid="transaction"]',
      '.transaction',
      '.tx-item',
      'tr[data-testid*="tx"]',
      'tr'
    ];
    
    for (const selector of selectors) {
      const elements = document.querySelectorAll(selector);
      if (elements.length > 0) {
        return Array.from(elements);
      }
    }
    
    return [];
  }
  
  async extractTransactionData(element, index) {
    try {
      const txData = {
        index,
        chain: this.currentChain,
        timestamp: new Date().toISOString(),
        isAffiliate: false
      };
      
      // Extract transaction hash
      txData.txHash = this.extractTransactionHash(element);
      if (!txData.txHash) return null;
      
      // Extract addresses
      txData.fromAddress = await this.extractAddress(element, 'from');
      txData.toAddress = await this.extractAddress(element, 'to');
      
      // Extract token information
      txData.tokenIn = this.extractText(element, 'token-in', 'input-token');
      txData.tokenOut = this.extractText(element, 'token-out', 'output-token');
      
      // Extract amounts
      txData.amountIn = this.extractText(element, 'amount-in', 'input-amount');
      txData.amountOut = this.extractText(element, 'amount-out', 'output-amount');
      
      // Extract status
      txData.status = this.extractText(element, 'status', 'tx-status') || 'unknown';
      
      // Check if this is a ShapeShift affiliate transaction
      txData.isAffiliate = this.isShapeShiftAffiliateTransaction(txData);
      
      if (txData.isAffiliate) {
        this.log(`🎯 Found affiliate transaction: ${txData.txHash}`);
      }
      
      return txData;
      
    } catch (error) {
      this.log(`⚠️ Error extracting transaction ${index}: ${error.message}`, 'warning');
      return null;
    }
  }
  
  extractTransactionHash(element) {
    // Look for hash in various formats
    const hashPattern = /0x[a-fA-F0-9]{64}/;
    
    // Try to find hash element
    const hashSelectors = [
      '[data-testid="tx-hash"]',
      '.tx-hash',
      '.hash',
      'a[href*="tx"]'
    ];
    
    for (const selector of hashSelectors) {
      const hashElement = element.querySelector(selector);
      if (hashElement) {
        const text = hashElement.textContent || hashElement.href || '';
        const match = text.match(hashPattern);
        if (match) return match[0];
      }
    }
    
    // Fallback: search in element text
    const text = element.textContent || '';
    const match = text.match(hashPattern);
    return match ? match[0] : null;
  }
  
  async extractAddress(element, type) {
    try {
      const selectors = [
        `[data-testid="${type}-address"]`,
        `.${type}-address`,
        `.${type === 'from' ? 'sender' : 'recipient'}`
      ];
      
      let addressElement = null;
      for (const selector of selectors) {
        addressElement = element.querySelector(selector);
        if (addressElement) break;
      }
      
      if (!addressElement) return null;
      
      // Try to get full address via copy-paste
      const fullAddress = await this.copyAddressToClipboard(addressElement);
      if (fullAddress && this.isValidAddress(fullAddress)) {
        return fullAddress;
      }
      
      // Fallback to direct text
      return addressElement.textContent?.trim() || null;
      
    } catch (error) {
      this.log(`⚠️ Error extracting ${type} address: ${error.message}`, 'warning');
      return null;
    }
  }
  
  async copyAddressToClipboard(element) {
    try {
      // Click to select the element
      element.click();
      await this.wait(100);
      
      // Use keyboard shortcuts to copy
      element.focus();
      element.select();
      
      // Simulate Cmd+C (or Ctrl+C on Windows)
      const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;
      const key = isMac ? 'Meta' : 'Control';
      
      element.dispatchEvent(new KeyboardEvent('keydown', { key, metaKey: isMac, ctrlKey: !isMac }));
      element.dispatchEvent(new KeyboardEvent('keydown', { key: 'c', metaKey: isMac, ctrlKey: !isMac }));
      element.dispatchEvent(new KeyboardEvent('keyup', { key: 'c', metaKey: isMac, ctrlKey: !isMac }));
      element.dispatchEvent(new KeyboardEvent('keyup', { key, metaKey: isMac, ctrlKey: !isMac }));
      
      await this.wait(100);
      
      // Try to get from clipboard (this might not work due to security restrictions)
      try {
        const clipboardText = await navigator.clipboard.readText();
        if (clipboardText && this.isValidAddress(clipboardText)) {
          return clipboardText.trim();
        }
      } catch (e) {
        // Clipboard access might be restricted
      }
      
      // Fallback: return the element text
      return element.textContent?.trim() || null;
      
    } catch (error) {
      this.log(`⚠️ Copy-paste failed: ${error.message}`, 'warning');
      return element.textContent?.trim() || null;
    }
  }
  
  extractText(element, ...selectors) {
    for (const selector of selectors) {
      const el = element.querySelector(`[data-testid="${selector}"], .${selector}`);
      if (el) {
        return el.textContent?.trim() || null;
      }
    }
    return null;
  }
  
  isValidAddress(address) {
    return /^0x[a-fA-F0-9]{40}$/.test(address);
  }
  
  isShapeShiftAffiliateTransaction(txData) {
    if (!txData.fromAddress || !txData.toAddress) return false;
    
    const affiliateAddress = this.shapeshiftAffiliates[this.currentChain];
    if (!affiliateAddress) return false;
    
    const fromLower = txData.fromAddress.toLowerCase();
    const toLower = txData.toAddress.toLowerCase();
    const affiliateLower = affiliateAddress.toLowerCase();
    
    return fromLower === affiliateLower || toLower === affiliateLower;
  }
  
  wait(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
  
  log(message, type = 'info') {
    console.log(`[ButterSwap Scraper] ${message}`);
    
    // Also send to popup if available
    try {
      chrome.runtime.sendMessage({
        action: 'log',
        message,
        type
      });
    } catch (e) {
      // Popup might not be open
    }
  }
}

// Initialize the scraper when the page loads
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    new ButterSwapContentScraper();
  });
} else {
  new ButterSwapContentScraper();
}

