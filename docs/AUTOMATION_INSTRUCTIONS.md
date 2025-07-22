# ShapeShift Affiliate Fee Collection System - Automation Instructions

## Current System Overview

### What's Running
The system is currently collecting affiliate fee data from three sources:
1. **EVM Chains** (Ethereum/Polygon) - CowSwap and 0x Protocol events
2. **Chainflip** - Broker affiliate fees via web scraping
3. **THORChain** - Affiliate fees via API calls

### Current Performance Metrics

#### EVM Listener Performance
- **Total Blocks**: 576 chunks (last day of data)
- **Processing Rate**: ~0.2 seconds per block
- **Estimated Time**: 2-3 minutes for Polygon chain
- **Data Volume**: ~50-100 events per block range
- **Issues**: Ethereum failing due to Infura auth, Polygon working

#### Chainflip Scraper Performance
- **Pages to Scrape**: ~20-30 broker pages
- **Processing Rate**: ~2-3 seconds per page
- **Estimated Time**: 1-2 minutes
- **Data Volume**: ~200-500 affiliate fee records
- **Issues**: Rate limiting from web scraping

#### THORChain Listener Performance
- **API Calls**: ~50-100 batches
- **Processing Rate**: ~1-2 seconds per batch
- **Estimated Time**: 2-3 minutes
- **Data Volume**: ~100-300 affiliate fee records
- **Issues**: API rate limiting

### Total System Performance
- **Current Total Time**: 5-8 minutes for full collection
- **Data Points Collected**: ~1,000-2,000 records per run
- **Database Size**: ~50-100MB per collection
- **Background Process**: Running via `nohup` with logging

## Current Architecture

### Database Structure
```sql
-- EVM Events
evm_cowswap_events (tx_hash, block_number, event_type, event_data, timestamp, chain_id)
evm_zerox_events (tx_hash, block_number, event_type, event_data, timestamp, chain_id)
evm_affiliate_transfers (tx_hash, block_number, token_address, from_address, to_address, amount, timestamp, chain_id)

-- Chainflip Data
chainflip_affiliate_fees (broker_name, volume_usd, affiliate_fee_usd, transaction_count, date, timestamp)

-- THORChain Data
thorchain_affiliate_fees (tx_hash, block_height, affiliate_fee, asset, pool, timestamp)
```

### Current Issues
1. **Rate Limiting**: All three systems hit rate limits
2. **Authentication**: Infura key issues for Ethereum
3. **Memory Usage**: Large log processing causes hangs
4. **Error Handling**: Limited retry logic
5. **Monitoring**: No real-time status updates

## Optimization Instructions for ChatGPT

### 1. Infrastructure Optimization

**Current Setup**: Single machine running Python scripts
**Target**: Distributed, scalable, cloud-based system

**Recommendations**:
- **AWS Lambda Functions**: Convert each listener to serverless functions
- **EventBridge**: Schedule regular collection (every hour)
- **RDS PostgreSQL**: Replace SQLite with cloud database
- **S3**: Store historical data and logs
- **CloudWatch**: Monitor performance and errors

### 2. Performance Optimizations

**EVM Listener**:
- Use WebSocket connections instead of HTTP polling
- Implement block range parallelization
- Cache block timestamps to avoid repeated calls
- Use multiple RPC providers (Infura, Alchemy, QuickNode)

**Chainflip Scraper**:
- Use headless browser with proxy rotation
- Implement intelligent retry with exponential backoff
- Cache broker pages to avoid re-scraping
- Use async/await for concurrent scraping

**THORChain Listener**:
- Implement connection pooling for API calls
- Use WebSocket for real-time updates
- Cache API responses to reduce calls
- Implement batch processing for multiple pools

### 3. Database Optimization

**Current**: SQLite with manual merging
**Target**: Real-time, scalable database

