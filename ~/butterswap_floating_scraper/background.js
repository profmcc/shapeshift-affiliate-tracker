// Background Service Worker for ButterSwap Floating Scraper

// Handle extension installation
chrome.runtime.onInstalled.addListener((details) => {
  if (details.reason === 'install') {
    console.log('ButterSwap Floating Scraper extension installed');
    
    // Set default settings
    chrome.storage.local.set({
      maxTx: 100,
      version: '1.0.0'
    });
  } else if (details.reason === 'update') {
    console.log('ButterSwap Floating Scraper extension updated');
  }
});

// Handle extension icon click
chrome.action.onClicked.addListener((tab) => {
  if (tab.url && tab.url.includes('explorer.butterswap.io')) {
    // Inject the floating UI if not already present
    chrome.scripting.executeScript({
      target: { tabId: tab.id },
      function: () => {
        // This will trigger the content script to create the floating UI
        if (!document.getElementById('butterswap-floating-scraper')) {
          // Dispatch a custom event to trigger UI creation
          document.dispatchEvent(new CustomEvent('butterswap-show-ui'));
        }
      }
    });
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
  console.log('ButterSwap Floating Scraper extension started');
});

// Handle extension shutdown
chrome.runtime.onSuspend.addListener(() => {
  console.log('ButterSwap Floating Scraper extension suspended');
});

