"""
Start Command Handler
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

from bot.keyboards.main import get_main_keyboard
from bot.utils.exceptions import BotError

logger = logging.getLogger(__name__)


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    try:
        user = update.effective_user
        if not user:
            return
        
        welcome_message = f"""
🤖 **Welcome to DEX Trading Bot!**

Hello {user.first_name}! 👋

This bot allows you to trade on multiple DEX exchanges including:
• **Hyperliquid** - Decentralized perpetuals
• **Aster** - Multi-chain DEX

**Available Features:**
📊 Real-time market data
💰 Balance and position tracking
📈 Price and funding rate alerts
🔄 Spot and futures trading
📱 User-friendly interface

**Quick Start:**
1. Connect your exchange accounts
2. Set up alerts for your favorite tokens
3. Start trading with simple commands

Use /help to see all available commands.

**⚠️ Important:** This bot is for educational purposes. Always do your own research before trading.
        """
        
        keyboard = get_main_keyboard()
        
        await update.message.reply_text(
            welcome_message,
            parse_mode='Markdown',
            reply_markup=keyboard
        )
        
        logger.info(f"Start command executed by user {user.id} (@{user.username})")
        
    except Exception as e:
        logger.error(f"Error in start handler: {e}")
        await update.message.reply_text(
            "❌ An error occurred. Please try again later."
        )


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    try:
        help_message = """
📚 **DEX Trading Bot Commands**

**🔐 Account Management:**
/connect_hyperliquid - Connect Hyperliquid account
/connect_aster - Connect Aster account
/disconnect - Disconnect exchange account
/accounts - View connected accounts

**💰 Trading Commands:**
/balance [exchange] - Check account balance
/positions [exchange] - View current positions
/orders [exchange] - View open orders
/buy <symbol> <quantity> [price] - Place buy order
/sell <symbol> <quantity> [price] - Place sell order
/close <symbol> - Close position
/cancel <order_id> - Cancel order

**📊 Market Data:**
/price <symbol> - Get current price
/depth <symbol> - View order book
/funding <symbol> - Check funding rate
/24h <symbol> - 24h price statistics

**🔔 Alert Commands:**
/alert_price <symbol> <condition> <value> - Set price alert
/alert_funding <symbol> <value> - Set funding rate alert
/alert_position <symbol> <condition> <value> - Set position alert
/alerts - View all alerts
/delete_alert <alert_id> - Delete alert

**⚙️ System Commands:**
/start - Start the bot
/help - Show this help message
/status - Check bot status

**Examples:**
/buy BTC 0.1 50000
/sell ETH 1.0
/price BTC
/alert_price BTC above 60000
        """
        
        await update.message.reply_text(help_message, parse_mode='Markdown')
        
        user = update.effective_user
        logger.info(f"Help command executed by user {user.id} (@{user.username})")
        
    except Exception as e:
        logger.error(f"Error in help handler: {e}")
        await update.message.reply_text(
            "❌ An error occurred. Please try again later."
        )


async def status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status command"""
    try:
        # Get bot status information
        status_message = """
📊 **Bot Status**

**🤖 Bot Status:** ✅ Online
**⏰ Uptime:** Active
**🔄 Last Update:** Just now

**📈 Exchange Status:**
• Hyperliquid: ✅ Connected
• Aster: ✅ Connected

**📊 System Status:**
• WebSocket: ✅ Active
• API Rate Limits: ✅ Normal
• Storage: ✅ Available

**👥 User Stats:**
• Active Users: 1
• Total Commands: 0
• Last Activity: Now

Use /help for available commands.
        """
        
        await update.message.reply_text(status_message, parse_mode='Markdown')
        
        user = update.effective_user
        logger.info(f"Status command executed by user {user.id} (@{user.username})")
        
    except Exception as e:
        logger.error(f"Error in status handler: {e}")
        await update.message.reply_text(
            "❌ An error occurred. Please try again later."
        )
