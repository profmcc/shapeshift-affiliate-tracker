document.addEventListener('DOMContentLoaded', function() {
    const openUIButton = document.getElementById('open-ui');
    openUIButton.addEventListener('click', function() {
        chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
            const activeTab = tabs[0];
            if (!activeTab.url.includes('viewblock.io/thorchain')) {
                document.body.innerHTML = `
                    <div style="padding: 20px; text-align: center;">
                        <h3 style="color: #e74c3c; margin-bottom: 15px;">⚠️ Wrong Page</h3>
                        <p style="margin-bottom: 15px;">Please navigate to:</p>
                        <p style="background: #f8f9fa; padding: 10px; border-radius: 4px; font-family: monospace; font-size: 12px; word-break: break-all;">
                            https://viewblock.io/thorchain/txs?affiliate=ss
                        </p>
                        <button id="go-to-page" style="background: #3498db; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; margin-top: 15px;">
                            Go to Page
                        </button>
                    </div>
                `;
                document.getElementById('go-to-page').addEventListener('click', function() {
                    chrome.tabs.update(activeTab.id, {
                        url: 'https://viewblock.io/thorchain/txs?affiliate=ss'
                    });
                    window.close();
                });
                return;
            }
            chrome.tabs.sendMessage(activeTab.id, {action: 'openFloatingUI'}, function(response) {
                if (chrome.runtime.lastError) {
                    document.body.innerHTML = `
                        <div style="padding: 20px; text-align: center;">
                            <h3 style="color: #e74c3c; margin-bottom: 15px;">⚠️ Extension Error</h3>
                            <p style="margin-bottom: 15px;">Please refresh the page and try again.</p>
                            <button id="refresh-page" style="background: #3498db; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer;">
                                Refresh Page
                            </button>
                        </div>
                    `;
                    document.getElementById('refresh-page').addEventListener('click', function() {
                        chrome.tabs.reload(activeTab.id);
                        window.close();
                    });
                } else if (response && response.success) {
                    document.body.innerHTML = `
                        <div style="padding: 20px; text-align: center;">
                            <h3 style="color: #27ae60; margin-bottom: 15px;">✅ Success!</h3>
                            <p>Floating UI opened on the page.</p>
                            <p style="font-size: 12px; color: #7f8c8d; margin-top: 10px;">
                                You can now close this popup and use the floating interface.
                            </p>
                        </div>
                    `;
                    setTimeout(() => { window.close(); }, 2000);
                } else {
                    document.body.innerHTML = `
                        <div style="padding: 20px; text-align: center;">
                            <h3 style="color: #e74c3c; margin-bottom: 15px;">⚠️ Error</h3>
                            <p>${response ? response.error : 'Unknown error occurred'}</p>
                        </div>
                    `;
                }
            });
        });
    });
}); 