// ==Chainflip Transaction Scraper Content Script==

// --- State ---
let autoPagingState = {
    isActive: false,
    currentPage: 1,
    maxPages: 10,
    delay: 2000,
    capturedTransactions: [],
    stopRequested: false
};

// --- UI Creation ---
function createFloatingUI() {
    // Remove existing UI if present
    const existing = document.getElementById('chainflip-floating-ui');
    if (existing) existing.remove();

    const ui = document.createElement('div');
    ui.id = 'chainflip-floating-ui';
    ui.innerHTML = `
        <div id="ui-header">
            <span id="ui-title">Chainflip Scraper</span>
            <div id="ui-controls">
                <button id="ui-minimize" title="Minimize">−</button>
                <button id="ui-close" title="Close">×</button>
            </div>
        </div>
        <div id="ui-content">
            <div id="ui-status">
                <div id="status-text">Ready</div>
                <div id="progress-info">Page: ${autoPagingState.currentPage} | Captured: ${autoPagingState.capturedTransactions.length}</div>
            </div>
            <div id="ui-settings">
                <div class="setting-group">
                    <label for="max-pages">Max Pages:</label>
                    <input type="number" id="max-pages" value="${autoPagingState.maxPages}" min="1" max="50">
                </div>
                <div class="setting-group">
                    <label for="page-delay">Delay (ms):</label>
                    <input type="number" id="page-delay" value="${autoPagingState.delay}" min="500" max="10000" step="100">
                </div>
            </div>
            <div id="ui-buttons">
                <button id="capture-current" class="action-btn primary">Capture Current Page</button>
                <button id="start-auto-paging" class="action-btn ${autoPagingState.isActive ? 'danger' : 'success'}">${autoPagingState.isActive ? 'Stop Auto-Capture' : 'Start Auto-Capture'}</button>
                <button id="download-data" class="action-btn secondary">Download CSV</button>
                <button id="clear-cache" class="action-btn secondary">Clear Data/Cache</button>
            </div>
        </div>
    `;

    // --- Styles ---
    const style = document.createElement('style');
    style.textContent = `
        #chainflip-floating-ui { position: fixed; top: 20px; right: 20px; width: 320px; background: #fff; border: 2px solid #6366f1; border-radius: 8px; box-shadow: 0 4px 20px rgba(0,0,0,0.3); font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-size: 14px; color: #333; z-index: 10000; user-select: none; }
        #ui-header { background: #6366f1; color: white; padding: 10px 15px; display: flex; justify-content: space-between; align-items: center; cursor: move; border-radius: 6px 6px 0 0; }
        #ui-title { font-weight: bold; font-size: 16px; }
        #ui-controls button { background: none; border: none; color: white; font-size: 18px; cursor: pointer; padding: 0 5px; margin-left: 5px; }
        #ui-controls button:hover { background: rgba(255,255,255,0.2); border-radius: 3px; }
        #ui-content { padding: 15px; background: #fff; }
        #ui-status { margin-bottom: 15px; padding: 10px; background: #f5f5f5; border-radius: 4px; border-left: 4px solid #6366f1; }
        #status-text { font-weight: bold; color: #333; margin-bottom: 5px; }
        #progress-info { font-size: 12px; color: #666; }
        #ui-settings { margin-bottom: 15px; }
        .setting-group { display: flex; align-items: center; margin-bottom: 10px; }
        .setting-group label { flex: 1; color: #333; font-weight: 500; }
        .setting-group input { flex: 1; padding: 5px 8px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px; color: #333; background: #fff; }
        .setting-group input:focus { outline: none; border-color: #6366f1; box-shadow: 0 0 0 2px rgba(99,102,241,0.2); }
        #ui-buttons { display: flex; flex-direction: column; gap: 8px; }
        .action-btn { padding: 10px 15px; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; font-weight: 500; transition: all 0.2s; }
        .action-btn.primary { background: #6366f1; color: white; }
        .action-btn.primary:hover { background: #4f46e5; }
        .action-btn.success { background: #10b981; color: white; }
        .action-btn.success:hover { background: #059669; }
        .action-btn.danger { background: #ef4444; color: white; }
        .action-btn.danger:hover { background: #dc2626; }
        .action-btn.secondary { background: #6b7280; color: white; }
        .action-btn.secondary:hover { background: #4b5563; }
        .ui-minimized #ui-content { display: none; }
        .ui-minimized { width: 200px; }
    `;

    document.head.appendChild(style);
    document.body.appendChild(ui);
    setupFloatingUIEvents();
}

