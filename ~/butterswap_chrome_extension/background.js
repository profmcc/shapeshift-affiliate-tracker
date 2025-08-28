// Background Service Worker for ButterSwap Web Scraper - Multi-Chain Version

// Handle extension installation
chrome.runtime.onInstalled.addListener((details) => {
  if (details.reason === 'install') {
    console.log('ButterSwap Multi-Chain Web Scraper extension installed');
    
    // Set default settings
    chrome.storage.local.set({
      maxTx: 100,
      version: '1.0.0'
    });
  } else if (details.reason === 'update') {
    console.log('ButterSwap Multi-Chain Web Scraper extension updated');
  }
});

// Handle messages from content scripts and popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  switch (request.action) {
    case 'log':
      console.log(`[ButterSwap Multi-Chain Scraper] ${request.message}`);
      break;
      
    case 'getTabInfo':
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
      return true;
      
    case 'openButterSwap':
      chrome.tabs.create({
        url: 'https://explorer.butterswap.io/en'
      });
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

// Handle storage changes
chrome.storage.onChanged.addListener((changes, namespace) => {
  if (namespace === 'local') {
    console.log('Storage changed:', changes);
  }
});

// Handle extension startup
chrome.runtime.onStartup.addListener(() => {
  console.log('ButterSwap Multi-Chain Web Scraper extension started');
});

// Handle extension shutdown
chrome.runtime.onSuspend.addListener(() => {
  console.log('ButterSwap Multi-Chain Web Scraper extension suspended');
});
