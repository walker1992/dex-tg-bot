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
        """Log incoming requests"""
        start_time = time.time()
        self.request_count += 1
        
        # Extract request information
        user_id = update.effective_user.id if update.effective_user else None
        username = update.effective_user.username if update.effective_user else None
        chat_id = update.effective_chat.id if update.effective_chat else None
        
        # Log message content
        message_text = ""
        if update.effective_message:
            message_text = update.effective_message.text or ""
        
        # Log callback query
        callback_data = ""
        if update.callback_query:
            callback_data = update.callback_query.data or ""
        
        # Determine request type
        request_type = "unknown"
        if update.effective_message and update.effective_message.text:
            if update.effective_message.text.startswith("/"):
                request_type = "command"
            else:
                request_type = "message"
        elif update.callback_query:
            request_type = "callback"
        
        # Log request
        logger.info(
            f"Request #{self.request_count} | "
            f"Type: {request_type} | "
            f"User: {user_id} (@{username}) | "
            f"Chat: {chat_id} | "
            f"Content: {message_text[:100]}{'...' if len(message_text) > 100 else ''} | "
            f"Callback: {callback_data}"
        )
        
        # Log errors if any
        if context.error:
            logger.error(
                f"Request #{self.request_count} | "
                f"Error: {context.error} | "
                f"User: {user_id} (@{username})"
            )
        
        # Log response time
        end_time = time.time()
        response_time = end_time - start_time
        
        if response_time > 1.0:  # Log slow requests
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
        """Log configuration change"""
        self.logger.info(
            f"Config change | "
            f"User: {user_id} | "
            f"Key: {config_key} | "
            f"Old: {old_value} | "
            f"New: {new_value}"
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
        """Log API key usage"""
        self.logger.info(
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
        """Log API call performance"""
        self.logger.info(
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
