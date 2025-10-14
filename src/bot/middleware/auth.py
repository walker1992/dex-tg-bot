"""
Authentication Middleware for Telegram Bot
"""
import logging
from typing import Callable, Awaitable, Any
from telegram import Update
from telegram.ext import ContextTypes

from services.config import ServiceConfig
from bot.utils.exceptions import AuthenticationError

logger = logging.getLogger(__name__)


class AuthMiddleware:
    """Authentication middleware for user access control"""
    
    def __init__(self, config: ServiceConfig):
        self.config = config
        self.failed_attempts = {}  # Track failed login attempts
    
    async def check_auth(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """Check user authentication"""
        if not update.effective_user:
            return False
        
        user_id = update.effective_user.id
        
        # Check if user is allowed
        if not self._is_user_allowed(user_id):
            await self._handle_unauthorized_user(update, context)
            return False
        
        # Check for rate limiting
        if self._is_rate_limited(user_id):
            await self._handle_rate_limited_user(update, context)
            return False
        
        # Reset failed attempts on successful access
        if user_id in self.failed_attempts:
            del self.failed_attempts[user_id]
        
        return True
    
    def _is_user_allowed(self, user_id: int) -> bool:
        """Check if user is in allowed users list"""
        allowed_users = self.config.telegram.allowed_users
        
        # If no allowed users specified, allow all
        if not allowed_users:
            return True
        
        return user_id in allowed_users
    
    def _is_rate_limited(self, user_id: int) -> bool:
        """Check if user is rate limited"""
        if user_id not in self.failed_attempts:
            return False
        
        failed_count = self.failed_attempts[user_id]["count"]
        max_attempts = self.config.security.max_login_attempts
        
        return failed_count >= max_attempts
    
    async def _handle_unauthorized_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle unauthorized user access"""
        user_id = update.effective_user.id
        username = update.effective_user.username or "Unknown"
        
        logger.warning(f"Unauthorized access attempt from user {user_id} (@{username})")
        
        # Track failed attempt
        self._track_failed_attempt(user_id)
        
        # Send response
        if update.effective_message:
            await update.effective_message.reply_text(
                "❌ Access denied. You are not authorized to use this bot."
            )
    
    async def _handle_rate_limited_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle rate limited user"""
        user_id = update.effective_user.id
        
        logger.warning(f"Rate limited user {user_id} attempted access")
        
        if update.effective_message:
            await update.effective_message.reply_text(
                "❌ Too many failed attempts. Please try again later."
            )
    
    def _track_failed_attempt(self, user_id: int):
        """Track failed login attempt"""
        import time
        
        current_time = time.time()
        
        if user_id not in self.failed_attempts:
            self.failed_attempts[user_id] = {
                "count": 0,
                "first_attempt": current_time
            }
        
        self.failed_attempts[user_id]["count"] += 1
        self.failed_attempts[user_id]["last_attempt"] = current_time
    
    def is_admin(self, user_id: int) -> bool:
        """Check if user is admin"""
        admin_users = self.config.telegram.admin_users
        return user_id in admin_users if admin_users else False
    
    def get_user_role(self, user_id: int) -> str:
        """Get user role"""
        if self.is_admin(user_id):
            return "admin"
        elif self._is_user_allowed(user_id):
            return "user"
        else:
            return "unauthorized"


def require_permission(permission: str):
    """Decorator to require specific permission"""
    def decorator(func: Callable[[Update, ContextTypes.DEFAULT_TYPE], Awaitable[Any]]):
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            if not update.effective_user:
                await update.effective_message.reply_text("❌ User not found")
                return
            
            user_id = update.effective_user.id
            
            # Get auth middleware from bot data
            auth_middleware = context.bot_data.get('auth_middleware')
            
            if not auth_middleware:
                if update.effective_message:
                    await update.effective_message.reply_text("❌ Authentication system not available")
                return
            
            # Check permission
            if permission == "admin" and not auth_middleware.is_admin(user_id):
                if update.effective_message:
                    await update.effective_message.reply_text("❌ Admin permission required")
                return
            
            if permission == "user" and not auth_middleware._is_user_allowed(user_id):
                if update.effective_message:
                    await update.effective_message.reply_text("❌ User permission required")
                return
            
            # Permission granted, execute function
            return await func(update, context)
        
        return wrapper
    return decorator


def require_admin(func: Callable[[Update, ContextTypes.DEFAULT_TYPE], Awaitable[Any]]):
    """Decorator to require admin permission"""
    return require_permission("admin")(func)


def require_user(func: Callable[[Update, ContextTypes.DEFAULT_TYPE], Awaitable[Any]]):
    """Decorator to require user permission"""
    return require_permission("user")(func)
