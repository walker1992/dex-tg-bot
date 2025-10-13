"""
Custom Exceptions for Telegram Bot
"""


class BotError(Exception):
    """Base exception for bot errors"""
    pass


class AuthenticationError(BotError):
    """Authentication related errors"""
    pass


class AuthorizationError(BotError):
    """Authorization related errors"""
    pass


class TradingError(BotError):
    """Trading related errors"""
    pass


class ValidationError(BotError):
    """Input validation errors"""
    pass


class ServiceError(BotError):
    """Service layer errors"""
    pass


class StorageError(BotError):
    """Storage related errors"""
    pass


class ConfigurationError(BotError):
    """Configuration related errors"""
    pass


class NetworkError(BotError):
    """Network related errors"""
    pass


class RateLimitError(BotError):
    """Rate limiting errors"""
    pass
