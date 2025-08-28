// Background Service Worker for ButterSwap Web Scraper Chrome Extension

// Handle extension installation
chrome.runtime.onInstalled.addListener((details) => {
  if (details.reason === 'install') {
    console.log('ButterSwap Web Scraper extension installed');
    
    // Set default settings
    chrome.storage.local.set({
      chain: 'ethereum',
      maxTx: 100,
      version: '1.0.0'
    });
  } else if (details.reason === 'update') {
    console.log('ButterSwap Web Scraper extension updated');
  }
});

// Handle messages from content scripts and popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  switch (request.action) {
    case 'log':
      // Handle log messages from content script
      console.log(`[ButterSwap Scraper] ${request.message}`);
      break;
      
    case 'getTabInfo':
      // Get information about the current tab
      chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        if (tabs[0]) {
          sendResponse({
            url: tabs[0].url,
            title: tabs[0].title,
            isButterSwap: tabs[0].url.includes('explorer.butterswap.io')
          });
        } else {
          sendResponse({ error: 'No active tab found' });
        }
      });
      return true; // Keep message channel open
      
    case 'openButterSwap':
      // Open ButterSwap explorer in new tab
      chrome.tabs.create({
        url: 'https://explorer.butterswap.io/en'
      });
      break;
      
    case 'exportData':
      // Handle data export
      if (request.data && request.data.length > 0) {
        const csvContent = convertToCSV(request.data);
        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        
        chrome.downloads.download({
          url: url,
          filename: `butterswap_transactions_${request.chain}_${new Date().toISOString().split('T')[0]}.csv`,
          saveAs: true
        });
        
        // Clean up the URL object
        setTimeout(() => URL.revokeObjectURL(url), 1000);
      }
      break;
  }
});

// Handle tab updates to inject content script when needed
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === 'complete' && 
      tab.url && 
      tab.url.includes('explorer.butterswap.io')) {
    
    // Inject content script if not already injected
    chrome.scripting.executeScript({
      target: { tabId: tabId },
      files: ['content.js']
    }).catch(error => {
      // Content script might already be injected
      console.log('Content script injection result:', error);
    });
  }
});

// Handle extension icon click
chrome.action.onClicked.addListener((tab) => {
  if (tab.url && tab.url.includes('explorer.butterswap.io')) {
    // Open popup
    chrome.action.openPopup();
  } else {
    // Navigate to ButterSwap explorer
    chrome.tabs.create({
      url: 'https://explorer.butterswap.io/en'
    });
  }
});

// Utility function to convert data to CSV
function convertToCSV(data) {
  if (data.length === 0) return '';
  
  const headers = Object.keys(data[0]);
  const csvRows = [headers.join(',')];
  
  for (const row of data) {
    const values = headers.map(header => {
      const value = row[header];
      if (value === null || value === undefined) return '';
      
      const stringValue = String(value);
      // Escape commas and quotes
      if (stringValue.includes(',') || stringValue.includes('"')) {
        return `"${stringValue.replace(/"/g, '""')}"`;
      }
      return stringValue;
    });
    csvRows.push(values.join(','));
  }
  
  return csvRows.join('\n');
}

// Handle context menu (right-click menu)
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: 'scrapeButterSwap',
    title: 'Scrape ButterSwap Transactions',
    contexts: ['page'],
    documentUrlPatterns: ['*://explorer.butterswap.io/*']
  });
  
  chrome.contextMenus.create({
    id: 'openButterSwap',
    title: 'Open ButterSwap Explorer',
    contexts: ['page']
  });
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
  switch (info.menuItemId) {
    case 'scrapeButterSwap':
      // Send message to content script to start scraping
      chrome.tabs.sendMessage(tab.id, {
        action: 'startScraping',
        chain: 'ethereum',
        maxTx: 100
      });
      break;
      
    case 'openButterSwap':
      chrome.tabs.create({
        url: 'https://explorer.butterswap.io/en'
      });
      break;
  }
});

// Handle storage changes
chrome.storage.onChanged.addListener((changes, namespace) => {
  if (namespace === 'local') {
    console.log('Storage changed:', changes);
  }
});

// Handle extension startup
chrome.runtime.onStartup.addListener(() => {
  console.log('ButterSwap Web Scraper extension started');
});

// Handle extension shutdown
chrome.runtime.onSuspend.addListener(() => {
  console.log('ButterSwap Web Scraper extension suspended');
});

