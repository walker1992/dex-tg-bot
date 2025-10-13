"""
Custom exceptions for exchange services
"""
from typing import Any, Dict, Optional


class ExchangeServiceError(Exception):
    """Base exception for exchange service errors"""
    
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}


class ConnectionError(ExchangeServiceError):
    """Connection related errors"""
    pass


class AuthenticationError(ExchangeServiceError):
    """Authentication related errors"""
    pass


class AuthorizationError(ExchangeServiceError):
    """Authorization related errors"""
    pass


class RateLimitError(ExchangeServiceError):
    """Rate limit exceeded errors"""
    
    def __init__(self, message: str, retry_after: Optional[int] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


class InsufficientBalanceError(ExchangeServiceError):
    """Insufficient balance errors"""
    pass


class InvalidSymbolError(ExchangeServiceError):
    """Invalid symbol errors"""
    pass


class InvalidOrderError(ExchangeServiceError):
    """Invalid order errors"""
    pass


class OrderNotFoundError(ExchangeServiceError):
    """Order not found errors"""
    pass


class OrderExecutionError(ExchangeServiceError):
    """Order execution errors"""
    pass


class MarketDataError(ExchangeServiceError):
    """Market data errors"""
    pass


class WebSocketError(ExchangeServiceError):
    """WebSocket related errors"""
    pass


class ConfigurationError(ExchangeServiceError):
    """Configuration related errors"""
    pass


class ValidationError(ExchangeServiceError):
    """Validation errors"""
    pass


class TimeoutError(ExchangeServiceError):
    """Timeout errors"""
    pass


class NetworkError(ExchangeServiceError):
    """Network related errors"""
    pass


class ServiceUnavailableError(ExchangeServiceError):
    """Service unavailable errors"""
    pass


class MaintenanceError(ExchangeServiceError):
    """Exchange maintenance errors"""
    pass


class HyperliquidError(ExchangeServiceError):
    """Hyperliquid specific errors"""
    pass


class AsterError(ExchangeServiceError):
    """Aster specific errors"""
    pass


def handle_exchange_error(error: Exception, exchange: str = "unknown") -> ExchangeServiceError:
    """Convert generic exceptions to exchange service errors"""
    
    error_message = str(error)
    error_type = type(error).__name__
    
    # Map common error types
    if "connection" in error_message.lower() or "timeout" in error_message.lower():
        return ConnectionError(f"{exchange} connection error: {error_message}")
    
    elif "authentication" in error_message.lower() or "unauthorized" in error_message.lower():
        return AuthenticationError(f"{exchange} authentication error: {error_message}")
    
    elif "rate limit" in error_message.lower() or "too many requests" in error_message.lower():
        return RateLimitError(f"{exchange} rate limit exceeded: {error_message}")
    
    elif "insufficient balance" in error_message.lower() or "balance" in error_message.lower():
        return InsufficientBalanceError(f"{exchange} insufficient balance: {error_message}")
    
    elif "invalid symbol" in error_message.lower() or "symbol" in error_message.lower():
        return InvalidSymbolError(f"{exchange} invalid symbol: {error_message}")
    
    elif "order" in error_message.lower():
        if "not found" in error_message.lower():
            return OrderNotFoundError(f"{exchange} order not found: {error_message}")
        else:
            return InvalidOrderError(f"{exchange} order error: {error_message}")
    
    elif "websocket" in error_message.lower():
        return WebSocketError(f"{exchange} websocket error: {error_message}")
    
    elif "network" in error_message.lower() or "connection" in error_message.lower():
        return NetworkError(f"{exchange} network error: {error_message}")
    
    else:
        return ExchangeServiceError(f"{exchange} error: {error_message}")


def get_error_code_from_response(response_data: Dict[str, Any], exchange: str = "unknown") -> Optional[str]:
    """Extract error code from exchange response"""
    
    if exchange.lower() == "hyperliquid":
        # Hyperliquid error format
        if "error" in response_data:
            return str(response_data.get("error"))
        elif "code" in response_data:
            return str(response_data.get("code"))
    
    elif exchange.lower() == "aster":
        # Aster error format (similar to Binance)
        if "code" in response_data:
            return str(response_data.get("code"))
        elif "error" in response_data:
            return str(response_data.get("error"))
    
    return None


def get_error_message_from_response(response_data: Dict[str, Any], exchange: str = "unknown") -> str:
    """Extract error message from exchange response"""
    
    if exchange.lower() == "hyperliquid":
        # Hyperliquid error format
        if "error" in response_data:
            return str(response_data.get("error"))
        elif "message" in response_data:
            return str(response_data.get("message"))
    
    elif exchange.lower() == "aster":
        # Aster error format (similar to Binance)
        if "msg" in response_data:
            return str(response_data.get("msg"))
        elif "message" in response_data:
            return str(response_data.get("message"))
        elif "error" in response_data:
            return str(response_data.get("error"))
    
    return "Unknown error"


def create_exchange_error(response_data: Dict[str, Any], exchange: str = "unknown") -> ExchangeServiceError:
    """Create appropriate exchange error from response data"""
    
    error_code = get_error_code_from_response(response_data, exchange)
    error_message = get_error_message_from_response(response_data, exchange)
    
    # Map specific error codes to appropriate exception types
    if exchange.lower() == "aster":
        if error_code in ["-1021", "-1022"]:
            return AuthenticationError(f"Aster authentication error: {error_message}", error_code)
        elif error_code in ["-1003", "-1004"]:
            return RateLimitError(f"Aster rate limit exceeded: {error_message}", error_code)
        elif error_code in ["-2010", "-2011"]:
            return InsufficientBalanceError(f"Aster insufficient balance: {error_message}", error_code)
        elif error_code in ["-1121", "-1122"]:
            return InvalidSymbolError(f"Aster invalid symbol: {error_message}", error_code)
        elif error_code in ["-2013", "-2014"]:
            return OrderNotFoundError(f"Aster order not found: {error_message}", error_code)
        elif error_code in ["-1013", "-1014"]:
            return InvalidOrderError(f"Aster invalid order: {error_message}", error_code)
    
    # Default to generic exchange error
    return ExchangeServiceError(f"{exchange} error: {error_message}", error_code)
