# ViewBlock THORChain Scraper Chrome Extension

Capture THORChain affiliate transaction data from ViewBlock.io with a floating, draggable UI.

## Features
- Floating, draggable UI on the ViewBlock page
- Capture current page or auto-capture all pages (with configurable delay)
- Download captured data as JSON
- UI persists across navigation
- Modern, readable styling
- Robust error handling and user feedback

## Installation
1. Download or clone this repository.
2. Open Chrome and go to `chrome://extensions/`.
3. Enable "Developer mode" (top right).
4. Click "Load unpacked" and select the `viewblock_extension` folder.
5. The extension should now appear in your Chrome toolbar.

## Usage
1. Navigate to: `https://viewblock.io/thorchain/txs?affiliate=ss`
2. Click the extension icon and then "Open Floating Interface".
3. The floating UI will appear on the page.
4. Set your desired max pages and delay.
5. Click "Capture Current Page" or "Start Auto-Capture".
6. When done, click "Download Data" to save as JSON.

## Troubleshooting
- If the UI does not appear, make sure you are on the correct ViewBlock page.
- If auto-capture stops early, try increasing the delay.
- If you reload the page, reopen the floating UI from the extension popup.
- For any issues, try reloading the extension from `chrome://extensions/`.

## Data Format
- Data is saved as JSON, with one object per transaction row (raw text).
- You can further process or parse the data as needed for your analysis.

---
MIT License 