function updateFloatingUI() {
    const ui = document.getElementById('chainflip-floating-ui');
    if (!ui) return;
    const statusText = ui.querySelector('#status-text');
    const progressInfo = ui.querySelector('#progress-info');
    const startAutoPagingBtn = ui.querySelector('#start-auto-paging');
    if (autoPagingState.isActive) {
        statusText.textContent = `Auto-capturing page ${autoPagingState.currentPage}/${autoPagingState.maxPages}`;
        progressInfo.textContent = `Page: ${autoPagingState.currentPage} | Captured: ${autoPagingState.capturedTransactions.length}`;
        startAutoPagingBtn.textContent = 'Stop Auto-Capture';
        startAutoPagingBtn.classList.remove('success');
        startAutoPagingBtn.classList.add('danger');
    } else {
        statusText.textContent = `Ready - ${autoPagingState.capturedTransactions.length} transactions captured`;
        progressInfo.textContent = autoPagingState.capturedTransactions.length > 0 ? `Last capture: ${new Date().toLocaleTimeString()}` : '';
        startAutoPagingBtn.textContent = 'Start Auto-Capture';
        startAutoPagingBtn.classList.remove('danger');
        startAutoPagingBtn.classList.add('success');
    }
}

function setupFloatingUIEvents() {
    const ui = document.getElementById('chainflip-floating-ui');
    if (!ui) return;
    
    // Draggable
    let isDragging = false;
    let dragOffset = { x: 0, y: 0 };
    const header = ui.querySelector('#ui-header');
    header.addEventListener('mousedown', (e) => {
        isDragging = true;
        dragOffset = { x: e.clientX - ui.offsetLeft, y: e.clientY - ui.offsetTop };
    });
    document.addEventListener('mousemove', (e) => {
        if (isDragging) {
            ui.style.left = (e.clientX - dragOffset.x) + 'px';
            ui.style.top = (e.clientY - dragOffset.y) + 'px';
            ui.style.right = 'auto';
        }
    });
    document.addEventListener('mouseup', () => { isDragging = false; });
    
    // Settings
    ui.querySelector('#max-pages').addEventListener('change', (e) => {
        autoPagingState.maxPages = parseInt(e.target.value);
        saveAutoPagingState();
    });
    ui.querySelector('#page-delay').addEventListener('change', (e) => {
        autoPagingState.delay = parseInt(e.target.value);
        saveAutoPagingState();
    });
    
    // Buttons
    ui.querySelector('#capture-current').addEventListener('click', async () => {
        autoPagingState.capturedTransactions = [];
        autoPagingState.currentPage = getCurrentPageFromUrl();
        saveAutoPagingState();
        const data = await captureCurrentPageData();
        if (data.length > 0) {
            autoPagingState.capturedTransactions.push(...data);
            saveAutoPagingState();
            updateFloatingUI();
            alert(`Captured ${data.length} transactions from current page!`);
        } else {
            alert('No transactions found on current page');
        }
    });
    
    ui.querySelector('#start-auto-paging').addEventListener('click', () => {
        if (autoPagingState.isActive) {
            stopAutoPaging();
        } else {
            // Reset state for new capture
            autoPagingState.capturedTransactions = [];
            autoPagingState.currentPage = getCurrentPageFromUrl();
            autoPagingState.maxPages = parseInt(ui.querySelector('#max-pages').value);
            autoPagingState.delay = parseInt(ui.querySelector('#page-delay').value);
            saveAutoPagingState();
            startAutoPaging();
        }
    });
    
    ui.querySelector('#download-data').addEventListener('click', () => {
        downloadCapturedData();
    });
    
    ui.querySelector('#clear-cache').addEventListener('click', () => {
        chrome.storage.local.remove(['autoPagingState'], () => {
            autoPagingState.isActive = false;
            autoPagingState.stopRequested = false;
            autoPagingState.capturedTransactions = [];
            autoPagingState.currentPage = getCurrentPageFromUrl();
            updateFloatingUI();
            alert('Data/cache cleared!');
        });
    });
    
    ui.querySelector('#ui-minimize').addEventListener('click', () => {
        ui.classList.toggle('ui-minimized');
    });
    
    ui.querySelector('#ui-close').addEventListener('click', () => {
        ui.remove();
    });
}

