import logging
from shared.logging import setup_logging, get_logger

def test_get_logger_and_setup_logging(caplog):
    setup_logging(level=logging.INFO)
    logger = get_logger('test_logger')
    with caplog.at_level(logging.INFO):
        logger.info('Test log message')
    assert any('Test log message' in record.message for record in caplog.records)
    assert any('test_logger' in record.name for record in caplog.records) 