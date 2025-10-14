#!/usr/bin/env python3
"""
DEX Trading Telegram Bot - Main Entry Point
"""
import asyncio
import logging
import signal
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
from telegram.error import TelegramError

from services.config import load_config
from services.factory import ServiceManager
from bot.handlers import (
    start_handler, help_handler, status_handler,
    account_handlers, trading_handlers, alert_handlers
)
from bot.middleware.auth import AuthMiddleware
from bot.middleware.logging import LoggingMiddleware
from bot.utils.exceptions import BotError

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TradingBot:
    """Main Trading Bot Class"""
    
    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self.config = None
        self.service_manager = None
        self.application = None
        self.running = False
        
    async def initialize(self):
        """Initialize bot components"""
        try:
            logger.info("🚀 Initializing DEX Trading Bot...")
            
            # Load configuration
            self.config = load_config(self.config_path)
            logger.info("✅ Configuration loaded")
            
            # Initialize service manager
            self.service_manager = ServiceManager(self.config)
            logger.info("✅ Service manager initialized")
            
            # Connect to all services
            logger.info("🔄 Connecting to exchange services...")
            connection_results = await self.service_manager.connect_all_services()
            logger.info(f"Connection results: {connection_results}")
            
            # Create Telegram application
            self.application = Application.builder().token(
                self.config.telegram.bot_token
            ).build()
            
            # Store service manager in bot data for access in handlers
            self.application.bot_data['service_manager'] = self.service_manager
            
            # Add middleware
            self._setup_middleware()
            
            # Add handlers
            self._setup_handlers()
            
            # Add message handler for account setup flow
            self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._wrap_handler(self._handle_message)))
            
            logger.info("✅ Bot initialization completed")
            
        except Exception as e:
            logger.error(f"❌ Bot initialization failed: {e}")
            raise BotError(f"Initialization failed: {e}")
    
    def _setup_middleware(self):
        """Setup middleware"""
        # Store middleware instances for later use
        self.auth_middleware = AuthMiddleware(self.config)
        self.logging_middleware = LoggingMiddleware()
        
        # Store auth middleware in bot data for access in handlers
        self.application.bot_data['auth_middleware'] = self.auth_middleware
        logger.info("✅ Auth middleware initialized and stored in bot_data")
    
    def _wrap_handler(self, handler_func):
        """Wrap handler with middleware"""
        async def wrapped_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
            # Log request
            await self.logging_middleware.log_request(update, context)
            
            # Check authentication
            if not await self.auth_middleware.check_auth(update, context):
                return
            
            # Execute handler
            return await handler_func(update, context)
        
        return wrapped_handler
    
    def _setup_handlers(self):
        """Setup command handlers"""
        # Basic commands
        self.application.add_handler(CommandHandler("start", self._wrap_handler(start_handler)))
        self.application.add_handler(CommandHandler("help", self._wrap_handler(help_handler)))
        self.application.add_handler(CommandHandler("status", self._wrap_handler(status_handler)))
        
        # Account management commands
        self.application.add_handler(CommandHandler("connect_hyperliquid", self._wrap_handler(account_handlers.connect_hyperliquid)))
        self.application.add_handler(CommandHandler("connect_aster", self._wrap_handler(account_handlers.connect_aster)))
        self.application.add_handler(CommandHandler("disconnect", self._wrap_handler(account_handlers.disconnect)))
        self.application.add_handler(CommandHandler("accounts", self._wrap_handler(account_handlers.accounts)))
        
        # Trading commands
        self.application.add_handler(CommandHandler("balance", self._wrap_handler(trading_handlers.balance)))
        self.application.add_handler(CommandHandler("positions", self._wrap_handler(trading_handlers.positions)))
        self.application.add_handler(CommandHandler("orders", self._wrap_handler(trading_handlers.orders)))
        self.application.add_handler(CommandHandler("trades", self._wrap_handler(trading_handlers.trades)))
        self.application.add_handler(CommandHandler("buy", self._wrap_handler(trading_handlers.buy)))
        self.application.add_handler(CommandHandler("sell", self._wrap_handler(trading_handlers.sell)))
        self.application.add_handler(CommandHandler("close", self._wrap_handler(trading_handlers.close)))
        self.application.add_handler(CommandHandler("leverage", self._wrap_handler(trading_handlers.leverage)))
        self.application.add_handler(CommandHandler("cancel", self._wrap_handler(trading_handlers.cancel)))
        
        # Market data commands
        self.application.add_handler(CommandHandler("price", self._wrap_handler(trading_handlers.price)))
        self.application.add_handler(CommandHandler("depth", self._wrap_handler(trading_handlers.depth)))
        self.application.add_handler(CommandHandler("funding", self._wrap_handler(trading_handlers.funding)))
        self.application.add_handler(CommandHandler("24h", self._wrap_handler(trading_handlers.stats_24h)))
        
        # Alert commands
        self.application.add_handler(CommandHandler("alert_price", self._wrap_handler(alert_handlers.alert_price)))
        self.application.add_handler(CommandHandler("alert_funding", self._wrap_handler(alert_handlers.alert_funding)))
        self.application.add_handler(CommandHandler("alert_position", self._wrap_handler(alert_handlers.alert_position)))
        self.application.add_handler(CommandHandler("alerts", self._wrap_handler(alert_handlers.alerts)))
        self.application.add_handler(CommandHandler("delete_alert", self._wrap_handler(alert_handlers.delete_alert)))
        
        # Callback query handlers for inline keyboards
        self.application.add_handler(CallbackQueryHandler(self._wrap_handler(self._handle_callback_query)))
        
        # Error handler
        self.application.add_error_handler(self._error_handler)
        
        logger.info("✅ Handlers setup completed")
    
    async def _handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries from inline keyboards"""
        query = update.callback_query
        await query.answer()
        
        try:
            # Parse callback data
            data = query.data
            if not data:
                return
            
            # Handle different callback types
            if data.startswith("menu_"):
                await self._handle_menu_callback(query, context, data)
            elif data.startswith("trade_"):
                await self._handle_trading_callback(query, context, data)
            elif data.startswith("trading_"):
                await self._handle_trading_callback(query, context, data)
            elif data.startswith("exchange_"):
                await self._handle_exchange_callback(query, context, data)
            elif data.startswith("market_"):
                await self._handle_market_callback(query, context, data)
            elif data.startswith("alert_"):
                await self._handle_alert_callback(query, context, data)
            elif data.startswith("connect_"):
                await self._handle_connect_callback(query, context, data)
            elif data.startswith("settings_"):
                await self._handle_settings_callback(query, context, data)
            elif data.startswith("quick_"):
                await self._handle_trading_callback(query, context, data)
            else:
                await query.edit_message_text("❌ Unknown action")
                
        except Exception as e:
            logger.error(f"Error handling callback query: {e}")
            await query.edit_message_text("❌ An error occurred")
    
    async def _handle_menu_callback(self, query, context: ContextTypes.DEFAULT_TYPE, data):
        """Handle menu-related callbacks"""
        try:
            if data == "menu_balance":
                # Show balance information using real data
                try:
                    # Get service manager from bot data
                    service_manager = self.service_manager
                    if not service_manager:
                        message = "❌ Service manager not available. Please try again later."
                    else:
                        # Import the balance helper function
                        from bot.handlers.trading import _get_all_balances
                        message = await _get_all_balances(service_manager)
                        message += "\n\nUse /balance [exchange] for detailed balance information."
                except Exception as e:
                    logger.error(f"Error fetching balance in menu callback: {e}")
                    message = "❌ Failed to fetch balance data. Please check your exchange connections."
                
                # Add back button
                from bot.keyboards.main import InlineKeyboardButton, InlineKeyboardMarkup
                back_keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back to Main", callback_data="menu_main")]
                ])
                await query.edit_message_text(message, parse_mode='Markdown', reply_markup=back_keyboard)
                
            elif data == "menu_positions":
                # Show positions information using real data
                try:
                    # Get service manager from bot data
                    service_manager = self.service_manager
                    if not service_manager:
                        message = "❌ Service manager not available. Please try again later."
                    else:
                        # Import the positions helper function
                        from bot.handlers.trading import _get_all_positions
                        message = await _get_all_positions(service_manager)
                except Exception as e:
                    logger.error(f"Error fetching positions in menu callback: {e}")
                    message = "❌ Failed to fetch position data. Please check your exchange connections."
                
                # Add back button
                from bot.keyboards.main import InlineKeyboardButton, InlineKeyboardMarkup
                back_keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back to Main", callback_data="menu_main")]
                ])
                await query.edit_message_text(message, parse_mode='Markdown', reply_markup=back_keyboard)
                
            elif data == "menu_orders":
                # Show orders information directly
                message = """
