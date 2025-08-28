// ButterSwap Floating Scraper - Content Script
// This script creates a floating UI and scrapes transaction data

class ButterSwapFloatingScraper {
  constructor() {
    this.isScraping = false;
    this.stopRequested = false;
    this.chainData = {};
    this.maxTransactionsPerChain = 100;
    this.currentChainIndex = 0;
    
    // Supported chains in order
    this.chains = [
      'ethereum',
      'polygon', 
      'optimism',
      'arbitrum',
      'base',
      'avalanche',
      'bsc'
    ];
    
    // ShapeShift affiliate addresses
    this.shapeshiftAffiliates = {
      'ethereum': "0x90A48D5CF7343B08dA12E067680B4C6dbfE551Be",
      'polygon': "0xB5F944600785724e31Edb90F9DFa16dBF01Af000",
      'optimism': "0x6268d07327f4fb7380732dc6d63d95F88c0E083b",
      'arbitrum': "0x38276553F8fbf2A027D901F8be45f00373d8Dd48",
      'base': "0x9c9aA90363630d4ab1D9dbF416cc3BBC8d3Ed502",
      'avalanche': "0x74d63F31C2335b5b3BA7ad2812357672b2624cEd",
      'bsc': "0x8b92b1698b57bEDF2142297e9397875ADBb2297E"
    };
    
    // Initialize chain data
    this.chains.forEach(chain => {
      this.chainData[chain] = {
        transactions: [],
        count: 0,
        affiliateCount: 0,
        completed: false,
        progress: 0
      };
    });
    
    this.init();
  }
  
