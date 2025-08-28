# Chainflip Transaction Scraper Chrome Extension

Capture Chainflip broker transaction data from scan.chainflip.io with a floating, draggable UI.

## Features

* Floating, draggable UI on the Chainflip broker page
* Capture current page or auto-capture all pages (with configurable delay)
* Download captured data as CSV
* UI persists across navigation
* Modern, readable styling with Chainflip theme colors
* Robust error handling and user feedback

## Installation

1. Download or clone this repository.
2. Open Chrome and go to `chrome://extensions/`.
3. Enable "Developer mode" (top right).
4. Click "Load unpacked" and select this `chainflip-extension` folder.
5. The extension should now appear in your Chrome toolbar.

## Usage

1. Navigate to a Chainflip broker page: `https://scan.chainflip.io/brokers/[broker-address]`
2. Click the extension icon and then "Open Floating Interface".
3. The floating UI will appear on the page.
4. Set your desired max pages and delay.
5. Click "Capture Current Page" or "Start Auto-Capture".
6. When done, click "Download CSV" to save as CSV file.

## Data Structure

The extension captures the following transaction data:
* Transaction ID
* Swap details (from/to amounts and assets)
* Source and destination addresses
* Transaction status
* Commission fees
* Transaction age
* Raw row text for additional processing

## CSV Output

Data is exported as CSV with the following columns:
- transaction_id
- swap_details
- from_amount
- from_asset
- to_amount
- to_asset
- from_address
- to_address
- status
- commission
- age
- raw_row_text

## Troubleshooting

* If the UI does not appear, make sure you are on a Chainflip broker page.
* If auto-capture stops early, try increasing the delay.
* If you reload the page, reopen the floating UI from the extension popup.
* For any issues, try reloading the extension from `chrome://extensions/`.

## Example Broker Page

You can test the extension on this example broker page:
`https://scan.chainflip.io/brokers/cFMeDPtPHccVYdBSJKTtCYuy7rewFNpro3xZBKaCGbSS2xhRi`

## Directory Structure

```
chainflip-extension/
├── manifest.json      # Extension configuration
├── content.js         # Main scraping logic and UI
├── popup.html         # Extension popup interface
├── popup.js           # Popup functionality
├── background.js      # Background service worker
└── README.md          # This file
```

---

MIT License
