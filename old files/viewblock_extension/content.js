// ==ViewBlock THORChain Scraper Content Script==

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
    const existing = document.getElementById('viewblock-floating-ui');
    if (existing) existing.remove();

    const ui = document.createElement('div');
    ui.id = 'viewblock-floating-ui';
    ui.innerHTML = `
        <div id="ui-header">
            <span id="ui-title">ViewBlock Scraper</span>
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
        #viewblock-floating-ui { position: fixed; top: 20px; right: 20px; width: 320px; background: #fff; border: 2px solid #2196F3; border-radius: 8px; box-shadow: 0 4px 20px rgba(0,0,0,0.3); font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-size: 14px; color: #333; z-index: 10000; user-select: none; }
        #ui-header { background: #2196F3; color: white; padding: 10px 15px; display: flex; justify-content: space-between; align-items: center; cursor: move; border-radius: 6px 6px 0 0; }
        #ui-title { font-weight: bold; font-size: 16px; }
        #ui-controls button { background: none; border: none; color: white; font-size: 18px; cursor: pointer; padding: 0 5px; margin-left: 5px; }
        #ui-controls button:hover { background: rgba(255,255,255,0.2); border-radius: 3px; }
        #ui-content { padding: 15px; background: #fff; }
        #ui-status { margin-bottom: 15px; padding: 10px; background: #f5f5f5; border-radius: 4px; border-left: 4px solid #2196F3; }
        #status-text { font-weight: bold; color: #333; margin-bottom: 5px; }
        #progress-info { font-size: 12px; color: #666; }
        #ui-settings { margin-bottom: 15px; }
        .setting-group { display: flex; align-items: center; margin-bottom: 10px; }
        .setting-group label { flex: 1; color: #333; font-weight: 500; }
        .setting-group input { flex: 1; padding: 5px 8px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px; color: #333; background: #fff; }
        .setting-group input:focus { outline: none; border-color: #2196F3; box-shadow: 0 0 0 2px rgba(33,150,243,0.2); }
        #ui-buttons { display: flex; flex-direction: column; gap: 8px; }
        .action-btn { padding: 10px 15px; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; font-weight: 500; transition: all 0.2s; }
        .action-btn.primary { background: #2196F3; color: white; }
        .action-btn.primary:hover { background: #1976D2; }
        .action-btn.success { background: #4CAF50; color: white; }
        .action-btn.success:hover { background: #45a049; }
        .action-btn.danger { background: #f44336; color: white; }
        .action-btn.danger:hover { background: #da190b; }
        .action-btn.secondary { background: #757575; color: white; }
        .action-btn.secondary:hover { background: #616161; }
        .ui-minimized #ui-content { display: none; }
        .ui-minimized { width: 200px; }
    `;
    document.head.appendChild(style);
    document.body.appendChild(ui);
    setupFloatingUIEvents();
    return ui;
}

