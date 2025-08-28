// Popup JavaScript for ButterSwap Web Scraper - Multi-Chain Version

document.addEventListener('DOMContentLoaded', function() {
  const startButton = document.getElementById('start-scraping');
  const stopButton = document.getElementById('stop-scraping');
  const exportButton = document.getElementById('export-data');
  const maxTxInput = document.getElementById('max-tx');
  const statusDiv = document.getElementById('status');
  
  // Chain count elements
  const chainCounts = {
    'ethereum': document.getElementById('eth-count'),
    'polygon': document.getElementById('polygon-count'),
    'optimism': document.getElementById('optimism-count'),
    'arbitrum': document.getElementById('arbitrum-count'),
    'base': document.getElementById('base-count'),
    'avalanche': document.getElementById('avalanche-count'),
    'bsc': document.getElementById('bsc-count')
  };
  
  let isScraping = false;
  
  // Load saved settings
  chrome.storage.local.get(['maxTx'], function(result) {
    if (result.maxTx) maxTxInput.value = result.maxTx;
  });
  
  // Save settings when changed
  maxTxInput.addEventListener('change', function() {
    chrome.storage.local.set({ maxTx: parseInt(maxTxInput.value) });
  });
  
  // Start multi-chain scraping
  startButton.addEventListener('click', function() {
    if (isScraping) return;
    
    isScraping = true;
    startButton.style.display = 'none';
    stopButton.style.display = 'block';
    statusDiv.textContent = 'Starting multi-chain scraper...';
    
    // Reset chain counts
    Object.values(chainCounts).forEach(countEl => {
      countEl.textContent = '0';
    });
    
    // Get current tab
    chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
      const tab = tabs[0];
      
      if (!tab.url.includes('explorer.butterswap.io')) {
        statusDiv.textContent = 'Please navigate to ButterSwap explorer first';
        isScraping = false;
        startButton.style.display = 'block';
        stopButton.style.display = 'none';
        return;
      }
      
      // Send message to content script to start multi-chain scraping
      chrome.tabs.sendMessage(tab.id, {
        action: 'startMultiChainScraping',
        maxTx: parseInt(maxTxInput.value)
      }, function(response) {
        if (response && response.success) {
          statusDiv.textContent = 'Multi-chain scraping started! Check console for progress.';
          // Start monitoring progress
          monitorMultiChainProgress(tab.id);
        } else {
          statusDiv.textContent = 'Failed to start scraping: ' + (response?.error || 'Unknown error');
          isScraping = false;
          startButton.style.display = 'block';
          stopButton.style.display = 'none';
        }
      });
    });
  });
  
  // Stop all scraping
  stopButton.addEventListener('click', function() {
    isScraping = false;
    startButton.style.display = 'block';
    stopButton.style.display = 'none';
    statusDiv.textContent = 'All scraping stopped';
    
    chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
      chrome.tabs.sendMessage(tabs[0].id, {action: 'stopAllScraping'});
    });
  });
  
  // Export all data
  exportButton.addEventListener('click', function() {
    chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
      chrome.tabs.sendMessage(tabs[0].id, {action: 'exportAllData'}, function(response) {
        if (response && response.success) {
          statusDiv.textContent = 'All data exported successfully!';
        } else {
          statusDiv.textContent = 'No data to export or export failed';
        }
      });
    });
  });
  
  // Monitor multi-chain progress
  function monitorMultiChainProgress(tabId) {
    const checkInterval = setInterval(async () => {
      if (!isScraping) {
        clearInterval(checkInterval);
        return;
      }
      
      try {
        const response = await chrome.tabs.sendMessage(tabId, { action: 'getMultiChainStatus' });
        if (response) {
          // Update chain counts
          Object.keys(chainCounts).forEach(chain => {
            if (response.chainData && response.chainData[chain]) {
              chainCounts[chain].textContent = response.chainData[chain].count || 0;
            }
          });
          
          // Update overall status
          if (response.completed) {
            const totalTx = Object.values(response.chainData || {}).reduce((sum, data) => sum + (data.count || 0), 0);
            const totalAffiliate = Object.values(response.chainData || {}).reduce((sum, data) => sum + (data.affiliateCount || 0), 0);
            
            statusDiv.textContent = `Completed! Total: ${totalTx} transactions, ${totalAffiliate} affiliate TX`;
            isScraping = false;
            startButton.style.display = 'block';
            stopButton.style.display = 'none';
            clearInterval(checkInterval);
          }
        }
      } catch (error) {
        // Tab might be closed or navigated away
        clearInterval(checkInterval);
        statusDiv.textContent = 'Lost connection to tab';
        isScraping = false;
        startButton.style.display = 'block';
        stopButton.style.display = 'none';
      }
    }, 2000); // Check every 2 seconds
  }
});
