# Chrome Extension Setup Guide

This guide walks you through downloading, installing, and using the Chrome extensions for capturing DeFi transaction data. All extensions save their data to your **Downloads** folder, which is then processed by the analysis notebooks to create the master CSV files.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Downloading the Extensions](#downloading-the-extensions)
3. [Installing Extensions in Chrome](#installing-extensions-in-chrome)
4. [Using the Extensions](#using-the-extensions)
5. [Running the Analysis Notebooks](#running-the-analysis-notebooks)
6. [Understanding the Output Files](#understanding-the-output-files)

---

## Prerequisites

- **Google Chrome** browser (latest version recommended)
- **Python 3.8+** with Jupyter Notebook installed
- **Git** (if downloading from repository)
- Access to the following websites:
  - ViewBlock.io (for THORChain data)
  - Chainflip.io (for Chainflip data)
  - ButterSwap (for ButterSwap data)

---

## Downloading the Extensions

### Option 1: Download Individual Extensions

Each extension is located in its own folder in this repository:

1. **ViewBlock THORChain Data Capture** (`viewblock-thorchain-extension/`)
   - Captures THORChain affiliate transaction data from ViewBlock.io
   - Version: 1.0.0
   - Extension ID: `cnncfbdlngfpjilejkmfhmifjkioalja`

2. **DeFi Data Snatcher v15** (`defi-data-snatcher-v15/`)
   - Captures Chainflip and ButterSwap transaction data
   - Version: 15.0.0
   - Simple text-based export version

### Option 2: Download the Entire Repository

If you want all extensions and analysis tools:

```bash
git clone https://github.com/profmcc/shapeshift-affiliate-tracker.git
cd shapeshift-affiliate-tracker
```

The extensions are located in:
- `viewblock-thorchain-extension/`
- `defi-data-snatcher-v15/`

---

## Installing Extensions in Chrome

### Step 1: Enable Developer Mode

1. Open Chrome and navigate to `chrome://extensions/`
2. Toggle **"Developer mode"** ON (top right corner)

### Step 2: Load the Extension

For each extension folder:

1. Click **"Load unpacked"** button
2. Navigate to the extension folder (e.g., `viewblock-thorchain-extension/` or `defi-data-snatcher-v15/`)
3. Select the folder and click **"Select Folder"**
4. The extension should now appear in your extensions list

### Step 3: Pin Extensions (Optional but Recommended)

1. Click the **puzzle piece icon** (🧩) in Chrome's toolbar
2. Find your extension in the list
3. Click the **pin icon** (📌) to keep it visible in your toolbar

### Repeat for All Extensions

Install both extensions:
- ✅ ViewBlock THORChain Data Capture
- ✅ DeFi Data Snatcher v15

---

## Using the Extensions

### ViewBlock THORChain Data Capture

1. **Navigate to ViewBlock.io**
   - Go to: `https://viewblock.io/thorchain/txs`
   - The extension automatically activates on this page

2. **Use the Extension**
   - Click the extension icon in your Chrome toolbar
   - A popup will appear with options to capture data
   - Follow the on-screen instructions to export transaction data

3. **Save Location**
   - All exported files are automatically saved to your **Downloads** folder
   - Files are named: `viewblock_thorchain_data_*.csv` or `viewblock_thorchain_data_*.json`

### DeFi Data Snatcher v15

1. **Navigate to the Target Website**
   - For Chainflip: Go to the Chainflip transaction page
   - For ButterSwap: Go to the ButterSwap transaction page

2. **Activate the Extension**
   - Click the extension icon in your Chrome toolbar
   - The extension will inject a simple text export UI
   - Follow the prompts to export data

3. **Save Location**
   - All exported files are automatically saved to your **Downloads** folder
   - Files are named: `chainflip_combined_*.csv` or similar

---

## Running the Analysis Notebooks

### Important: File Organization

**All extension output files MUST be saved to your Downloads folder** for the notebooks to find them automatically.

The notebooks look for files in: `~/Downloads/` (or `C:\Users\YourName\Downloads\` on Windows)

### Step 1: Navigate to the Analysis Repository

```bash
cd defi-analysis-repo
# or if you cloned it separately:
cd /path/to/defi-analysis-repo
```

### Step 2: Run the Individual Platform Notebooks

These notebooks process the raw data from each extension:

1. **THORChain Data Combiner** (`notebooks/thorchain_data_combiner.ipynb`)
   - Processes: `viewblock_thorchain_data_*.csv` and `viewblock_thorchain_data_*.json`
   - Output: `thorchain_combined_*.csv`

2. **Chainflip Volume Analyzer** (`notebooks/chainflip_volume_analyzer.ipynb`)
   - Processes: Chainflip data files from Downloads
   - Output: `chainflip_combined_*.csv`

3. **ButterSwap Data Analyzer** (`notebooks/butterswap_data_analyzer.ipynb`)
   - Processes: ButterSwap data files from Downloads
   - Output: `butterswap_combined_*.csv`

### Step 3: Run the Combined Analyzer

**This is the main notebook that creates the master CSV:**

```bash
jupyter notebook notebooks/combined_swappers_analyzer.ipynb
```

Or run it programmatically:

```bash
jupyter nbconvert --to notebook --execute notebooks/combined_swappers_analyzer.ipynb
```

This notebook:
- Loads all platform-specific combined CSVs from Downloads
- Standardizes columns across platforms
- Removes duplicates and invalid rows
- Creates the master CSV files

---

## Understanding the Output Files

After running `combined_swappers_analyzer.ipynb`, you'll find these files in your **Downloads** folder:

### Master Files (Sorted First Alphabetically)

1. **`01_combined_swappers_master_YYYYMMDD_HHMMSS.csv`** ⭐ **MASTER FILE**
   - This is the **primary output file** you should use for analysis
   - Contains all cleaned, deduplicated transaction data from all platforms
   - Includes all standardized columns and metadata
   - **This file appears first in alphabetical order** (prefixed with `01_`)

2. **`02_combined_swappers_master_simple_YYYYMMDD_HHMMSS.csv`**
   - Simplified version with minimal columns
   - Contains a single validated `amount` column
   - Useful for quick analysis or when you only need basic transaction data

### Platform-Specific Files

- `thorchain_combined_*.csv` - THORChain transactions only
- `chainflip_combined_*.csv` - Chainflip transactions only
- `butterswap_combined_*.csv` - ButterSwap transactions only

### File Naming Convention

Files are timestamped to prevent overwriting:
- Format: `01_combined_swappers_master_20251216_153534.csv`
- Date: `YYYYMMDD` (2025-12-16)
- Time: `HHMMSS` (15:35:34)

---

## Quick Start Workflow

1. **Install Extensions** → Load both extensions in Chrome
2. **Capture Data** → Use extensions to export data from each platform
3. **Verify Downloads** → Check that files are in your Downloads folder
4. **Run Notebooks** → Execute the analysis notebooks in order:
   - `thorchain_data_combiner.ipynb`
   - `chainflip_volume_analyzer.ipynb`
   - `butterswap_data_analyzer.ipynb`
   - `combined_swappers_analyzer.ipynb` ⭐
5. **Find Master CSV** → Look for `01_combined_swappers_master_*.csv` in Downloads

---

## Troubleshooting

### Extension Not Working

- Make sure Developer Mode is enabled in `chrome://extensions/`
- Check that the extension is enabled (toggle should be ON)
- Reload the extension if needed (click the refresh icon)
- Check browser console for errors (F12 → Console tab)

### Files Not Found by Notebooks

- Verify files are in the Downloads folder (not subfolders)
- Check file naming matches expected patterns:
  - THORChain: `viewblock_thorchain_data_*.csv` or `*.json`
  - Chainflip: `chainflip_combined_*.csv`
- Ensure you've run the individual platform notebooks first

### Master CSV Not Generated

- Make sure all platform-specific combined CSVs exist in Downloads
- Check that `combined_swappers_analyzer.ipynb` completed without errors
- Verify the notebook found the input files (check the output messages)

### Master CSV Not Appearing First

- The master CSV is prefixed with `01_` to appear first alphabetically
- If you see old files without the prefix, those are from before the update
- New files will always have the `01_` prefix

---

## Support

For issues or questions:
- Check the individual extension README files
- Review notebook output messages for error details
- Ensure all prerequisites are installed correctly

---

## Summary Checklist

- [ ] Chrome Developer Mode enabled
- [ ] ViewBlock THORChain extension installed
- [ ] DeFi Data Snatcher v15 extension installed
- [ ] Extensions pinned to toolbar (optional)
- [ ] Data files saved to Downloads folder
- [ ] Individual platform notebooks run successfully
- [ ] Combined analyzer notebook run successfully
- [ ] Master CSV found: `01_combined_swappers_master_*.csv`

---

**Last Updated:** December 2024
**Repository:** https://github.com/profmcc/shapeshift-affiliate-tracker