// --- Data Extraction ---
async function captureCurrentPageData() {
    // Find the transaction table and extract rows
    const table = document.querySelector('table');
    if (!table) return [];
    
    const rows = table.querySelectorAll('tbody tr');
    const data = [];
    
    for (const row of rows) {
        const cells = row.querySelectorAll('td');
        if (cells.length < 5) continue;

        // Extract transaction data based on Chainflip's table structure
        let transactionId = null;
        let swapDetails = null;
        let addresses = null;
        let status = null;
        let commission = null;
        let age = null;
        let rawRowText = row.innerText;

        // Extract transaction ID from the first column or row attributes
        if (cells[0]) {
            const idMatch = cells[0].innerText.match(/#(\d+)/);
            if (idMatch) transactionId = idMatch[1];
        }

        // Extract swap details (from the first column)
        if (cells[0]) {
            swapDetails = cells[0].innerText.trim();
        }

        // Extract addresses (from the second column)
        if (cells[1]) {
            addresses = cells[1].innerText.trim();
        }

        // Extract status (from the third column)
        if (cells[2]) {
            status = cells[2].innerText.trim();
        }

        // Extract commission (from the fourth column)
        if (cells[3]) {
            commission = cells[3].innerText.trim();
        }

        // Extract age (from the fifth column)
        if (cells[4]) {
            age = cells[4].innerText.trim();
        }

        // Parse swap details to extract amounts and assets
        let fromAmount = null, fromAsset = null, toAmount = null, toAsset = null;
        if (swapDetails) {
            // Look for patterns like "0.00123562 BTC" -> "147.36 USDC" -> "147.20 USDT"
            const swapPattern = swapDetails.match(/(\d+\.?\d*)\s+([A-Z]+)\s*→\s*(\d+\.?\d*)\s+([A-Z]+)(?:\s*→\s*(\d+\.?\d*)\s+([A-Z]+))?/);
            if (swapPattern) {
                fromAmount = swapPattern[1];
                fromAsset = swapPattern[2];
                toAmount = swapPattern[3];
                toAsset = swapPattern[4];
                // Check if there's a third asset (like in the examples)
                if (swapPattern[5] && swapPattern[6]) {
                    // This is a multi-hop swap, use the final destination
                    toAmount = swapPattern[5];
                    toAsset = swapPattern[6];
                }
            }
        }

        // Extract addresses more precisely
        let fromAddress = null, toAddress = null;
        if (addresses) {
            const addressMatches = addresses.match(/([0-9a-fA-F]{4,}|[13][a-km-zA-HJ-NP-Z1-9]{25,34}|bc1[a-z0-9]{39,59})/g);
            if (addressMatches && addressMatches.length >= 2) {
                fromAddress = addressMatches[0];
                toAddress = addressMatches[1];
            }
        }

        data.push({
            transaction_id: transactionId,
            swap_details: swapDetails,
            from_amount: fromAmount,
            from_asset: fromAsset,
            to_amount: toAmount,
            to_asset: toAsset,
            from_address: fromAddress,
            to_address: toAddress,
            status: status,
            commission: commission,
            age: age,
            raw_row_text: rawRowText
        });
    }
    
    return data;
}

function saveAutoPagingState() {
    if (typeof chrome !== 'undefined' && chrome.storage) {
        chrome.storage.local.set({ autoPagingState });
    }
}

function loadAutoPagingState() {
    if (typeof chrome !== 'undefined' && chrome.storage) {
        chrome.storage.local.get(['autoPagingState'], function(result) {
            if (result.autoPagingState) {
                Object.assign(autoPagingState, result.autoPagingState);
                // If not actively capturing, reset isActive
                if (!autoPagingState.isActive || autoPagingState.stopRequested) {
                    autoPagingState.isActive = false;
                    autoPagingState.stopRequested = false;
                }
                updateFloatingUI();
                // If auto-paging was active and not stopped, resume
                if (autoPagingState.isActive && !autoPagingState.stopRequested) {
                    continueAutoPaging();
                }
            }
        });
    }
}

function stopAutoPaging() {
    autoPagingState.isActive = false;
    autoPagingState.stopRequested = true;
    saveAutoPagingState();
    updateFloatingUI();
}

async function startAutoPaging() {
    autoPagingState.isActive = true;
    autoPagingState.stopRequested = false;
    autoPagingState.currentPage = getCurrentPageFromUrl();
    saveAutoPagingState();
    await continueAutoPaging();
}

async function continueAutoPaging() {
    while (autoPagingState.isActive && !autoPagingState.stopRequested && autoPagingState.currentPage <= autoPagingState.maxPages) {
        await new Promise(resolve => setTimeout(resolve, 2000));
        const pageData = await captureCurrentPageData();
        
        // Prevent double-storing: only add if not already present (by transaction_id)
        const existingIds = new Set(autoPagingState.capturedTransactions.map(tx => tx.transaction_id));
        const newData = pageData.filter(tx => !existingIds.has(tx.transaction_id));
        
        if (newData.length > 0) {
            autoPagingState.capturedTransactions.push(...newData);
        }
        
        saveAutoPagingState();
        updateFloatingUI();
        
        await new Promise(resolve => setTimeout(resolve, Math.max(autoPagingState.delay, 3000)));
        
        if (autoPagingState.currentPage >= autoPagingState.maxPages) break;
        
        autoPagingState.currentPage++;
        saveAutoPagingState();
        
        const success = await navigateToNextPage();
        if (!success) break;
        
        return;
    }
    
    autoPagingState.isActive = false;
    saveAutoPagingState();
    updateFloatingUI();
    
    if (autoPagingState.capturedTransactions.length > 0) {
        alert(`Auto-capture completed! Captured ${autoPagingState.capturedTransactions.length} transactions. Click "Download CSV" to save.`);
    }
}

function getCurrentPageFromUrl() {
    const urlMatch = window.location.href.match(/[?&]page=(\d+)/);
    return urlMatch ? parseInt(urlMatch[1]) : 1;
}

async function navigateToNextPage() {
    // Try to click next button or manipulate URL
    const currentUrl = window.location.href;
    let nextPageUrl;
    const currentPage = getCurrentPageFromUrl();
    
    nextPageUrl = currentUrl.replace(/[?&]page=\d+/, `&page=${currentPage + 1}`);
    if (!currentUrl.includes('page=')) {
        const sep = currentUrl.includes('?') ? '&' : '?';
        nextPageUrl = `${currentUrl}${sep}page=${currentPage + 1}`;
    }
    
    window.location.href = nextPageUrl;
    return true;
}

function downloadCapturedData() {
    const data = autoPagingState.capturedTransactions;
    if (!data || data.length === 0) {
        alert('No data to download.');
        return;
    }
    
    // Get all unique keys from all objects
    const allKeys = Array.from(
        data.reduce((keys, obj) => {
            Object.keys(obj).forEach(k => keys.add(k));
            return keys;
        }, new Set())
    );
    
    // CSV header
    const csvRows = [allKeys.join(",")];
    
    // CSV rows
    for (const row of data) {
        const values = allKeys.map(key => {
            let val = row[key] !== undefined && row[key] !== null ? String(row[key]) : '';
            // Escape quotes and commas
            if (val.includes('"') || val.includes(',') || val.includes('\n')) {
                val = '"' + val.replace(/"/g, '""') + '"';
            }
            return val;
        });
        csvRows.push(values.join(","));
    }
    
    const csvString = csvRows.join("\n");
    const blob = new Blob([csvString], {type: 'text/csv'});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `chainflip_transactions_${new Date().toISOString().replace(/[:.]/g, '-')}.csv`;
    document.body.appendChild(a);
    a.click();
    setTimeout(() => { document.body.removeChild(a); URL.revokeObjectURL(url); }, 100);
}

function isChainflipBrokerPage() {
    const url = window.location.href;
    return url.includes('scan.chainflip.io/brokers/');
}

// --- MutationObserver for Table Changes ---
let tableObserver = null;
function observeTableChanges() {
    const table = document.querySelector('table');
    if (!table) return;
    
    if (tableObserver) tableObserver.disconnect();
    
    tableObserver = new MutationObserver(() => {
        // If auto-paging is active, resume
        if (autoPagingState.isActive && !autoPagingState.stopRequested) {
            continueAutoPaging();
        }
    });
    
    tableObserver.observe(table, { childList: true, subtree: true });
}

// --- Message Listener ---
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'openFloatingUI') {
        if (isChainflipBrokerPage()) {
            createFloatingUI();
            updateFloatingUI();
            sendResponse({success: true});
        } else {
            sendResponse({success: false, error: 'Not on Chainflip broker page'});
        }
    }
});

// --- Init ---
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        if (isChainflipBrokerPage()) {
            setTimeout(() => { 
                createFloatingUI(); 
                updateFloatingUI(); 
                observeTableChanges(); 
            }, 1000);
            loadAutoPagingState();
        }
    });
} else {
    if (isChainflipBrokerPage()) {
        setTimeout(() => { 
            createFloatingUI(); 
            updateFloatingUI(); 
            observeTableChanges(); 
        }, 1000);
        loadAutoPagingState();
    }
}
