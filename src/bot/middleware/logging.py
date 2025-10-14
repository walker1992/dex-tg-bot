"""
Logging Middleware for Telegram Bot
"""
import logging
import time
from typing import Callable, Awaitable, Any
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


class LoggingMiddleware:
    """Logging middleware for request/response logging"""
    
    def __init__(self):
        self.request_count = 0
    
    async def log_request(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Log user actions concisely; suppress low-level HTTP logs elsewhere"""
        start_time = time.time()
        self.request_count += 1
        
        # Extract request information
        user_id = update.effective_user.id if update.effective_user else None
        username = update.effective_user.username if update.effective_user else None
        first_name = update.effective_user.first_name if update.effective_user else None
        chat_id = update.effective_chat.id if update.effective_chat else None
        
        # Log commands and button clicks
        try:
            if update.message and update.message.text and update.message.text.startswith('/'):
                logger.info(
                    f"UserAction | Command: {update.message.text} | User: {user_id} (@{username}) {first_name} | Chat: {chat_id}"
                )
            elif update.callback_query and update.callback_query.data:
                logger.info(
                    f"UserAction | Callback: {update.callback_query.data} | User: {user_id} (@{username}) {first_name} | Chat: {chat_id}"
                )
        except Exception:
            pass
        
        # Only log errors
        if context.error:
            logger.error(
                f"Request #{self.request_count} | "
                f"Error: {context.error} | "
                f"User: {user_id} (@{username})"
            )
        
        # Log response time only for slow requests (>2s instead of 1s)
        end_time = time.time()
        response_time = end_time - start_time
        
        if response_time > 2.0:  # Increased threshold and only log slow requests
            logger.warning(
                f"Request #{self.request_count} | "
                f"Slow request: {response_time:.2f}s | "
                f"User: {user_id} (@{username})"
            )


class SecurityLogger:
    """Security-specific logging"""
    
    def __init__(self):
        self.logger = logging.getLogger('security')
    
    def log_trade_attempt(self, user_id: int, action: str, details: dict):
        """Log trade attempt"""
        self.logger.warning(
            f"Trade attempt | "
            f"User: {user_id} | "
            f"Action: {action} | "
            f"Details: {details}"
        )
    
    def log_config_change(self, user_id: int, config_key: str, old_value, new_value):
        """Log configuration change - only log important changes"""
        # Only log sensitive config changes
        if config_key in ['api_key', 'secret_key', 'passphrase']:
            self.logger.warning(
                f"Config change | "
                f"User: {user_id} | "
                f"Key: {config_key} | "
                f"Changed"
            )
    
    def log_unauthorized_access(self, user_id: int, action: str, details: dict):
        """Log unauthorized access attempt"""
        self.logger.warning(
            f"Unauthorized access | "
            f"User: {user_id} | "
            f"Action: {action} | "
            f"Details: {details}"
        )
    
    def log_api_key_usage(self, user_id: int, exchange: str, action: str):
        """Log API key usage - only log errors and sensitive actions"""
        # Only log sensitive actions
        if action in ['create', 'delete', 'update']:
            self.logger.warning(
                f"API key usage | "
                f"User: {user_id} | "
                f"Exchange: {exchange} | "
                f"Action: {action}"
            )


class PerformanceLogger:
    """Performance monitoring"""
    
    def __init__(self):
        self.logger = logging.getLogger('performance')
        self.metrics = {}
    
    def log_api_call(self, exchange: str, endpoint: str, duration: float, success: bool):
        """Log API call performance - only log failures and slow calls"""
        # Only log failures or slow calls (>1s)
        if not success or duration > 1.0:
            level = "error" if not success else "warning"
            getattr(self.logger, level)(
                f"API call | "
                f"Exchange: {exchange} | "
                f"Endpoint: {endpoint} | "
                f"Duration: {duration:.3f}s | "
                f"Success: {success}"
            )
        
        # Track metrics
        key = f"{exchange}_{endpoint}"
        if key not in self.metrics:
            self.metrics[key] = {
                "count": 0,
                "total_duration": 0,
                "success_count": 0,
                "error_count": 0
            }
        
        self.metrics[key]["count"] += 1
        self.metrics[key]["total_duration"] += duration
        
        if success:
            self.metrics[key]["success_count"] += 1
        else:
            self.metrics[key]["error_count"] += 1
    
    def get_metrics(self) -> dict:
        """Get performance metrics"""
        return self.metrics.copy()
    
    def log_slow_operation(self, operation: str, duration: float, details: dict):
        """Log slow operations"""
        self.logger.warning(
            f"Slow operation | "
            f"Operation: {operation} | "
            f"Duration: {duration:.3f}s | "
            f"Details: {details}"
        )


# Global instances
security_logger = SecurityLogger()
performance_logger = PerformanceLogger()