  init() {
    // Wait for page to load
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => this.createFloatingUI());
    } else {
      this.createFloatingUI();
    }
  }
  
  createFloatingUI() {
    // Check if UI already exists
    if (document.getElementById('butterswap-floating-scraper')) {
      return;
    }
    
    const ui = document.createElement('div');
    ui.id = 'butterswap-floating-scraper';
    ui.innerHTML = `
      <div class="bs-header">
        <h3>🦋 ButterSwap Scraper</h3>
        <div>
          <button class="bs-minimize-btn" title="Minimize">−</button>
          <button class="bs-close-btn" title="Close">×</button>
        </div>
      </div>
      <div class="bs-content">
        <div class="bs-controls">
          <div class="bs-input-group">
            <label for="bs-max-tx">Max transactions per chain:</label>
            <input type="number" id="bs-max-tx" value="100" min="1" max="1000">
          </div>
          
          <button id="bs-start-btn" class="bs-button primary">🚀 Start Multi-Chain Scraping</button>
          <button id="bs-stop-btn" class="bs-button danger bs-hidden">⏹️ Stop All</button>
          <button id="bs-export-btn" class="bs-button secondary">📊 Export All Data</button>
        </div>
        
        <div class="bs-status">
          <h4>📊 Scraping Status</h4>
          <div class="bs-chain-progress" id="bs-chain-progress">
            ${this.chains.map(chain => `
              <div class="bs-chain-item">
                <span class="bs-chain-name">${chain.charAt(0).toUpperCase() + chain.slice(1)}:</span>
                <span class="bs-chain-count" id="bs-${chain}-count">0</span>
              </div>
              <div class="bs-progress-bar">
                <div class="bs-progress-fill" id="bs-${chain}-progress"></div>
              </div>
            `).join('')}
          </div>
        </div>
        
        <div class="bs-log" id="bs-log">
          <div class="bs-log-entry bs-log-info">✅ Extension loaded successfully</div>
          <div class="bs-log-entry bs-log-info">🌐 Ready to scrape ButterSwap explorer</div>
        </div>
      </div>
    `;
    
    document.body.appendChild(ui);
    this.setupEventListeners();
    this.setupDragging();
    this.log('Floating UI created successfully');
  }
  
  setupEventListeners() {
    const startBtn = document.getElementById('bs-start-btn');
    const stopBtn = document.getElementById('bs-stop-btn');
    const exportBtn = document.getElementById('bs-export-btn');
    const maxTxInput = document.getElementById('bs-max-tx');
    const closeBtn = document.querySelector('.bs-close-btn');
    const minimizeBtn = document.querySelector('.bs-minimize-btn');
    
    startBtn.addEventListener('click', () => this.startScraping());
    stopBtn.addEventListener('click', () => this.stopScraping());
    exportBtn.addEventListener('click', () => this.exportData());
    closeBtn.addEventListener('click', () => this.hideUI());
    minimizeBtn.addEventListener('click', () => this.toggleMinimize());
    
    // Save settings
    maxTxInput.addEventListener('change', () => {
      this.maxTransactionsPerChain = parseInt(maxTxInput.value);
      chrome.storage.local.set({ maxTx: this.maxTransactionsPerChain });
    });
    
    // Load saved settings
    chrome.storage.local.get(['maxTx'], (result) => {
      if (result.maxTx) {
        maxTxInput.value = result.maxTx;
        this.maxTransactionsPerChain = result.maxTx;
      }
    });
  }
  
  setupDragging() {
    const ui = document.getElementById('butterswap-floating-scraper');
    const header = ui.querySelector('.bs-header');
    let isDragging = false;
    let startX, startY, startLeft, startTop;
    
    header.addEventListener('mousedown', (e) => {
      if (e.target.closest('button')) return; // Don't drag when clicking buttons
      
      isDragging = true;
      startX = e.clientX;
      startY = e.clientY;
      startLeft = ui.offsetLeft;
      startTop = ui.offsetTop;
      
      ui.classList.add('dragging');
      e.preventDefault();
    });
    
    document.addEventListener('mousemove', (e) => {
      if (!isDragging) return;
      
      const deltaX = e.clientX - startX;
      const deltaY = e.clientY - startY;
      
      ui.style.left = (startLeft + deltaX) + 'px';
      ui.style.top = (startTop + deltaY) + 'px';
      ui.style.right = 'auto';
    });
    
    document.addEventListener('mouseup', () => {
      if (isDragging) {
        isDragging = false;
        ui.classList.remove('dragging');
      }
    });
  }
  
  async startScraping() {
    if (this.isScraping) return;
    
    this.isScraping = true;
    this.stopRequested = false;
    this.currentChainIndex = 0;
    
    // Reset chain data
    this.chains.forEach(chain => {
      this.chainData[chain] = {
        transactions: [],
        count: 0,
        affiliateCount: 0,
        completed: false,
        progress: 0
      };
    });
    
    // Update UI
    document.getElementById('bs-start-btn').classList.add('bs-hidden');
    document.getElementById('bs-stop-btn').classList.remove('bs-hidden');
    
    this.log('🚀 Starting multi-chain scraping...');
    this.log(`📊 Target: ${this.maxTransactionsPerChain} transactions per chain`);
    
    // Start scraping chains sequentially
    await this.scrapeAllChains();
  }
  
  stopScraping() {
    this.stopRequested = true;
    this.isScraping = false;
    
    document.getElementById('bs-start-btn').classList.remove('bs-hidden');
    document.getElementById('bs-stop-btn').classList.add('bs-hidden');
    
    this.log('⏹️ Scraping stopped by user');
  }
  
  async scrapeAllChains() {
    try {
      for (let i = 0; i < this.chains.length; i++) {
        if (this.stopRequested) break;
        
        const chain = this.chains[i];
        this.currentChainIndex = i;
        
        this.log(`🔄 Switching to ${chain} chain...`);
        await this.scrapeChain(chain);
        
        if (i < this.chains.length - 1) {
          await this.wait(1000); // Wait between chains
        }
      }
      
      if (!this.stopRequested) {
        this.log('✅ All chains completed successfully!');
        this.showCompletionSummary();
      }
      
    } catch (error) {
      this.log(`❌ Error during multi-chain scraping: ${error.message}`, 'error');
    } finally {
      this.isScraping = false;
      document.getElementById('bs-start-btn').classList.remove('bs-hidden');
      document.getElementById('bs-stop-btn').classList.add('bs-hidden');
    }
  }
  
  async scrapeChain(chain) {
    try {
      this.log(`🎯 Starting ${chain} chain scraping...`);
      
      // Navigate to the chain
      await this.navigateToChain(chain);
      
      // Wait for page to load
      await this.wait(2000);
      
      // Find transaction elements
      const txElements = this.findTransactionElements();
      this.log(`📊 Found ${txElements.length} transaction elements on ${chain}`);
      
      if (txElements.length === 0) {
        this.log(`⚠️ No transactions found on ${chain}`);
        this.chainData[chain].completed = true;
        this.updateChainProgress(chain, 100);
        return;
      }
      
      // Scrape transactions
      const maxToScrape = Math.min(this.maxTransactionsPerChain, txElements.length);
      this.log(`🎯 Scraping ${maxToScrape} transactions on ${chain}...`);
      
      for (let i = 0; i < maxToScrape; i++) {
        if (this.stopRequested) {
          this.log(`⏹️ Scraping stopped on ${chain}`);
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
            
            // Update progress
            const progress = Math.round(((i + 1) / maxToScrape) * 100);
            this.updateChainProgress(chain, progress);
            
            if (i % 10 === 0) {
              this.log(`${chain}: ${i + 1}/${maxToScrape} transactions scraped`);
            }
          }
          
          await this.wait(100);
          
        } catch (error) {
          this.log(`⚠️ Error scraping transaction ${i + 1} on ${chain}: ${error.message}`, 'warning');
        }
      }
      
      this.chainData[chain].completed = true;
      this.updateChainProgress(chain, 100);
      
      this.log(`✅ ${chain} completed! Found ${this.chainData[chain].count} transactions, ${this.chainData[chain].affiliateCount} affiliate TX`);
      
    } catch (error) {
      this.log(`❌ Error scraping ${chain} chain: ${error.message}`, 'error');
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
            this.log(`✅ Switched to ${chain} chain`);
            await this.wait(2000);
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
      this.log(`⚠️ Error navigating to ${chain} chain: ${error.message}`, 'warning');
    }
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
        this.log(`🎯 Found affiliate transaction on ${chain}: ${txData.txHash}`);
      }
      
      return txData;
      
    } catch (error) {
      this.log(`⚠️ Error extracting transaction ${index} on ${chain}: ${error.message}`, 'warning');
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
  
  isShapeShiftAffiliateTransaction(txData) {
    if (!txData.fromAddress || !txData.toAddress) return false;
    
    const affiliateAddress = this.shapeshiftAffiliates[txData.chain];
    if (!affiliateAddress) return false;
    
    const fromLower = txData.fromAddress.toLowerCase();
    const toLower = txData.toAddress.toLowerCase();
    const affiliateLower = affiliateAddress.toLowerCase();
    
    return fromLower === affiliateLower || toLower === affiliateLower;
  }
  
  updateChainProgress(chain, progress) {
    this.chainData[chain].progress = progress;
    
    // Update count display
    const countEl = document.getElementById(`bs-${chain}-count`);
    if (countEl) {
      countEl.textContent = this.chainData[chain].count;
    }
    
    // Update progress bar
    const progressEl = document.getElementById(`bs-${chain}-progress`);
    if (progressEl) {
      progressEl.style.width = `${progress}%`;
    }
  }
  
  showCompletionSummary() {
    const totalTx = this.chains.reduce((sum, chain) => sum + this.chainData[chain].count, 0);
    const totalAffiliate = this.chains.reduce((sum, chain) => sum + this.chainData[chain].affiliateCount, 0);
    
    this.log(`🎉 Scraping completed!`);
    this.log(`📊 Total transactions: ${totalTx}`);
    this.log(`🎯 Total affiliate transactions: ${totalAffiliate}`);
    
    // Show chain breakdown
    this.chains.forEach(chain => {
      if (this.chainData[chain].count > 0) {
        this.log(`${chain}: ${this.chainData[chain].count} TX, ${this.chainData[chain].affiliateCount} affiliate`);
      }
    });
  }
  
  exportData() {
    const allTransactions = [];
    let totalCount = 0;
    
    // Combine all chain data
    this.chains.forEach(chain => {
      if (this.chainData[chain].transactions.length > 0) {
        allTransactions.push(...this.chainData[chain].transactions);
        totalCount += this.chainData[chain].transactions.length;
      }
    });
    
    if (totalCount === 0) {
      this.log('⚠️ No data to export', 'warning');
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
      this.log('📊 Data exported successfully!');
      
    } catch (error) {
      this.log(`❌ Export failed: ${error.message}`, 'error');
    }
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
  
  hideUI() {
    const ui = document.getElementById('butterswap-floating-scraper');
    if (ui) {
      ui.remove();
    }
  }
  
  toggleMinimize() {
    const ui = document.getElementById('butterswap-floating-scraper');
    ui.classList.toggle('minimized');
  }
  
  log(message, type = 'info') {
    const logContainer = document.getElementById('bs-log');
    if (!logContainer) return;
    
    const logEntry = document.createElement('div');
    logEntry.className = `bs-log-entry bs-log-${type}`;
    logEntry.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
    
    logContainer.appendChild(logEntry);
    logContainer.scrollTop = logContainer.scrollHeight;
    
    // Keep only last 20 log entries
    while (logContainer.children.length > 20) {
      logContainer.removeChild(logContainer.firstChild);
    }
    
    // Also log to console for debugging
    console.log(`[ButterSwap Scraper] ${message}`);
  }
  
  wait(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

// Initialize the floating scraper
new ButterSwapFloatingScraper();