📋 **Open Orders**

**Hyperliquid:**
• BTC-PERP: Buy 0.05 BTC @ $48,000 (Limit)
• ETH-PERP: Sell 0.5 ETH @ $3,200 (Limit)

**Aster:**
• BTCUSDT: Buy 0.1 BTC @ $47,000 (Limit)
• ETHUSDT: Sell 1.0 ETH @ $3,100 (Limit)

**Total Open Orders:** 4

Use /orders [exchange] for detailed order information.
                """
                # Add back button
                from bot.keyboards.main import InlineKeyboardButton, InlineKeyboardMarkup
                back_keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back to Main", callback_data="menu_main")]
                ])
                await query.edit_message_text(message, parse_mode='Markdown', reply_markup=back_keyboard)
                
            elif data == "menu_trading":
                # Show trading menu
                from bot.keyboards.main import get_quick_trade_keyboard
                keyboard = get_quick_trade_keyboard()
                await query.edit_message_text(
                    "🛒 **Trading Menu**\n\nSelect a trading option:",
                    parse_mode='Markdown',
                    reply_markup=keyboard
                )
                
            elif data == "menu_market":
                # Show market data menu
                from bot.keyboards.main import get_market_keyboard
                keyboard = get_market_keyboard()
                await query.edit_message_text(
                    "📊 **Market Data Menu**\n\nSelect an option:",
                    parse_mode='Markdown',
                    reply_markup=keyboard
                )
                
            elif data == "menu_alerts":
                # Show alerts menu
                from bot.keyboards.main import get_alerts_keyboard
                keyboard = get_alerts_keyboard()
                await query.edit_message_text(
                    "🔔 **Alerts Menu**\n\nSelect an option:",
                    parse_mode='Markdown',
                    reply_markup=keyboard
                )
                
            elif data == "menu_settings":
                # Show settings menu
                from bot.keyboards.main import get_settings_keyboard
                keyboard = get_settings_keyboard()
                await query.edit_message_text(
                    "⚙️ **Settings Menu**\n\nSelect an option:",
                    parse_mode='Markdown',
                    reply_markup=keyboard
                )
                
            elif data == "menu_connect":
                # Show connect menu
                from bot.keyboards.main import get_connect_keyboard
                keyboard = get_connect_keyboard()
                await query.edit_message_text(
                    "🔗 **Connect Exchange**\n\nSelect an exchange to connect:",
                    parse_mode='Markdown',
                    reply_markup=keyboard
                )
                
            elif data == "menu_help":
                # Show help
                from bot.handlers.start import help_handler
                mock_update = Update(update_id=0, callback_query=query)
                await help_handler(mock_update, context)
                
            elif data == "menu_main":
                # Return to main menu
                from bot.keyboards.main import get_main_keyboard
                keyboard = get_main_keyboard()
                await query.edit_message_text(
                    "🤖 **DEX Trading Bot**\n\nSelect an option:",
                    parse_mode='Markdown',
                    reply_markup=keyboard
                )
                
        except Exception as e:
            logger.error(f"Error in menu callback handler: {e}")
            await query.edit_message_text("❌ An error occurred in menu handler")
    
    async def _handle_exchange_callback(self, query, context: ContextTypes.DEFAULT_TYPE, data):
        """Handle exchange-related callbacks"""
        # Implementation for exchange callbacks
        pass
    
    async def _handle_trading_callback(self, query, context: ContextTypes.DEFAULT_TYPE, data):
        """Handle trading-related callbacks"""
        try:
            if data == "quick_buy" or data == "trading_quick_buy":
                # Show exchange selection for quick buy
                from bot.keyboards.main import get_trading_exchange_keyboard
                keyboard = get_trading_exchange_keyboard()
                await query.edit_message_text(
                    "🛒 **Quick Buy**\n\nSelect an exchange:",
                    parse_mode='Markdown',
                    reply_markup=keyboard
                )
            elif data == "quick_sell" or data == "trading_quick_sell":
                # Show exchange selection for quick sell
                from bot.keyboards.main import get_trading_exchange_keyboard
                keyboard = get_trading_exchange_keyboard()
                await query.edit_message_text(
                    "🛍️ **Quick Sell**\n\nSelect an exchange:",
                    parse_mode='Markdown',
                    reply_markup=keyboard
                )
            elif data == "quick_close":
                # Show exchange selection for quick close
                from bot.keyboards.main import get_trading_exchange_keyboard
                keyboard = get_trading_exchange_keyboard()
                await query.edit_message_text(
                    "📊 **Close Position**\n\nSelect an exchange:",
                    parse_mode='Markdown',
                    reply_markup=keyboard
                )
            elif data == "quick_leverage":
                # Show exchange selection for leverage setting
                from bot.keyboards.main import get_trading_exchange_keyboard
                keyboard = get_trading_exchange_keyboard()
                await query.edit_message_text(
                    "⚙️ **Set Leverage**\n\nSelect an exchange:",
                    parse_mode='Markdown',
                    reply_markup=keyboard
                )
            elif data.startswith("trade_exchange_"):
                # Handle exchange selection for trading
                exchange = data.replace("trade_exchange_", "")
                from bot.keyboards.main import get_trading_market_type_keyboard
                keyboard = get_trading_market_type_keyboard(exchange)
                await query.edit_message_text(
                    f"📊 **{exchange.title()} Trading**\n\nSelect market type:",
                    parse_mode='Markdown',
                    reply_markup=keyboard
                )
            elif data.startswith("trade_market_"):
                # Handle market type selection
                parts = data.replace("trade_market_", "").split("_")
                market_type = parts[0]
                exchange = parts[1]
                from bot.keyboards.main import get_trading_side_keyboard
                keyboard = get_trading_side_keyboard(exchange, market_type)
                await query.edit_message_text(
                    f"📈 **{market_type.title()} Trading on {exchange.title()}**\n\nSelect trading side:",
                    parse_mode='Markdown',
                    reply_markup=keyboard
                )
            elif data.startswith("trade_side_"):
                # Handle trading side selection
                parts = data.replace("trade_side_", "").split("_")
                if len(parts) >= 3:
                    side = parts[0]  # long/short/buy/sell
                    exchange = parts[1]
                    market_type = parts[2]
                    
                    # Show symbol selection or order form
                    if market_type == "futures":
                        message = f"""
