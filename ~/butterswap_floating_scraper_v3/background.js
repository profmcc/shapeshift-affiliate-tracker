/**
 * ButterSwap Floating Scraper v3.0 - Background Service Worker
 * Handles extension lifecycle, icon clicks, and background tasks
 */

const EXTENSION_VERSION = '3.0.0';
const EXTENSION_NAME = 'ButterSwap Floating Scraper v3.0';

// Handle extension installation
chrome.runtime.onInstalled.addListener((details) => {
  if (details.reason === 'install') {
    console.log(`${EXTENSION_NAME} v${EXTENSION_VERSION} installed successfully`);
    
    // Set default settings
    chrome.storage.local.set({
      pageDelay: 2000,
      maxPages: 1000,
      version: EXTENSION_VERSION,
      installDate: new Date().toISOString(),
      firstRun: true
    });
    
    console.log('Extension installed! Click the icon on ButterSwap explorer to start scraping.');
    
  } else if (details.reason === 'update') {
    const previousVersion = details.previousVersion;
    console.log(`${EXTENSION_NAME} updated from v${previousVersion} to v${EXTENSION_VERSION}`);
    
    // Update version in storage
    chrome.storage.local.set({
      version: EXTENSION_VERSION,
      lastUpdate: new Date().toISOString(),
      previousVersion: previousVersion
    });
    
    console.log(`Updated from v${previousVersion} to v${EXTENSION_VERSION}. New features available!`);
    
  } else if (details.reason === 'chrome_update') {
    console.log('Chrome browser updated, extension reloaded');
  }
});

// Handle extension icon click
chrome.action.onClicked.addListener(async (tab) => {
  try {
    if (tab.url && tab.url.includes('explorer.butterswap.io')) {
      console.log('Extension icon clicked on ButterSwap explorer page');
      
      // Inject the floating UI if not already present
      await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        function: () => {
          // Check if UI already exists
          if (!document.getElementById('butterswap-floating-scraper-v3')) {
            // Dispatch custom event to trigger UI creation
            document.dispatchEvent(new CustomEvent('butterswap-show-ui'));
            console.log('Triggered UI creation event');
          } else {
            console.log('UI already exists, bringing to front');
            // Bring existing UI to front
            const ui = document.getElementById('butterswap-floating-scraper-v3');
            ui.style.zIndex = '10001';
            setTimeout(() => {
              ui.style.zIndex = '10000';
            }, 100);
          }
        }
      });
      
    } else {
      console.log('Extension icon clicked, navigating to ButterSwap explorer');
      
      // Navigate to ButterSwap explorer
      await chrome.tabs.create({
        url: 'https://explorer.butterswap.io/en'
      });
    }
    
  } catch (error) {
    console.error('Error handling extension icon click:', error);
    
    // Try to create a new tab as fallback
    try {
      await chrome.tabs.create({
        url: 'https://explorer.butterswap.io/en'
      });
    } catch (fallbackError) {
      console.error('Fallback navigation also failed:', fallbackError);
    }
  }
});

// Handle storage changes
chrome.storage.onChanged.addListener((changes, namespace) => {
  if (namespace === 'local') {
    console.log('Storage changed:', changes);
    
    // Handle specific setting changes
    if (changes.pageDelay) {
      console.log(`Page delay updated to: ${changes.pageDelay.newValue}ms`);
    }
    
    if (changes.maxPages) {
      console.log(`Max pages updated to: ${changes.maxPages.newValue}`);
    }
    
    if (changes.version) {
      console.log(`Version updated to: ${changes.version.newValue}`);
    }
  }
});

// Handle extension startup
chrome.runtime.onStartup.addListener(() => {
  console.log(`${EXTENSION_NAME} v${EXTENSION_VERSION} started`);
  
  // Check if this is the first startup after install
  chrome.storage.local.get(['firstRun', 'installDate'], (result) => {
    if (result.firstRun) {
      console.log('First run detected, showing welcome message');
      
      // Clear first run flag
      chrome.storage.local.set({ firstRun: false });
      
      console.log('Welcome! Click the extension icon on ButterSwap explorer to start scraping transactions.');
    }
  });
});

// Handle extension shutdown
chrome.runtime.onSuspend.addListener(() => {
  console.log(`${EXTENSION_NAME} v${EXTENSION_VERSION} suspended`);
  
  // Save any pending data
  chrome.storage.local.set({
    lastShutdown: new Date().toISOString()
  });
});

// Handle messages from content scripts
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  console.log('Message received from content script:', message);
  
  try {
    switch (message.type) {
      case 'GET_VERSION':
        sendResponse({ version: EXTENSION_VERSION, name: EXTENSION_NAME });
        break;
        
      case 'GET_SETTINGS':
        chrome.storage.local.get(['pageDelay', 'maxPages'], (result) => {
          sendResponse(result);
        });
        return true; // Keep message channel open for async response
        
      case 'UPDATE_SETTINGS':
        chrome.storage.local.set(message.settings, () => {
          sendResponse({ success: true });
        });
        return true;
        
      case 'EXPORT_DATA':
        // Handle data export request
        console.log('Data export requested:', message.data);
        sendResponse({ success: true, message: 'Export handled by content script' });
        break;
        
      case 'ERROR_REPORT':
        // Log errors for debugging
        console.error('Content script error:', message.error);
        sendResponse({ logged: true });
        break;
        
      default:
        console.log('Unknown message type:', message.type);
        sendResponse({ error: 'Unknown message type' });
    }
    
  } catch (error) {
    console.error('Error handling message:', error);
    sendResponse({ error: error.message });
  }
});

// Handle extension update check
chrome.runtime.requestUpdateCheck((status) => {
  if (status === 'update_available') {
    console.log('Extension update available');
  } else if (status === 'no_update') {
    console.log('Extension is up to date');
  } else if (status === 'throttled') {
    console.log('Update check throttled');
  }
});

// Periodic health check
setInterval(() => {
  chrome.storage.local.get(['lastActivity'], (result) => {
    const now = Date.now();
    const lastActivity = result.lastActivity ? new Date(result.lastActivity).getTime() : 0;
    
    // If no activity for more than 1 hour, log it
    if (now - lastActivity > 3600000) {
      console.log('No recent activity detected');
    }
  });
}, 300000); // Check every 5 minutes

// Handle uninstall
chrome.runtime.setUninstallURL('https://github.com/profmcc/shapeshift-affiliate-tracker');

console.log(`${EXTENSION_NAME} v${EXTENSION_VERSION} background service worker initialized`);