function updateFloatingUI() {
    const ui = document.getElementById('viewblock-floating-ui');
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
    const ui = document.getElementById('viewblock-floating-ui');
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
function extractCopyableValues(row) {
    // Collect all possible values: copy button, tooltip, long text
    const values = [];
    // 1. Copy buttons
    row.querySelectorAll('button[data-clipboard-text]').forEach(btn => {
        const val = btn.getAttribute('data-clipboard-text');
        if (val && val.length > 8) values.push(val);
    });
    // 2. Elements with title (tooltip)
    row.querySelectorAll('[title]').forEach(el => {
        const val = el.getAttribute('title');
        if (val && val.length > 8 && !values.includes(val)) values.push(val);
    });
    // 3. Long text spans/divs (addresses/hashes)
    row.querySelectorAll('span,div').forEach(el => {
        const val = el.innerText.trim();
        if (val.length > 20 && !values.includes(val)) values.push(val);
    });
    return values;
}

async function captureCurrentPageData() {
    // Find the table and extract rows
    const table = document.querySelector('table');
    if (!table) return [];
    const rows = table.querySelectorAll('tbody tr');
    const data = [];
    for (const row of rows) {
        const cells = row.querySelectorAll('td');
        if (cells.length < 5) continue;

        // Extract all possible copyable values (tx_hash, from_address, to_address)
        const copyValues = extractCopyableValues(row);
        let tx_hash = copyValues[0] || null;
        let from_address = copyValues[1] || null;
        let to_address = copyValues[2] || null;
        let affiliate_address = copyValues[3] || null;

        // Extract visible fields by searching for likely patterns
        let block_height = null, type = null, from_amount = null, from_asset = null, to_amount = null, to_asset = null, status = null, timestamp = null;

        // Block height: look for a number with 6+ digits
        for (let i = 0; i < cells.length; ++i) {
            if (!block_height && /\d{6,}/.test(cells[i].innerText.replace(/,/g, ''))) {
                block_height = cells[i].innerText.replace(/[^\d]/g, '');
            }
        }
        // Type (Swap/Add/Withdraw)
        for (let i = 0; i < cells.length; ++i) {
            if (!type && /(Swap|Add|Withdraw)/i.test(cells[i].innerText)) {
                type = cells[i].innerText.trim();
            }
        }
        // Status (Success/Pending/Failed)
        for (let i = 0; i < cells.length; ++i) {
            if (!status && /(Success|Pending|Failed)/i.test(cells[i].innerText)) {
                status = cells[i].innerText.trim();
            }
        }
        // Timestamp (look for date/time string)
        for (let i = 0; i < cells.length; ++i) {
            if (!timestamp && /\d{4}.*(AM|PM)/.test(cells[i].innerText)) {
                timestamp = cells[i].innerText.trim();
            }
        }
        // From/To amounts and assets (look for numeric+asset pairs)
        let amountAssetPairs = [];
        for (let i = 0; i < cells.length; ++i) {
            let txt = cells[i].innerText.replace(/,/g, '').trim();
            let num = txt.match(/^([\d\.]+)$/);
            if (num && i + 1 < cells.length) {
                let asset = cells[i + 1].innerText.trim();
                if (/^[A-Z0-9\.\-]+$/.test(asset) && asset.length <= 10) {
                    amountAssetPairs.push({ amount: num[1], asset });
                }
            }
        }
        if (amountAssetPairs.length >= 1) {
            from_amount = amountAssetPairs[0].amount;
            from_asset = amountAssetPairs[0].asset;
        }
        if (amountAssetPairs.length >= 2) {
            to_amount = amountAssetPairs[1].amount;
            to_asset = amountAssetPairs[1].asset;
        }
        // Fallback: try to parse from the whole row text if above fails
        if (!from_amount || !from_asset || !to_amount || !to_asset) {
            const rowText = row.innerText;
            const swapMatch = rowText.match(/(\d[\d,\.]+)\s*([A-Z\.\-]+)\s+(\d[\d,\.]+)\s*([A-Z\.\-]+)/);
            if (swapMatch) {
                from_amount = from_amount || swapMatch[1];
                from_asset = from_asset || swapMatch[2];
                to_amount = to_amount || swapMatch[3];
                to_asset = to_asset || swapMatch[4];
            }
        }
        data.push({
            block_height,
            type,
            from_amount,
            from_asset,
            to_amount,
            to_asset,
            status,
            timestamp,
            tx_hash,
            from_address,
            to_address,
            affiliate_address,
            raw_row_text: row.innerText
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
        // Prevent double-storing: only add if not already present (by tx_hash)
        const existingHashes = new Set(autoPagingState.capturedTransactions.map(tx => tx.tx_hash));
        const newData = pageData.filter(tx => !existingHashes.has(tx.tx_hash));
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
        alert(`Auto-capture completed! Captured ${autoPagingState.capturedTransactions.length} transactions. Click "Download Data" to save.`);
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
    a.download = `viewblock_thorchain_data_${new Date().toISOString().replace(/[:.]/g, '-')}.csv`;
    document.body.appendChild(a);
    a.click();
    setTimeout(() => { document.body.removeChild(a); URL.revokeObjectURL(url); }, 100);
}
function isViewBlockThorchainPage() {
    const url = window.location.href;
    return url.includes('viewblock.io/thorchain') && (url.includes('affiliate=ss') || url.includes('txs'));
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
        if (isViewBlockThorchainPage()) {
            createFloatingUI();
            updateFloatingUI();
            sendResponse({success: true});
        } else {
            sendResponse({success: false, error: 'Not on ViewBlock THORChain page'});
        }
    }
});
// --- Init ---
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        if (isViewBlockThorchainPage()) {
            setTimeout(() => { createFloatingUI(); updateFloatingUI(); observeTableChanges(); }, 1000);
            loadAutoPagingState();
        }
    });
} else {
    if (isViewBlockThorchainPage()) {
        setTimeout(() => { createFloatingUI(); updateFloatingUI(); observeTableChanges(); }, 1000);
        loadAutoPagingState();
    }
} 