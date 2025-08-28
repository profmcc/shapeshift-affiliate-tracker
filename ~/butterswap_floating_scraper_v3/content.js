/**
 * ButterSwap Floating Scraper v3.0
 * Advanced transaction scraper with auto-pagination, floating UI, and comprehensive debugging
 * 
 * Features:
 * - Auto-pagination through all transaction pages
 * - Configurable delays and page limits
 * - Real-time progress tracking
 * - ShapeShift affiliate detection
 * - Draggable floating interface
 * - Comprehensive error handling
 * - CSV export functionality
 * - Enhanced debugging tools
 * - Framework detection
 * - Test scraping functionality
 */

class ButterSwapFloatingScraperV3 {
  constructor() {
    this.version = '3.0.0';
    this.isScraping = false;
    this.stopRequested = false;
    this.allTransactions = [];
    this.currentPage = 1;
    this.totalPages = 0;
    this.pageDelay = 2000;
    this.maxPages = 1000;
    this.scrapingStartTime = null;
    this.successfulPages = 0;
    this.failedPages = 0;