**Recommendations**:
- **PostgreSQL with TimescaleDB**: For time-series data
- **Redis**: For caching and real-time updates
- **Data partitioning**: By date and chain
- **Indexing**: Optimize for common queries
- **Backup strategy**: Automated daily backups

### 4. Monitoring and Alerting

**Current**: Basic logging to files
**Target**: Comprehensive monitoring

**Recommendations**:
- **CloudWatch Dashboards**: Real-time metrics
- **SNS Alerts**: For failures and anomalies
- **Custom metrics**: Collection rates, data quality
- **Health checks**: Endpoint monitoring
- **Performance tracking**: Response times, throughput

### 5. Cost Optimization

**Current**: Single machine, manual execution
**Target**: Serverless, pay-per-use

**Estimates**:
- **Lambda**: ~$0.50/month for hourly execution
- **RDS**: ~$15/month for small instance
- **S3**: ~$0.50/month for storage
- **CloudWatch**: ~$5/month for monitoring
- **Total**: ~$21/month vs current $0 (but manual)

### 6. Automation Strategy

**Scheduled Collection**:
```yaml
# EventBridge Rule
- Every hour: Run EVM listener
- Every 6 hours: Run Chainflip scraper  
- Every 2 hours: Run THORChain listener
- Every day: Run comprehensive analysis
```

**Real-time Updates**:
- WebSocket connections for live data
- Event-driven architecture
- Immediate database updates
- Real-time dashboards

### 7. Data Pipeline Architecture

```
Data Sources → Lambda Functions → SQS → Lambda Processors → RDS → Analytics
     ↓              ↓              ↓           ↓           ↓        ↓
  EVM/Chainflip/  Collectors   Queue    Data Cleaners  Storage  Dashboards
   THORChain APIs
```

### 8. Implementation Priority

**Phase 1** (Week 1):
- Convert to AWS Lambda functions
- Set up RDS PostgreSQL database
- Implement basic monitoring

**Phase 2** (Week 2):
- Add EventBridge scheduling
- Implement retry logic and error handling
- Set up CloudWatch dashboards

**Phase 3** (Week 3):
- Optimize performance with caching
- Add real-time WebSocket connections
- Implement advanced analytics

**Phase 4** (Week 4):
- Add machine learning for anomaly detection
- Implement predictive analytics
- Create automated reporting

### 9. Expected Performance Improvements

**Current**: 5-8 minutes per collection
**Target**: 30-60 seconds per collection

**Optimizations**:
- Parallel processing: 3x faster
- Caching: 2x faster
- Optimized queries: 1.5x faster
- **Total improvement**: 6-9x faster

### 10. Cost-Benefit Analysis

**Current Costs**: $0 (manual)
**Target Costs**: ~$21/month
**Benefits**:
- Automated collection every hour
- Real-time monitoring and alerts
- Scalable infrastructure
- Historical data retention
- Professional dashboards
- Reduced manual intervention

## Technical Specifications for ChatGPT

### Required AWS Services
- Lambda (Python 3.9+)
- RDS PostgreSQL 13+
- S3 for storage
- EventBridge for scheduling
- CloudWatch for monitoring
- SNS for alerts

### Code Requirements
- Async/await patterns
- Connection pooling
- Exponential backoff retry
- Comprehensive error handling
- Structured logging
- Unit and integration tests

### Data Requirements
- Real-time collection
- Data validation
- Duplicate detection
- Historical analysis
- Export capabilities

### Monitoring Requirements
- Collection success rates
- Data quality metrics
- Performance benchmarks
- Error tracking
- Cost monitoring

## Success Metrics

**Performance**:
- Collection time < 1 minute
- 99.9% uptime
- < 1% error rate

**Data Quality**:
- 100% data completeness
- Real-time updates
- Historical accuracy

**Cost Efficiency**:
- < $25/month total cost
- Pay-per-use model
- Scalable architecture

This system should provide a robust, automated, and cost-effective solution for collecting ShapeShift affiliate fee data across all supported platforms. 