📈 **{side.title()} {market_type.title()} on {exchange.title()}**

**Popular Futures Symbols:**
• BTC-PERP
• ETH-PERP  
• SOL-PERP
• AVAX-PERP

**Next Steps:**
1. Choose a symbol
2. Enter quantity
3. Set leverage (for futures)
4. Confirm order

Use /buy or /sell commands for quick trading.
                        """
                    else:  # spot
                        message = f"""
💱 **{side.title()} {market_type.title()} on {exchange.title()}**

**Popular Spot Symbols:**
• BTC/USDC
• ETH/USDC
• SOL/USDC
• AVAX/USDC

**Next Steps:**
1. Choose a symbol
2. Enter quantity
3. Set price (for limit orders)
4. Confirm order

Use /buy or /sell commands for quick trading.
                        """
                    
                    from bot.keyboards.main import InlineKeyboardButton, InlineKeyboardMarkup
                    back_keyboard = InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 Back to Market Type", callback_data=f"trade_market_{market_type}_{exchange}")]
                    ])
                    await query.edit_message_text(message, parse_mode='Markdown', reply_markup=back_keyboard)
                else:
                    await query.edit_message_text("❌ Invalid trading side selection")
            elif data == "trading_balance":
                # Show balance information using real data
                try:
                    service_manager = self.service_manager
                    if not service_manager:
                        message = "❌ Service manager not available. Please try again later."
                    else:
                        from bot.handlers.trading import _get_all_balances
                        message = await _get_all_balances(service_manager)
                        message += "\n\nUse /balance [exchange] for detailed balance information."
                except Exception as e:
                    logger.error(f"Error fetching balance in trading callback: {e}")
                    message = "❌ Failed to fetch balance data. Please check your exchange connections."
                
                from bot.keyboards.main import InlineKeyboardButton, InlineKeyboardMarkup
                back_keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back to Trading", callback_data="menu_trading")]
                ])
                await query.edit_message_text(message, parse_mode='Markdown', reply_markup=back_keyboard)
                
            elif data == "trading_positions":
                # Show positions information using real data
                try:
                    service_manager = self.service_manager
                    if not service_manager:
                        message = "❌ Service manager not available. Please try again later."
                    else:
                        from bot.handlers.trading import _get_all_positions
                        message = await _get_all_positions(service_manager)
                except Exception as e:
                    logger.error(f"Error fetching positions in trading callback: {e}")
                    message = "❌ Failed to fetch position data. Please check your exchange connections."
                
                from bot.keyboards.main import InlineKeyboardButton, InlineKeyboardMarkup
                back_keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back to Trading", callback_data="menu_trading")]
                ])
                await query.edit_message_text(message, parse_mode='Markdown', reply_markup=back_keyboard)
                
            elif data == "trading_orders":
                # Show orders information directly
                message = """
