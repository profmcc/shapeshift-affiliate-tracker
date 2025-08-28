// Content Script for ButterSwap Web Scraper - Multi-Chain Version

class ButterSwapMultiChainScraper {
  constructor() {
    this.isScraping = false;
    this.stopRequested = false;
    this.chainData = {};
    this.maxTransactionsPerChain = 100;
    
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
    
    // Initialize chain data structure
    Object.keys(this.shapeshiftAffiliates).forEach(chain => {
      this.chainData[chain] = {
        transactions: [],
        count: 0,
        affiliateCount: 0,
        completed: false
      };
    });
    
    this.initializeMessageListener();
    console.log('ButterSwap Multi-Chain Scraper: Content script loaded');
  }
  
  initializeMessageListener() {
    chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
      switch (request.action) {
        case 'startMultiChainScraping':
          this.startMultiChainScraping(request.maxTx, sendResponse);
          return true;
        case 'stopAllScraping':
          this.stopAllScraping(sendResponse);
          return true;
        case 'exportAllData':
          this.exportAllData(sendResponse);
          return true;
        case 'getMultiChainStatus':
          this.getMultiChainStatus(sendResponse);
          return true;
      }
    });
  }
  
  async startMultiChainScraping(maxTx, sendResponse) {
    try {
      this.maxTransactionsPerChain = maxTx;
      this.isScraping = true;
      this.stopRequested = false;
      
      // Reset chain data
      Object.keys(this.chainData).forEach(chain => {
        this.chainData[chain] = {
          transactions: [],
          count: 0,
          affiliateCount: 0,
          completed: false
        };
      });
      
      console.log(`Starting multi-chain scraping, max ${maxTx} transactions per chain`);
      
      // Start scraping all chains in parallel
      this.scrapeAllChains().then(() => {
        console.log('Multi-chain scraping completed');
      });
      
      sendResponse({ success: true });
      
    } catch (error) {
      console.error('Error starting multi-chain scraping:', error);
      sendResponse({ success: false, error: error.message });
    }
  }
  
  stopAllScraping(sendResponse) {
    this.stopRequested = true;
    this.isScraping = false;
    console.log('All chain scraping stopped by user');
    sendResponse({ success: true });
  }
  
  exportAllData(sendResponse) {
    const allTransactions = [];
    let totalCount = 0;
    
    // Combine all chain data
    Object.keys(this.chainData).forEach(chain => {
      if (this.chainData[chain].transactions.length > 0) {
        allTransactions.push(...this.chainData[chain].transactions);
        totalCount += this.chainData[chain].transactions.length;
      }
    });
    
    if (totalCount === 0) {
      sendResponse({ success: false, error: 'No data to export' });
      return;
    }
    
    try {
      const csvContent = this.convertToCSV(allTransactions);
      const blob = new Blob([csvContent], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      
      const a = document.createElement('a');
      a.href = url;
      a.download = `butterswap_all_chains_${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      
      URL.revokeObjectURL(url);
      sendResponse({ success: true });
      
    } catch (error) {
      sendResponse({ success: false, error: error.message });
    }
  }
  
  getMultiChainStatus(sendResponse) {
    const completed = Object.values(this.chainData).every(chain => chain.completed);
    
    sendResponse({
      chainData: this.chainData,
      completed: completed,
      totalTransactions: Object.values(this.chainData).reduce((sum, chain) => sum + chain.count, 0),
      totalAffiliate: Object.values(this.chainData).reduce((sum, chain) => sum + chain.affiliateCount, 0)
    });
  }
  
  async scrapeAllChains() {
    try {
      console.log('Starting to scrape all chains...');
      
      // Wait for page to load
      await this.wait(2000);
      
      // Scrape each chain
      const chainPromises = Object.keys(this.shapeshiftAffiliates).map(chain => 
        this.scrapeChain(chain)
      );
      
      // Wait for all chains to complete
      await Promise.all(chainPromises);
      
      console.log('All chains completed!');
      this.isScraping = false;
      
    } catch (error) {
      console.error('Error during multi-chain scraping:', error);
      this.isScraping = false;
    }
  }
  
  async scrapeChain(chain) {
    try {
      console.log(`Starting to scrape ${chain} chain...`);
      
      // Navigate to the chain if needed
      await this.navigateToChain(chain);
      
      // Wait for transactions to load
      await this.waitForTransactions();
      
      // Find transaction elements
      const txElements = this.findTransactionElements();
      console.log(`Found ${txElements.length} transaction elements on ${chain}`);
      
      if (txElements.length === 0) {
        console.log(`No transactions found on ${chain}`);
        this.chainData[chain].completed = true;
        return;
      }
      
      // Scrape transactions for this chain
      const maxToScrape = Math.min(this.maxTransactionsPerChain, txElements.length);
      console.log(`Scraping ${maxToScrape} transactions on ${chain}...`);
      
      for (let i = 0; i < maxToScrape; i++) {
        if (this.stopRequested) {
          console.log(`Scraping stopped on ${chain}`);
          break;
        }
        
        try {
          const txData = await this.extractTransactionData(txElements[i], i + 1, chain);
          if (txData) {
            this.chainData[chain].transactions.push(txData);
            this.chainData[chain].count++;
            
            if (txData.isAffiliate) {
              this.chainData[chain].affiliateCount++;
            }
            
            if (i % 10 === 0) {
              console.log(`${chain} progress: ${i + 1}/${maxToScrape} transactions scraped`);
            }
          }
          
          await this.wait(100);
          
        } catch (error) {
          console.warn(`Error scraping transaction ${i + 1} on ${chain}:`, error);
        }
      }
      
      console.log(`${chain} completed! Found ${this.chainData[chain].count} transactions, ${this.chainData[chain].affiliateCount} affiliate TX`);
      this.chainData[chain].completed = true;
      
    } catch (error) {
      console.error(`Error scraping ${chain} chain:`, error);
      this.chainData[chain].completed = true;
    }
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
            console.log(`Switched to ${chain} chain`);
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
            console.log(`Switched to ${chain} chain`);
            await this.wait(2000);
          }
        }
      } else {
        console.log(`Chain selector not found, assuming ${chain} chain`);
      }
      
    } catch (error) {
      console.warn(`Error navigating to ${chain} chain:`, error);
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
    // Try different selectors to find transaction elements
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
  
  async extractTransactionData(element, index, chain) {
    try {
      const txData = {
        index,
        chain: chain,
        timestamp: new Date().toISOString(),
        isAffiliate: false
      };
      
      // Extract transaction hash
      txData.txHash = this.extractTransactionHash(element);
      if (!txData.txHash) return null;
      
      // Extract addresses
      txData.fromAddress = this.extractAddress(element, 'from');
      txData.toAddress = this.extractAddress(element, 'to');
      
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
        console.log(`Found affiliate transaction on ${chain}: ${txData.txHash}`);
      }
      
      return txData;
      
    } catch (error) {
      console.warn(`Error extracting transaction ${index} on ${chain}:`, error);
      return null;
    }
  }
  
  extractTransactionHash(element) {
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
  
  extractAddress(element, type) {
    const selectors = [
      `[data-testid="${type}-address"]`,
      `.${type}-address`,
      `.${type === 'from' ? 'sender' : 'recipient'}`
    ];
    
    for (const selector of selectors) {
      const addressElement = element.querySelector(selector);
      if (addressElement) {
        return addressElement.textContent?.trim() || null;
      }
    }
    
    return null;
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
    
    const affiliateAddress = this.shapeshiftAffiliates[txData.chain];
    if (!affiliateAddress) return false;
    
    const fromLower = txData.fromAddress.toLowerCase();
    const toLower = txData.toAddress.toLowerCase();
    const affiliateLower = affiliateAddress.toLowerCase();
    
    return fromLower === affiliateLower || toLower === affiliateLower;
  }
  
  wait(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
  
  convertToCSV(data) {
    if (data.length === 0) return '';
    
    const headers = Object.keys(data[0]);
    const csvRows = [headers.join(',')];
    
    for (const row of data) {
      const values = headers.map(header => {
        const value = row[header];
        if (value === null || value === undefined) return '';
        
        const stringValue = String(value);
        if (stringValue.includes(',') || stringValue.includes('"')) {
          return `"${stringValue.replace(/"/g, '""')}"`;
        }
        return stringValue;
      });
      csvRows.push(values.join(','));
    }
    
    return csvRows.join('\n');
  }
}

// Initialize the multi-chain scraper
new ButterSwapMultiChainScraper();
