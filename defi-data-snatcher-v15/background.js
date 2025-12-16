// DeFi Data Snatcher v15 - Simple Text Export Version
console.log('🔗 v15 Simple Text Export Background script loaded!');

chrome.action.onClicked.addListener(async (tab) => {
  console.log('🎯 Extension clicked on tab:', tab.id);
  
  try {
    await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: showSimpleTextExportUI
    });
    console.log('✅ Simple text export script executed successfully');
  } catch (error) {
    console.error('❌ Error:', error);
  }
});

function showSimpleTextExportUI() {
  console.log('showSimpleTextExportUI function called');
  
  // Remove existing UI if present
  const existingUI = document.getElementById('defi-snatcher-v15');
  if (existingUI) {
    existingUI.remove();
  }
  
  // Create simple text export UI
  const ui = document.createElement('div');
  ui.id = 'defi-snatcher-v15';
  ui.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    width: 500px;
    background: linear-gradient(135deg, #2d1b69 0%, #11998e 100%);
    color: white;
    padding: 25px;
    border-radius: 20px;
    z-index: 10000;
    font-family: 'Segoe UI', Arial, sans-serif;
    border: 3px solid #ffd700;
    box-shadow: 0 15px 40px rgba(0,0,0,0.4);
  `;
  
  ui.innerHTML = `
    <div style="display: flex; align-items: center; margin-bottom: 25px;">
      <div style="
        width: 45px;
        height: 45px;
        background: linear-gradient(45deg, #ffd700, #ff6b6b);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-right: 18px;
        font-size: 22px;
      ">📝</div>
      <h3 style="margin: 0; font-size: 20px; color: #ffd700;">Simple Text Export v15</h3>
    </div>
    
    <button id="scanBtn" style="
      width: 100%;
      padding: 14px;
      margin: 10px 0;
      background: linear-gradient(45deg, #ffd700, #ff8c00);
      color: #2d1b69;
      border: none;
      border-radius: 10px;
      cursor: pointer;
      font-weight: bold;
      font-size: 14px;
      transition: all 0.3s ease;
    ">🔍 Scan Table & Extract Links</button>
    
    <button id="exportTextBtn" style="
      width: 100%;
      padding: 14px;
      margin: 10px 0;
      background: linear-gradient(45deg, #11998e, #38ef7d);
      color: white;
      border: none;
      border-radius: 10px;
      cursor: pointer;
      font-weight: bold;
      font-size: 14px;
      transition: all 0.3s ease;
    ">📝 Export Simple Text</button>
    
    <button id="exportRawBtn" style="
      width: 100%;
      padding: 14px;
      margin: 10px 0;
      background: linear-gradient(45deg, #a55eea, #8854d0);
      color: white;
      border: none;
      border-radius: 10px;
      cursor: pointer;
      font-weight: bold;
      font-size: 14px;
      transition: all 0.3s ease;
    ">📄 Export Raw Data</button>
    
    <button id="clearBtn" style="
      width: 100%;
      padding: 14px;
      margin: 10px 0;
      background: linear-gradient(45deg, #e17055, #d63031);
      color: white;
      border: none;
      border-radius: 10px;
      cursor: pointer;
      font-weight: bold;
      font-size: 14px;
      transition: all 0.3s ease;
    ">🗑️ Clear Data</button>
    
    <button id="closeBtn" style="
      width: 100%;
      padding: 14px;
      margin: 10px 0;
      background: linear-gradient(45deg, #e17055, #d63031);
      color: white;
      border: none;
      border-radius: 10px;
      cursor: pointer;
      font-weight: bold;
      font-size: 14px;
      transition: all 0.3s ease;
    ">❌ Close</button>
    
    <div id="status" style="
      margin-top: 25px;
      padding: 18px;
      background: rgba(255, 215, 0, 0.1);
      border-radius: 12px;
      font-size: 13px;
      text-align: center;
      border-left: 4px solid #ffd700;
    ">Ready to scan and export as simple text</div>
    
    <div id="results" style="
      margin-top: 20px;
      max-height: 300px;
      overflow-y: auto;
      display: none;
    "></div>
  `;
  
  document.body.appendChild(ui);
  console.log('Simple text export UI created and added to page');
  
  // Add event listeners
  document.getElementById('scanBtn').addEventListener('click', () => {
    console.log('Scan button clicked');
    scanTableAndExtractLinks();
  });
  
  document.getElementById('exportTextBtn').addEventListener('click', () => {
    console.log('Export text button clicked');
    exportSimpleText();
  });
  
  document.getElementById('exportRawBtn').addEventListener('click', () => {
    console.log('Export raw button clicked');
    exportRawData();
  });
  
  document.getElementById('clearBtn').addEventListener('click', () => {
    console.log('Clear button clicked');
    clearData();
  });
  
  document.getElementById('closeBtn').addEventListener('click', () => {
    console.log('Close button clicked');
    ui.remove();
  });
  
  // Global data storage
  window.defiDataV15 = {
    tableData: [],
    transactionLinks: [],
    scanTime: null
  };
  
  function scanTableAndExtractLinks() {
    console.log('Scanning table and extracting links...');
    const status = document.getElementById('status');
    const results = document.getElementById('results');
    
    status.textContent = '🔍 Scanning table and extracting links...';
    status.style.borderLeftColor = '#ff8c00';
    
    try {
      // Get current timestamp
      const now = new Date();
      const humanReadableTime = now.toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      });
      const timestamp = now.toISOString();
      
      window.defiDataV15.scanTime = {
        human: humanReadableTime,
        timestamp: timestamp
      };
      
      // Find the transaction table
      const tables = document.querySelectorAll('table');
      console.log('Found tables:', tables.length);
      
      let transactionTable = null;
      tables.forEach((table, index) => {
        const tableText = table.textContent;
        console.log(`Table ${index + 1} text:`, tableText.substring(0, 200));
        
        // Look for transaction table
        if (tableText.includes('Hash') || tableText.includes('hash') || 
            tableText.includes('From') || tableText.includes('To') || 
            tableText.includes('Status') || tableText.includes('Time') ||
            tableText.includes('0x') || tableText.includes('USDC') || 
            tableText.includes('ETH') || tableText.includes('POL')) {
          transactionTable = table;
          console.log(`Found transaction table: ${index + 1}`);
        }
      });
      
      if (!transactionTable) {
        // Use first table as fallback
        transactionTable = tables[0];
        console.log('Using first table as fallback');
      }
      
      // Parse table rows cleanly
      const rows = transactionTable.querySelectorAll('tr');
      console.log('Found rows:', rows.length);
      
      const tableData = [];
      const transactionLinks = [];
      
      rows.forEach((row, rowIndex) => {
        const cells = Array.from(row.querySelectorAll('td, th')).map(cell => {
          // Clean cell text
          let text = cell.textContent.trim();
          
          // Remove extra whitespace and normalize
          text = text.replace(/\s+/g, ' ').replace(/\n/g, ' ').trim();
          
          return text;
        });
        
        console.log(`Row ${rowIndex + 1} cells:`, cells);
        
        if (cells.length > 0) {
          const isHeader = rowIndex === 0;
          
          if (isHeader) {
            // Add link column to headers
            cells.push('Full Transaction Link');
          }
          
          // Parse data rows
          let hash = null;
          let fullLink = null;
          
          if (!isHeader && cells.length >= 1) {
            // Extract hash from first column
            hash = cells[0];
            
            // Generate full transaction link
            if (hash && hash.includes('0x')) {
              fullLink = generateTransactionLink(hash);
              
              // Store transaction link
              transactionLinks.push({
                id: transactionLinks.length + 1,
                hash: hash,
                fullLink: fullLink,
                rowIndex: rowIndex + 1
              });
            }
          }
          
          tableData.push({
            rowIndex: rowIndex + 1,
            isHeader: isHeader,
            hash: hash,
            from: isHeader ? null : cells[1] || null,
            to: isHeader ? null : cells[2] || null,
            fee: isHeader ? null : cells[3] || null,
            status: isHeader ? null : cells[4] || null,
            time: isHeader ? null : cells[5] || null,
            fullLink: fullLink,
            // Raw cells for reference
            rawCells: cells
          });
        }
      });
      
      // Store results
      window.defiDataV15.tableData = tableData;
      window.defiDataV15.transactionLinks = transactionLinks;
      
      // Update status
      status.textContent = `✅ Table scanned! Found ${tableData.length} rows, ${transactionLinks.length} transaction links`;
      status.style.borderLeftColor = '#11998e';
      
      // Show results
      showSimpleTextResults();
      
      console.log('Table scan complete:', window.defiDataV15);
      
    } catch (error) {
      console.error('Table scan error:', error);
      status.textContent = '❌ Error during table scan';
      status.style.borderLeftColor = '#e17055';
    }
  }
  
  function generateTransactionLink(hash) {
    console.log('Generating transaction link for hash:', hash);
    
    // Clean hash (remove any extra text)
    const cleanHash = hash.match(/0x[a-fA-F0-9]{6,}?\.{3}[a-fA-F0-9]{6,}|0x[a-fA-F0-9]{40}/);
    if (!cleanHash) {
      console.log('No valid hash found in:', hash);
      return null;
    }
    
    const cleanHashStr = cleanHash[0];
    console.log('Clean hash:', cleanHashStr);
    
    // Get current page URL to determine base
    const currentUrl = window.location.href;
    const urlParts = currentUrl.split('/');
    
    // Try to determine the base URL for transactions
    let baseUrl = 'https://butterswap.com';
    
    // Check if we're on a known domain
    if (currentUrl.includes('butterswap.com')) {
      baseUrl = 'https://butterswap.com';
    } else if (currentUrl.includes('butter.network')) {
      baseUrl = 'https://butter.network';
    } else if (currentUrl.includes('butter.fi')) {
      baseUrl = 'https://butter.fi';
    } else {
      // Try to construct from current URL
      const domain = urlParts[2]; // Get domain part
      const protocol = urlParts[0];
      baseUrl = `${protocol}//${domain}`;
    }
    
    // Generate multiple possible transaction URLs
    const possibleUrls = [
      `${baseUrl}/tx/${cleanHashStr}`,
      `${baseUrl}/transaction/${cleanHashStr}`,
      `${baseUrl}/hash/${cleanHashStr}`,
      `${baseUrl}/explorer/tx/${cleanHashStr}`,
      `${baseUrl}/explorer/transaction/${cleanHashStr}`,
      `${baseUrl}/explorer/hash/${cleanHashStr}`,
      `${baseUrl}/blockchain/tx/${cleanHashStr}`,
      `${baseUrl}/blockchain/transaction/${cleanHashStr}`,
      `${baseUrl}/blockchain/hash/${cleanHashStr}`
    ];
    
    console.log('Generated possible URLs:', possibleUrls);
    
    // Return the first one (most likely to work)
    return possibleUrls[0];
  }
  
  function showSimpleTextResults() {
    const results = document.getElementById('results');
    results.style.display = 'block';
    
    results.innerHTML = `
      <div style="
        background: rgba(255, 215, 0, 0.1);
        padding: 20px;
        border-radius: 12px;
        margin-top: 20px;
        border: 1px solid rgba(255, 215, 0, 0.3);
      ">
        <h4 style="margin: 0 0 20px 0; color: #ffd700; text-align: center;">📝 Simple Text Results v15</h4>
        
        <div style="margin-bottom: 15px;">
          <strong style="color: #11998e;">Table Rows:</strong> ${window.defiDataV15.tableData.length}
          <div style="font-size: 11px; opacity: 0.8; margin-left: 15px; margin-top: 5px;">
            ${window.defiDataV15.tableData.filter(r => !r.isHeader).length} data rows, ${window.defiDataV15.tableData.filter(r => r.isHeader).length} header rows
          </div>
        </div>
        
        <div style="margin-bottom: 15px;">
          <strong style="color: #11998e;">Transaction Links:</strong> ${window.defiDataV15.transactionLinks.length}
          <div style="font-size: 11px; opacity: 0.8; margin-left: 15px; margin-top: 5px;">
            ${window.defiDataV15.transactionLinks.slice(0, 3).map(l => l.hash.substring(0, 10) + '...').join(', ')}
            ${window.defiDataV15.transactionLinks.length > 3 ? '...' : ''}
          </div>
        </div>
        
        <div style="margin-bottom: 15px;">
          <strong style="color: #11998e;">Scan Time:</strong> ${window.defiDataV15.scanTime ? window.defiDataV15.scanTime.human : 'Not scanned'}
        </div>
      </div>
    `;
  }
  
  function exportSimpleText() {
    if (!window.defiDataV15 || window.defiDataV15.tableData.length === 0) {
      alert('No data to export! Please scan table first.');
      return;
    }
    
    try {
      console.log('Starting simple text export...');
      
      // Create simple text format - NO CSV, NO COMPLEX PROCESSING
      let textContent = 'DeFi Data Snatcher v15 - Simple Text Export\n';
      textContent += '=============================================\n\n';
      
      // Add scan time
      if (window.defiDataV15.scanTime) {
        textContent += `Scan Time: ${window.defiDataV15.scanTime.human}\n`;
        textContent += `Timestamp: ${window.defiDataV15.scanTime.timestamp}\n\n`;
      }
      
      // Add table data in simple text format
      textContent += 'TABLE DATA:\n';
      textContent += '===========\n\n';
      
      window.defiDataV15.tableData.forEach((row, index) => {
        if (!row.isHeader) {
          textContent += `Row ${index + 1}:\n`;
          textContent += `  Hash: ${row.hash || 'N/A'}\n`;
          textContent += `  From: ${row.from || 'N/A'}\n`;
          textContent += `  To: ${row.to || 'N/A'}\n`;
          textContent += `  Fee: ${row.fee || 'N/A'}\n`;
          textContent += `  Status: ${row.status || 'N/A'}\n`;
          textContent += `  Time: ${row.time || 'N/A'}\n`;
          textContent += `  Link: ${row.fullLink || 'N/A'}\n`;
          textContent += '\n';
        }
      });
      
      // Add transaction links section
      if (window.defiDataV15.transactionLinks.length > 0) {
        textContent += 'TRANSACTION LINKS:\n';
        textContent += '==================\n\n';
        
        window.defiDataV15.transactionLinks.forEach((link, index) => {
          textContent += `Link ${index + 1}:\n`;
          textContent += `  ID: ${link.id}\n`;
          textContent += `  Hash: ${link.hash}\n`;
          textContent += `  Row: ${link.rowIndex}\n`;
          textContent += `  URL: ${link.fullLink}\n`;
          textContent += '\n';
        });
      }
      
      console.log('Text content generated successfully');
      console.log('Text preview:', textContent.substring(0, 500) + '...');
      
      // Create and download the text file
      const blob = new Blob([textContent], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      
      const a = document.createElement('a');
      a.href = url;
      a.download = `butterswap_simple_text_v15_${new Date().toISOString().split('T')[0]}.txt`;
      
      console.log('Download link created:', a.download);
      
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      
      URL.revokeObjectURL(url);
      
      console.log('File download initiated successfully');
      
      // Update status
      const status = document.getElementById('status');
      const dataRowCount = window.defiDataV15.tableData.filter(r => !r.isHeader).length;
      const linkCount = window.defiDataV15.transactionLinks.length;
      status.textContent = `📝 Exported ${dataRowCount} rows with ${linkCount} transaction links as simple text!`;
      status.style.borderLeftColor = '#11998e';
      
      console.log('Simple text export completed successfully!');
      
    } catch (error) {
      console.error('Export error:', error);
      alert('Export failed: ' + error.message + '\n\nCheck console for details.');
      
      // Update status
      const status = document.getElementById('status');
      status.textContent = '❌ Export failed - check console for details';
      status.style.borderLeftColor = '#e17055';
    }
  }
  
  function exportRawData() {
    if (!window.defiDataV15 || window.defiDataV15.tableData.length === 0) {
      alert('No data to export! Please scan table first.');
      return;
    }
    
    try {
      console.log('Starting raw data export...');
      
      // Export raw data as JSON - NO CSV PROCESSING AT ALL
      const exportData = {
        version: 'v15',
        scanTime: window.defiDataV15.scanTime,
        tableData: window.defiDataV15.tableData,
        transactionLinks: window.defiDataV15.transactionLinks,
        exportTime: new Date().toISOString()
      };
      
      const jsonContent = JSON.stringify(exportData, null, 2);
      
      console.log('JSON content generated successfully');
      console.log('JSON preview:', jsonContent.substring(0, 500) + '...');
      
      // Create and download the JSON file
      const blob = new Blob([jsonContent], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      
      const a = document.createElement('a');
      a.href = url;
      a.download = `butterswap_raw_data_v15_${new Date().toISOString().split('T')[0]}.json`;
      
      console.log('Download link created:', a.download);
      
      function clearData() {
        window.defiDataV15 = {
          tableData: [],
          transactionLinks: [],
          scanTime: null
        };
        
        const status = document.getElementById('status');
        const results = document.getElementById('results');
        
        status.textContent = 'Data cleared. Ready to scan and export as simple text.';
        status.style.borderLeftColor = '#ffd700';
        results.style.display = 'none';
        
        console.log('Data cleared');
      }
    }
  }
}