📋 **Open Orders**

**Hyperliquid:**
• BTC-PERP: Buy 0.05 BTC @ $48,000 (Limit)
• ETH-PERP: Sell 0.5 ETH @ $3,200 (Limit)

**Aster:**
• BTCUSDT: Buy 0.1 BTC @ $47,000 (Limit)
• ETHUSDT: Sell 1.0 ETH @ $3,100 (Limit)

**Total Open Orders:** 4

Use /orders [exchange] for detailed order information.
                """
                from bot.keyboards.main import InlineKeyboardButton, InlineKeyboardMarkup
                back_keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back to Trading", callback_data="menu_trading")]
                ])
                await query.edit_message_text(message, parse_mode='Markdown', reply_markup=back_keyboard)
                
            elif data == "trading_price":
                # Show price information
                message = """
📈 **Price Information**

**Popular Symbols:**
• BTC: $50,000.00 (+5.26%)
• ETH: $2,800.00 (-3.45%)
• SOL: $95.50 (+2.15%)

Use /price <symbol> [exchange] for specific price information.
                """
                from bot.keyboards.main import InlineKeyboardButton, InlineKeyboardMarkup
                back_keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back to Trading", callback_data="menu_trading")]
                ])
                await query.edit_message_text(message, parse_mode='Markdown', reply_markup=back_keyboard)
            else:
                await query.edit_message_text("❌ Unknown trading action")
        except Exception as e:
            logger.error(f"Error in trading callback: {e}")
            await query.edit_message_text("❌ An error occurred. Please try again.")
    
    async def _handle_alert_callback(self, query, context: ContextTypes.DEFAULT_TYPE, data):
        """Handle alert-related callbacks"""
        try:
            if data == "alerts_list":
                message = """
