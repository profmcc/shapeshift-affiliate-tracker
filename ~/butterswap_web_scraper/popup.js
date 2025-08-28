// Popup JavaScript for ButterSwap Web Scraper Chrome Extension

class ButterSwapScraperPopup {
  constructor() {
    this.isScraping = false;
    this.scrapedData = [];
    this.currentChain = 'ethereum';
    this.maxTransactions = 100;
    
    this.initializeElements();
    this.bindEvents();
    this.loadSettings();
  }
  
  initializeElements() {
    this.chainSelect = document.getElementById('chain-select');
    this.maxTxInput = document.getElementById('max-tx');
    this.startButton = document.getElementById('start-scraping');
    this.stopButton = document.getElementById('stop-scraping');
    this.exportButton = document.getElementById('export-data');
    this.statusSpan = document.getElementById('scraping-status');
    this.txCountSpan = document.getElementById('tx-count');
    this.affiliateCountSpan = document.getElementById('affiliate-count');
    this.progressBar = document.getElementById('progress-bar');
    this.logContainer = document.querySelector('.log');
  }
  
  bindEvents() {
    this.startButton.addEventListener('click', () => this.startScraping());
    this.stopButton.addEventListener('click', () => this.stopScraping());
    this.exportButton.addEventListener('click', () => this.exportData());
    this.chainSelect.addEventListener('change', (e) => this.currentChain = e.target.value);
    this.maxTxInput.addEventListener('change', (e) => this.maxTransactions = parseInt(e.target.value));
  }
  
  loadSettings() {
    chrome.storage.local.get(['chain', 'maxTx'], (result) => {
      if (result.chain) {
        this.currentChain = result.chain;
        this.chainSelect.value = this.currentChain;
      }
      if (result.maxTx) {
        this.maxTransactions = result.maxTx;
        this.maxTxInput.value = this.maxTransactions;
      }
    });
  }
  
  saveSettings() {
    chrome.storage.local.set({
      chain: this.currentChain,
      maxTx: this.maxTransactions
    });
  }
  
  async startScraping() {
    if (this.isScraping) return;
    
    this.isScraping = true;
    this.updateUI('scraping');
    this.saveSettings();
    
    try {
      // Get the active tab
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      
      if (!tab.url.includes('explorer.butterswap.io')) {
        this.log('❌ Please navigate to ButterSwap explorer first', 'error');
        this.updateUI('error');
        return;
      }
      
      this.log('🚀 Starting scraping process...', 'info');
      
      // Send message to content script to start scraping
      const response = await chrome.tabs.sendMessage(tab.id, {
        action: 'startScraping',
        chain: this.currentChain,
        maxTx: this.maxTransactions
      });
      
      if (response && response.success) {
        this.log('✅ Scraping started successfully', 'info');
        this.monitorScraping(tab.id);
      } else {
        throw new Error(response?.error || 'Failed to start scraping');
      }
      
    } catch (error) {
      this.log(`❌ Error starting scraping: ${error.message}`, 'error');
      this.updateUI('error');
    }
  }
  
  async stopScraping() {
    this.isScraping = false;
    this.updateUI('stopped');
    
    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      await chrome.tabs.sendMessage(tab.id, { action: 'stopScraping' });
      this.log('⏹️ Scraping stopped', 'warning');
    } catch (error) {
      this.log(`⚠️ Error stopping scraping: ${error.message}`, 'warning');
    }
  }
  
  async monitorScraping(tabId) {
    const checkInterval = setInterval(async () => {
      if (!this.isScraping) {
        clearInterval(checkInterval);
        return;
      }
      
      try {
        const response = await chrome.tabs.sendMessage(tabId, { action: 'getStatus' });
        if (response) {
          this.updateProgress(response.progress, response.totalTx, response.affiliateTx);
          
          if (response.completed) {
            this.scrapedData = response.data || [];
            this.updateUI('completed');
            this.log(`✅ Scraping completed! Found ${response.totalTx} transactions`, 'info');
            clearInterval(checkInterval);
          }
        }
      } catch (error) {
        // Tab might be closed or navigated away
        clearInterval(checkInterval);
        this.updateUI('error');
        this.log('❌ Lost connection to tab', 'error');
      }
    }, 1000);
  }
  
  updateUI(status) {
    switch (status) {
      case 'scraping':
        this.startButton.classList.add('hidden');
        this.stopButton.classList.remove('hidden');
        this.statusSpan.textContent = 'Scraping...';
        this.statusSpan.className = 'status-value';
        break;
        
      case 'completed':
        this.startButton.classList.remove('hidden');
        this.stopButton.classList.add('hidden');
        this.statusSpan.textContent = 'Completed';
        this.statusSpan.className = 'status-value';
        break;
        
      case 'stopped':
        this.startButton.classList.remove('hidden');
        this.stopButton.classList.add('hidden');
        this.statusSpan.textContent = 'Stopped';
        this.statusSpan.className = 'status-value';
        break;
        
      case 'error':
        this.startButton.classList.remove('hidden');
        this.stopButton.classList.add('hidden');
        this.statusSpan.textContent = 'Error';
        this.statusSpan.className = 'status-value';
        break;
        
      default:
        this.startButton.classList.remove('hidden');
        this.stopButton.classList.add('hidden');
        this.statusSpan.textContent = 'Ready';
        this.statusSpan.className = 'status-value';
    }
  }
  
  updateProgress(progress, totalTx, affiliateTx) {
    this.progressBar.style.width = `${progress}%`;
    this.txCountSpan.textContent = totalTx || 0;
    this.affiliateCountSpan.textContent = affiliateTx || 0;
  }
  
  log(message, type = 'info') {
    const logEntry = document.createElement('div');
    logEntry.className = `log-entry log-${type}`;
    logEntry.textContent = message;
    
    this.logContainer.appendChild(logEntry);
    this.logContainer.scrollTop = this.logContainer.scrollHeight;
    
    // Keep only last 20 log entries
    while (this.logContainer.children.length > 20) {
      this.logContainer.removeChild(this.logContainer.firstChild);
    }
  }
  
  async exportData() {
    if (this.scrapedData.length === 0) {
      this.log('⚠️ No data to export', 'warning');
      return;
    }
    
    try {
      const csvContent = this.convertToCSV(this.scrapedData);
      const blob = new Blob([csvContent], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      
      const a = document.createElement('a');
      a.href = url;
      a.download = `butterswap_transactions_${this.currentChain}_${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      
      URL.revokeObjectURL(url);
      this.log('📊 Data exported successfully', 'info');
      
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
        return typeof value === 'string' && value.includes(',') ? `"${value}"` : value;
      });
      csvRows.push(values.join(','));
    }
    
    return csvRows.join('\n');
  }
}

// Initialize the popup when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  new ButterSwapScraperPopup();
});

