#!/usr/bin/env python3
"""
Error Handler for ShapeShift Affiliate Tracker
Centralized error handling and recovery utilities
"""

import logging
import traceback
import time
from typing import Any, Callable, Dict, List, Optional, Union
from functools import wraps


class ErrorHandler:
    """
    Centralized error handling for all listeners

    This class provides:
    1. Consistent error logging and formatting
    2. Retry mechanisms for transient failures
    3. Error categorization and reporting
    4. Graceful degradation strategies
    """

    def __init__(self, logger: logging.Logger = None):
        """Initialize error handler with optional logger"""
        self.logger = logger or logging.getLogger(__name__)
        self.error_counts = {}
        self.last_error_time = {}

    def handle_api_error(
        self, error: Exception, context: str, retry_count: int = 0
    ) -> bool:
        """
        Handle API-related errors with retry logic

        Args:
            error (Exception): The error that occurred
            context (str): Context where the error occurred
            retry_count (int): Current retry attempt

        Returns:
            bool: True if error was handled and retry should be attempted
        """

        error_type = type(error).__name__

        # Log the error with context
        self.logger.error(f"❌ API Error in {context}: {error_type} - {error}")

        # Categorize errors for different handling strategies
        if "timeout" in str(error).lower() or "connection" in str(error).lower():
            # Network/connection errors - retry with exponential backoff
            if retry_count < 3:
                wait_time = min(2**retry_count, 30)  # Max 30 seconds
                self.logger.info(
                    f"🔄 Retrying {context} in {wait_time} seconds (attempt {retry_count + 1}/3)"
                )
                time.sleep(wait_time)
                return True
            else:
                self.logger.error(f"❌ Max retries exceeded for {context}")
                return False

        elif "rate limit" in str(error).lower() or "429" in str(error):
            # Rate limiting - wait longer and retry
            if retry_count < 2:
                wait_time = 60 * (retry_count + 1)  # 1 minute, then 2 minutes
                self.logger.info(
                    f"⏳ Rate limited, waiting {wait_time} seconds before retry"
                )
                time.sleep(wait_time)
                return True
            else:
                self.logger.error(f"❌ Rate limit exceeded for {context}")
                return False

        elif "404" in str(error) or "not found" in str(error).lower():
            # Resource not found - don't retry
            self.logger.warning(f"⚠️ Resource not found in {context}, skipping")
            return False

        elif "500" in str(error) or "server error" in str(error).lower():
            # Server errors - retry with backoff
            if retry_count < 2:
                wait_time = 10 * (retry_count + 1)
                self.logger.info(f"🔄 Server error, retrying in {wait_time} seconds")
                time.sleep(wait_time)
                return True
            else:
                self.logger.error(f"❌ Server error persisted for {context}")
                return False

        # Default: don't retry for unknown errors
        return False

    def handle_blockchain_error(
        self, error: Exception, context: str, chain_name: str
    ) -> bool:
        """
        Handle blockchain-specific errors

        Args:
            error (Exception): The error that occurred
            context (str): Context where the error occurred
            chain_name (str): Name of the blockchain

        Returns:
            bool: True if operation should continue, False if should stop
        """

        error_type = type(error).__name__
        error_msg = str(error).lower()

        # Log blockchain-specific errors
        self.logger.error(
            f"❌ Blockchain Error on {chain_name} in {context}: {error_type} - {error}"
        )

        # Handle common blockchain errors
        if "nonce" in error_msg or "replacement" in error_msg:
            self.logger.warning(
                f"⚠️ Nonce issue on {chain_name}, may need to wait for confirmation"
            )
            return True

        elif "insufficient funds" in error_msg or "balance" in error_msg:
            self.logger.error(
                f"❌ Insufficient funds on {chain_name}, stopping operations"
            )
            return False

        elif "gas" in error_msg:
            self.logger.warning(
                f"⚠️ Gas estimation issue on {chain_name}, may need manual gas setting"
            )
            return True

        elif "network" in error_msg or "connection" in error_msg:
            self.logger.warning(f"⚠️ Network issue on {chain_name}, may be temporary")
            return True

        # Default: continue for unknown errors
        return True

    def handle_data_validation_error(
        self, error: Exception, context: str, data: Any
    ) -> bool:
        """
        Handle data validation errors

        Args:
            error (Exception): The validation error
            context (str): Context where validation failed
            data (Any): The data that failed validation

        Returns:
            bool: True if error was handled gracefully
        """

        error_type = type(error).__name__

        # Log validation errors with data context
        self.logger.warning(
            f"⚠️ Data Validation Error in {context}: {error_type} - {error}"
        )

        if hasattr(data, "__len__"):
            self.logger.info(f"📊 Data length: {len(data)}")

        # Handle specific validation errors
        if "missing" in str(error).lower():
            self.logger.info(f"💡 Missing field detected, skipping invalid record")
            return True

        elif "type" in str(error).lower():
            self.logger.info(f"💡 Type mismatch detected, attempting conversion")
            return True

        elif "format" in str(error).lower():
            self.logger.info(f"💡 Format issue detected, attempting cleanup")
            return True

        # Default: log and continue
        return True

    def retry_on_error(
        self, max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0
    ):
        """
        Decorator for retrying functions on error

        Args:
            max_retries (int): Maximum number of retry attempts
            delay (float): Initial delay between retries in seconds
            backoff (float): Multiplier for delay on each retry
        """

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                last_exception = None
                current_delay = delay

                for attempt in range(max_retries + 1):
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        last_exception = e

                        if attempt < max_retries:
                            self.logger.warning(f"⚠️ Attempt {attempt + 1} failed: {e}")
                            self.logger.info(
                                f"🔄 Retrying in {current_delay} seconds..."
                            )
                            time.sleep(current_delay)
                            current_delay *= backoff
                        else:
                            self.logger.error(
                                f"❌ All {max_retries + 1} attempts failed"
                            )
                            break

                # Re-raise the last exception if all retries failed
                raise last_exception

            return wrapper

        return decorator

    def log_error_summary(self) -> Dict[str, Any]:
        """
        Generate a summary of errors encountered

        Returns:
            Dict[str, Any]: Summary of error counts and types
        """

        if not self.error_counts:
            return {"total_errors": 0, "error_types": {}}

        total_errors = sum(self.error_counts.values())
        error_types = {}

        for error_key, count in self.error_counts.items():
            error_type = error_key.split(":")[0] if ":" in error_key else "unknown"
            error_types[error_type] = error_types.get(error_type, 0) + count

        summary = {
            "total_errors": total_errors,
            "error_types": error_types,
            "error_details": self.error_counts.copy(),
        }

        return summary

    def reset_error_counts(self):
        """Reset error tracking counters"""
        self.error_counts.clear()
        self.last_error_time.clear()
        self.logger.info("🔄 Error counters reset")


# Global error handler instance
error_handler = ErrorHandler()


# Convenience functions for common error handling patterns
def handle_api_errors(func: Callable) -> Callable:
    """Decorator for handling API errors with retry logic"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        max_retries = 3
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt < max_retries - 1:
                    if error_handler.handle_api_error(e, func.__name__, attempt):
                        continue
                raise e
        return func(*args, **kwargs)

    return wrapper


def handle_blockchain_errors(func: Callable) -> Callable:
    """Decorator for handling blockchain errors"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Extract chain name from args if available
            chain_name = "unknown"
            if args and hasattr(args[0], "chain_name"):
                chain_name = args[0].chain_name
            elif "chain_name" in kwargs:
                chain_name = kwargs["chain_name"]

            if not error_handler.handle_blockchain_error(e, func.__name__, chain_name):
                raise e
            return None

    return wrapper