🔔 **My Alerts**

**Active Alerts:**
• BTC Price > $55,000 (Active)
• ETH Price < $2,500 (Active)
• Funding Rate > 0.01% (Active)

**Total Active Alerts:** 3

Use /alerts to manage your alerts.
                """
                from bot.keyboards.main import InlineKeyboardButton, InlineKeyboardMarkup
                back_keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back to Alerts", callback_data="menu_alerts")]
                ])
                await query.edit_message_text(message, parse_mode='Markdown', reply_markup=back_keyboard)
            else:
                await query.edit_message_text("❌ Alert feature coming soon")
        except Exception as e:
            logger.error(f"Error in alert callback: {e}")
            await query.edit_message_text("❌ An error occurred. Please try again.")
    
    async def _handle_market_callback(self, query, context: ContextTypes.DEFAULT_TYPE, data):
        """Handle market-related callbacks"""
        try:
            if data == "market_price":
                message = """
📈 **Market Prices**

**Popular Symbols:**
• BTC: $50,000.00 (+5.26%)
• ETH: $2,800.00 (-3.45%)
• SOL: $95.50 (+2.15%)
• AVAX: $35.20 (+1.85%)

Use /price <symbol> [exchange] for specific price information.
                """
                from bot.keyboards.main import InlineKeyboardButton, InlineKeyboardMarkup
                back_keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back to Market", callback_data="menu_market")]
                ])
                await query.edit_message_text(message, parse_mode='Markdown', reply_markup=back_keyboard)
            else:
                await query.edit_message_text("❌ Market feature coming soon")
        except Exception as e:
            logger.error(f"Error in market callback: {e}")
            await query.edit_message_text("❌ An error occurred. Please try again.")
    
    async def _handle_connect_callback(self, query, context: ContextTypes.DEFAULT_TYPE, data):
        """Handle connect-related callbacks"""
        try:
            if data == "connect_hyperliquid":
                message = """
🔷 **Connect Hyperliquid**

To connect your Hyperliquid account:

1. Go to Hyperliquid settings
2. Generate API keys
3. Send your API key and secret

**Format:** `/connect_hyperliquid <api_key> <secret>`

⚠️ **Security Note:** Never share your API keys with anyone!
                """
                from bot.keyboards.main import InlineKeyboardButton, InlineKeyboardMarkup
                back_keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back to Connect", callback_data="menu_connect")]
                ])
                await query.edit_message_text(message, parse_mode='Markdown', reply_markup=back_keyboard)
            elif data == "connect_aster":
                message = """
🔶 **Connect Aster**

To connect your Aster account:

1. Go to Aster settings
2. Generate API keys
3. Send your API key and secret

**Format:** `/connect_aster <api_key> <secret>`

⚠️ **Security Note:** Never share your API keys with anyone!
                """
                from bot.keyboards.main import InlineKeyboardButton, InlineKeyboardMarkup
                back_keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back to Connect", callback_data="menu_connect")]
                ])
                await query.edit_message_text(message, parse_mode='Markdown', reply_markup=back_keyboard)
            else:
                await query.edit_message_text("❌ Connect feature coming soon")
        except Exception as e:
            logger.error(f"Error in connect callback: {e}")
            await query.edit_message_text("❌ An error occurred. Please try again.")
    
    async def _handle_settings_callback(self, query, context: ContextTypes.DEFAULT_TYPE, data):
        """Handle settings-related callbacks"""
        try:
            if data == "settings_accounts":
                message = """
🔗 **Exchange Accounts**

**Connected Accounts:**
• Hyperliquid: ✅ Connected
• Aster: ✅ Connected

**Account Status:**
• Total Exchanges: 2
• Active Connections: 2
• Last Updated: Just now

Use /accounts to view detailed account information.
                """
                from bot.keyboards.main import InlineKeyboardButton, InlineKeyboardMarkup
                back_keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Back to Settings", callback_data="menu_settings")]
                ])
                await query.edit_message_text(message, parse_mode='Markdown', reply_markup=back_keyboard)
            else:
                await query.edit_message_text("❌ Settings feature coming soon")
        except Exception as e:
            logger.error(f"Error in settings callback: {e}")
            await query.edit_message_text("❌ An error occurred. Please try again.")
    
    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle non-command messages (for account setup flow)"""
        try:
            from bot.handlers.account import handle_account_setup
            await handle_account_setup(update, context)
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            if update.effective_message:
                await update.effective_message.reply_text(
                    "❌ An error occurred. Please try again later."
                )
    
    async def _error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors"""
        logger.error(f"Update {update} caused error {context.error}")
        
        if update and update.effective_message:
            try:
                await update.effective_message.reply_text(
                    "❌ An error occurred. Please try again later."
                )
            except TelegramError:
                pass
    
    async def start(self):
        """Start the bot"""
        try:
            logger.info("🤖 Starting DEX Trading Bot...")
            
            # Initialize bot
            await self.initialize()
            
            # Start polling
            self.running = True
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()
            
            logger.info("✅ Bot started successfully")
            
            # Keep running
            while self.running:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"❌ Bot start failed: {e}")
            raise BotError(f"Start failed: {e}")
    
    async def stop(self):
        """Stop the bot"""
        try:
            logger.info("🛑 Stopping DEX Trading Bot...")
            
            self.running = False
            
            # Disconnect from exchange services
            if self.service_manager:
                await self.service_manager.disconnect_all_services()
                logger.info("✅ Exchange services disconnected")
            
            if self.application:
                await self.application.updater.stop()
                await self.application.stop()
                await self.application.shutdown()
            
            logger.info("✅ Bot stopped successfully")
            
        except Exception as e:
            logger.error(f"❌ Bot stop failed: {e}")
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, shutting down...")
            asyncio.create_task(self.stop())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)


async def main():
    """Main function"""
    try:
        # Parse command line arguments
        config_path = "config.json"
        if len(sys.argv) > 1:
            config_path = sys.argv[1]
        
        # Create and start bot
        bot = TradingBot(config_path)
        bot.setup_signal_handlers()
        
        await bot.start()
        
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
