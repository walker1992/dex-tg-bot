"""
Trading Command Handlers
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

from bot.middleware.auth import require_user
from bot.utils.exceptions import BotError, ValidationError

logger = logging.getLogger(__name__)


@require_user
async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /balance command"""
    try:
        user = update.effective_user
        if not user:
            return
        
        # Parse command arguments
        args = context.args
        exchange = args[0].lower() if args else None
        
        if exchange and exchange not in ['hyperliquid', 'aster']:
            await update.message.reply_text(
                "❌ Invalid exchange. Available exchanges: hyperliquid, aster"
            )
            return
        
        # Get service manager from context
        service_manager = context.bot_data.get('service_manager')
        if not service_manager:
            await update.message.reply_text(
                "❌ Service manager not available. Please try again later."
            )
            return
        
        # Show loading message
        loading_msg = await update.message.reply_text("🔄 Fetching balance data...")
        
        try:
            if exchange == 'hyperliquid':
                message = await _get_hyperliquid_balance(service_manager)
            elif exchange == 'aster':
                message = await _get_aster_balance(service_manager)
            else:
                message = await _get_all_balances(service_manager)
            
            await loading_msg.edit_text(message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error fetching balance data: {e}")
            await loading_msg.edit_text(
                "❌ Failed to fetch balance data. Please check your exchange connections."
            )
        
        logger.info(f"Balance command executed by user {user.id} (@{user.username}) for exchange: {exchange or 'all'}")
        
    except Exception as e:
        logger.error(f"Error in balance handler: {e}")
        await update.message.reply_text(
            "❌ An error occurred. Please try again later."
        )


@require_user
async def positions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /positions command"""
    try:
        user = update.effective_user
        if not user:
            return
        
        # Parse command arguments
        args = context.args
        exchange = args[0].lower() if args else None
        
        if exchange and exchange not in ['hyperliquid', 'aster']:
            await update.message.reply_text(
                "❌ Invalid exchange. Available exchanges: hyperliquid, aster"
            )
            return
        
        # TODO: Implement actual positions fetching
        # For now, show mock data
        
        if exchange == 'hyperliquid':
            message = """
📊 **Hyperliquid Positions**

**BTC-PERP:**
• Side: Long
• Size: 0.1 BTC
• Entry Price: $45,000
• Current Price: $50,000
• PnL: +$500.00 (+11.11%)
• Margin: $450.00

**ETH-PERP:**
• Side: Short
• Size: 1.0 ETH
• Entry Price: $3,000
• Current Price: $2,800
• PnL: +$200.00 (+6.67%)
• Margin: $300.00

**Total PnL:** +$700.00
            """
        elif exchange == 'aster':
            message = """
📊 **Aster Positions**

**BTCUSDT:**
• Side: Long
• Size: 0.2 BTC
• Entry Price: $44,000
• Current Price: $50,000
• PnL: +$1,200.00 (+13.64%)
• Margin: $880.00

**ETHUSDT:**
• Side: Long
• Size: 2.0 ETH
• Entry Price: $2,900
• Current Price: $2,800
• PnL: -$200.00 (-3.45%)
• Margin: $580.00

**Total PnL:** +$1,000.00
            """
        else:
            message = """
📊 **All Positions**

**Hyperliquid:**
• BTC-PERP: Long 0.1 BTC (+$500.00)
• ETH-PERP: Short 1.0 ETH (+$200.00)
• Total PnL: +$700.00

**Aster:**
• BTCUSDT: Long 0.2 BTC (+$1,200.00)
• ETHUSDT: Long 2.0 ETH (-$200.00)
• Total PnL: +$1,000.00

**Combined PnL:** +$1,700.00
            """
        
        await update.message.reply_text(message, parse_mode='Markdown')
        
        logger.info(f"Positions command executed by user {user.id} (@{user.username}) for exchange: {exchange or 'all'}")
        
    except Exception as e:
        logger.error(f"Error in positions handler: {e}")
        await update.message.reply_text(
            "❌ An error occurred. Please try again later."
        )


@require_user
async def orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /orders command"""
    try:
        user = update.effective_user
        if not user:
            return
        
        # Parse command arguments
        args = context.args
        exchange = args[0].lower() if args else None
        
        if exchange and exchange not in ['hyperliquid', 'aster']:
            await update.message.reply_text(
                "❌ Invalid exchange. Available exchanges: hyperliquid, aster"
            )
            return
        
        # TODO: Implement actual orders fetching
        # For now, show mock data
        
        message = """
📋 **Open Orders**

**Hyperliquid:**
• BTC-PERP: Buy 0.05 BTC @ $48,000 (Limit)
• ETH-PERP: Sell 0.5 ETH @ $3,200 (Limit)

**Aster:**
• BTCUSDT: Buy 0.1 BTC @ $47,000 (Limit)
• ETHUSDT: Sell 1.0 ETH @ $3,100 (Limit)

**Total Open Orders:** 4
        """
        
        await update.message.reply_text(message, parse_mode='Markdown')
        
        logger.info(f"Orders command executed by user {user.id} (@{user.username}) for exchange: {exchange or 'all'}")
        
    except Exception as e:
        logger.error(f"Error in orders handler: {e}")
        await update.message.reply_text(
            "❌ An error occurred. Please try again later."
        )


@require_user
async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /buy command"""
    try:
        user = update.effective_user
        if not user:
            return
        
        # Parse command arguments
        args = context.args
        if len(args) < 2:
            await update.message.reply_text(
                "❌ Invalid command format.\n"
                "Usage: /buy <symbol> <quantity> [price] [exchange]\n"
                "Example: /buy BTC 0.1 50000 hyperliquid"
            )
            return
        
        symbol = args[0].upper()
        quantity = float(args[1])
        price = float(args[2]) if len(args) > 2 and args[2] != 'market' else None
        exchange = args[3].lower() if len(args) > 3 else 'hyperliquid'
        
        if exchange not in ['hyperliquid', 'aster']:
            await update.message.reply_text(
                "❌ Invalid exchange. Available exchanges: hyperliquid, aster"
            )
            return
        
        # Validate inputs
        if quantity <= 0:
            await update.message.reply_text("❌ Quantity must be positive")
            return
        
        if price is not None and price <= 0:
            await update.message.reply_text("❌ Price must be positive")
            return
        
        # TODO: Implement actual order placement
        # For now, show confirmation
        
        order_type = "Market" if price is None else "Limit"
        price_text = "Market Price" if price is None else f"${price:,.2f}"
        
        message = f"""
✅ **Buy Order Placed**

**Exchange:** {exchange.title()}
**Symbol:** {symbol}
**Side:** Buy
**Type:** {order_type}
**Quantity:** {quantity}
**Price:** {price_text}

**Order ID:** #12345
**Status:** Pending

Use /orders to view all open orders.
        """
        
        await update.message.reply_text(message, parse_mode='Markdown')
        
        logger.info(f"Buy order placed by user {user.id} (@{user.username}): {symbol} {quantity} @ {price_text} on {exchange}")
        
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid number format. Please check your quantity and price values."
        )
    except Exception as e:
        logger.error(f"Error in buy handler: {e}")
        await update.message.reply_text(
            "❌ An error occurred. Please try again later."
        )


@require_user
async def sell(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /sell command"""
    try:
        user = update.effective_user
        if not user:
            return
        
        # Parse command arguments
        args = context.args
        if len(args) < 2:
            await update.message.reply_text(
                "❌ Invalid command format.\n"
                "Usage: /sell <symbol> <quantity> [price] [exchange]\n"
                "Example: /sell BTC 0.1 50000 hyperliquid"
            )
            return
        
        symbol = args[0].upper()
        quantity = float(args[1])
        price = float(args[2]) if len(args) > 2 and args[2] != 'market' else None
        exchange = args[3].lower() if len(args) > 3 else 'hyperliquid'
        
        if exchange not in ['hyperliquid', 'aster']:
            await update.message.reply_text(
                "❌ Invalid exchange. Available exchanges: hyperliquid, aster"
            )
            return
        
        # Validate inputs
        if quantity <= 0:
            await update.message.reply_text("❌ Quantity must be positive")
            return
        
        if price is not None and price <= 0:
            await update.message.reply_text("❌ Price must be positive")
            return
        
        # TODO: Implement actual order placement
        # For now, show confirmation
        
        order_type = "Market" if price is None else "Limit"
        price_text = "Market Price" if price is None else f"${price:,.2f}"
        
        message = f"""
✅ **Sell Order Placed**

**Exchange:** {exchange.title()}
**Symbol:** {symbol}
**Side:** Sell
**Type:** {order_type}
**Quantity:** {quantity}
**Price:** {price_text}

**Order ID:** #12346
**Status:** Pending

Use /orders to view all open orders.
        """
        
        await update.message.reply_text(message, parse_mode='Markdown')
        
        logger.info(f"Sell order placed by user {user.id} (@{user.username}): {symbol} {quantity} @ {price_text} on {exchange}")
        
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid number format. Please check your quantity and price values."
        )
    except Exception as e:
        logger.error(f"Error in sell handler: {e}")
        await update.message.reply_text(
            "❌ An error occurred. Please try again later."
        )


@require_user
async def close(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /close command"""
    try:
        user = update.effective_user
        if not user:
            return
        
        # Parse command arguments
        args = context.args
        if len(args) < 1:
            await update.message.reply_text(
                "❌ Invalid command format.\n"
                "Usage: /close <symbol> [exchange]\n"
                "Example: /close BTC hyperliquid"
            )
            return
        
        symbol = args[0].upper()
        exchange = args[1].lower() if len(args) > 1 else 'hyperliquid'
        
        if exchange not in ['hyperliquid', 'aster']:
            await update.message.reply_text(
                "❌ Invalid exchange. Available exchanges: hyperliquid, aster"
            )
            return
        
        # TODO: Implement actual position closing
        # For now, show confirmation
        
        message = f"""
✅ **Position Closed**

**Exchange:** {exchange.title()}
**Symbol:** {symbol}
**Action:** Close Position
**Quantity:** 0.1 {symbol}
**Price:** Market Price

**Order ID:** #12347
**Status:** Filled

Use /positions to view remaining positions.
        """
        
        await update.message.reply_text(message, parse_mode='Markdown')
        
        logger.info(f"Position closed by user {user.id} (@{user.username}): {symbol} on {exchange}")
        
    except Exception as e:
        logger.error(f"Error in close handler: {e}")
        await update.message.reply_text(
            "❌ An error occurred. Please try again later."
        )


@require_user
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /cancel command"""
    try:
        user = update.effective_user
        if not user:
            return
        
        # Parse command arguments
        args = context.args
        if len(args) < 1:
            await update.message.reply_text(
                "❌ Invalid command format.\n"
                "Usage: /cancel <order_id>\n"
                "Example: /cancel 12345"
            )
            return
        
        order_id = args[0]
        
        # TODO: Implement actual order cancellation
        # For now, show confirmation
        
        message = f"""
✅ **Order Cancelled**

**Order ID:** #{order_id}
**Status:** Cancelled

Use /orders to view remaining open orders.
        """
        
        await update.message.reply_text(message, parse_mode='Markdown')
        
        logger.info(f"Order cancelled by user {user.id} (@{user.username}): {order_id}")
        
    except Exception as e:
        logger.error(f"Error in cancel handler: {e}")
        await update.message.reply_text(
            "❌ An error occurred. Please try again later."
        )


@require_user
async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /price command"""
    try:
        user = update.effective_user
        if not user:
            return
        
        # Parse command arguments
        args = context.args
        if len(args) < 1:
            await update.message.reply_text(
                "❌ Invalid command format.\n"
                "Usage: /price <symbol> [exchange]\n"
                "Example: /price BTC hyperliquid"
            )
            return
        
        symbol = args[0].upper()
        exchange = args[1].lower() if len(args) > 1 else 'hyperliquid'
        
        if exchange not in ['hyperliquid', 'aster']:
            await update.message.reply_text(
                "❌ Invalid exchange. Available exchanges: hyperliquid, aster"
            )
            return
        
        # TODO: Implement actual price fetching
        # For now, show mock data
        
        if exchange == 'hyperliquid':
            message = f"""
📈 **{symbol} Price - Hyperliquid**

**Current Price:** $50,000.00
**24h Change:** +$2,500.00 (+5.26%)
**24h High:** $51,200.00
**24h Low:** $47,800.00
**24h Volume:** 1,250.5 {symbol}

**Bid:** $49,995.00
**Ask:** $50,005.00
**Spread:** $10.00 (0.02%)
            """
        else:  # aster
            message = f"""
📈 **{symbol} Price - Aster**

**Current Price:** $50,100.00
**24h Change:** +$2,600.00 (+5.48%)
**24h High:** $51,300.00
**24h Low:** $47,900.00
**24h Volume:** 2,100.8 {symbol}

**Bid:** $50,095.00
**Ask:** $50,105.00
**Spread:** $10.00 (0.02%)
            """
        
        await update.message.reply_text(message, parse_mode='Markdown')
        
        logger.info(f"Price command executed by user {user.id} (@{user.username}): {symbol} on {exchange}")
        
    except Exception as e:
        logger.error(f"Error in price handler: {e}")
        await update.message.reply_text(
            "❌ An error occurred. Please try again later."
        )


@require_user
async def depth(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /depth command"""
    try:
        user = update.effective_user
        if not user:
            return
        
        # Parse command arguments
        args = context.args
        if len(args) < 1:
            await update.message.reply_text(
                "❌ Invalid command format.\n"
                "Usage: /depth <symbol> [exchange]\n"
                "Example: /depth BTC hyperliquid"
            )
            return
        
        symbol = args[0].upper()
        exchange = args[1].lower() if len(args) > 1 else 'hyperliquid'
        
        if exchange not in ['hyperliquid', 'aster']:
            await update.message.reply_text(
                "❌ Invalid exchange. Available exchanges: hyperliquid, aster"
            )
            return
        
        # TODO: Implement actual order book fetching
        # For now, show mock data
        
        message = f"""
📊 **{symbol} Order Book - {exchange.title()}**

**Bids (Buy Orders):**
$50,000.00 | 0.5 {symbol}
$49,995.00 | 1.2 {symbol}
$49,990.00 | 0.8 {symbol}
$49,985.00 | 2.1 {symbol}
$49,980.00 | 1.5 {symbol}

**Asks (Sell Orders):**
$50,005.00 | 0.7 {symbol}
$50,010.00 | 1.3 {symbol}
$50,015.00 | 0.9 {symbol}
$50,020.00 | 1.8 {symbol}
$50,025.00 | 2.2 {symbol}

**Best Bid:** $50,000.00
**Best Ask:** $50,005.00
**Spread:** $5.00 (0.01%)
        """
        
        await update.message.reply_text(message, parse_mode='Markdown')
        
        logger.info(f"Depth command executed by user {user.id} (@{user.username}): {symbol} on {exchange}")
        
    except Exception as e:
        logger.error(f"Error in depth handler: {e}")
        await update.message.reply_text(
            "❌ An error occurred. Please try again later."
        )


@require_user
async def funding(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /funding command"""
    try:
        user = update.effective_user
        if not user:
            return
        
        # Parse command arguments
        args = context.args
        if len(args) < 1:
            await update.message.reply_text(
                "❌ Invalid command format.\n"
                "Usage: /funding <symbol> [exchange]\n"
                "Example: /funding BTC hyperliquid"
            )
            return
        
        symbol = args[0].upper()
        exchange = args[1].lower() if len(args) > 1 else 'hyperliquid'
        
        if exchange not in ['hyperliquid', 'aster']:
            await update.message.reply_text(
                "❌ Invalid exchange. Available exchanges: hyperliquid, aster"
            )
            return
        
        # TODO: Implement actual funding rate fetching
        # For now, show mock data
        
        message = f"""
💰 **{symbol} Funding Rate - {exchange.title()}**

**Current Funding Rate:** 0.0001 (0.01%)
**Next Funding Time:** 2h 15m
**Funding Rate History:**
• 8h ago: 0.0002 (0.02%)
• 16h ago: -0.0001 (-0.01%)
• 24h ago: 0.0003 (0.03%)

**Average 24h:** 0.0001 (0.01%)
**Max 24h:** 0.0003 (0.03%)
**Min 24h:** -0.0001 (-0.01%)

**Funding Rate Impact:**
• Long positions pay: 0.0001
• Short positions receive: 0.0001
        """
        
        await update.message.reply_text(message, parse_mode='Markdown')
        
        logger.info(f"Funding command executed by user {user.id} (@{user.username}): {symbol} on {exchange}")
        
    except Exception as e:
        logger.error(f"Error in funding handler: {e}")
        await update.message.reply_text(
            "❌ An error occurred. Please try again later."
        )


@require_user
async def stats_24h(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /24h command"""
    try:
        user = update.effective_user
        if not user:
            return
        
        # Parse command arguments
        args = context.args
        if len(args) < 1:
            await update.message.reply_text(
                "❌ Invalid command format.\n"
                "Usage: /24h <symbol> [exchange]\n"
                "Example: /24h BTC hyperliquid"
            )
            return
        
        symbol = args[0].upper()
        exchange = args[1].lower() if len(args) > 1 else 'hyperliquid'
        
        if exchange not in ['hyperliquid', 'aster']:
            await update.message.reply_text(
                "❌ Invalid exchange. Available exchanges: hyperliquid, aster"
            )
            return
        
        # TODO: Implement actual 24h stats fetching
        # For now, show mock data
        
        message = f"""
📊 **{symbol} 24h Statistics - {exchange.title()}**

**Price Change:**
• Open: $47,500.00
• Close: $50,000.00
• Change: +$2,500.00 (+5.26%)

**High & Low:**
• 24h High: $51,200.00
• 24h Low: $47,800.00
• Range: $3,400.00 (7.11%)

**Volume:**
• 24h Volume: 1,250.5 {symbol}
• Volume (USD): $62,525,000
• Avg Price: $49,999.00

**Trades:**
• Total Trades: 15,420
• Buy Trades: 8,250 (53.5%)
• Sell Trades: 7,170 (46.5%)

**Market Cap:** $980,000,000,000
        """
        
        await update.message.reply_text(message, parse_mode='Markdown')
        
        logger.info(f"24h stats command executed by user {user.id} (@{user.username}): {symbol} on {exchange}")
        
    except Exception as e:
        logger.error(f"Error in 24h stats handler: {e}")
        await update.message.reply_text(
            "❌ An error occurred. Please try again later."
        )


# Helper functions for balance fetching
async def _get_hyperliquid_balance(service_manager) -> str:
    """Get Hyperliquid balance data"""
    try:
        # Get spot and futures services
        spot_service = service_manager.get_spot_service("hyperliquid")
        futures_service = service_manager.get_futures_service("hyperliquid")
        
        spot_balances = []
        futures_balances = []
        total_usd_value = 0
        
        # Get spot balances
        if spot_service and service_manager.is_service_connected("hyperliquid", "spot"):
            try:
                spot_balances = await spot_service.get_balances()
            except Exception as e:
                logger.warning(f"Failed to get Hyperliquid spot balances: {e}")
                # Try to reconnect if connection lost
                try:
                    await spot_service.connect()
                    if spot_service.is_connected:
                        spot_balances = await spot_service.get_balances()
                except Exception as reconnect_e:
                    logger.error(f"Failed to reconnect Hyperliquid spot service: {reconnect_e}")
        
        # Get futures balances
        if futures_service and service_manager.is_service_connected("hyperliquid", "futures"):
            try:
                futures_balances = await futures_service.get_balances()
            except Exception as e:
                logger.warning(f"Failed to get Hyperliquid futures balances: {e}")
                # Try to reconnect if connection lost
                try:
                    await futures_service.connect()
                    if futures_service.is_connected:
                        futures_balances = await futures_service.get_balances()
                except Exception as reconnect_e:
                    logger.error(f"Failed to reconnect Hyperliquid futures service: {reconnect_e}")
        
        if not spot_balances and not futures_balances:
            return "💰 **Hyperliquid Balance**\n\n❌ No balance data available. Please check your connection."
        
        # Format spot balances
        spot_lines = []
        spot_total = 0
        for balance in spot_balances:
            if balance.total > 0:
                price = await _get_asset_price_usd(balance.asset, service_manager)
                if price is not None:
                    usd_value = float(balance.total) * price
                    spot_total += usd_value
                    spot_lines.append(f"• **{balance.asset}:** {balance.total:,.4f} (${usd_value:,.2f})")
                else:
                    spot_lines.append(f"• **{balance.asset}:** {balance.total:,.4f} (无法获取price)")
        
        # Format futures balances
        futures_lines = []
        futures_total = 0
        for balance in futures_balances:
            if balance.total > 0:
                price = await _get_asset_price_usd(balance.asset, service_manager)
                if price is not None:
                    usd_value = float(balance.total) * price
                    futures_total += usd_value
                    futures_lines.append(f"• **{balance.asset}:** {balance.total:,.4f} (${usd_value:,.2f})")
                else:
                    futures_lines.append(f"• **{balance.asset}:** {balance.total:,.4f} (无法获取price)")
        
        total_usd_value = spot_total + futures_total
        
        # Build message
        message = "💰 **Hyperliquid Balance**\n\n"
        
        if spot_lines:
            message += "**Spot:**\n"
            message += "\n".join(spot_lines)
            message += f"\n• Total: ${spot_total:,.2f}\n\n"
        
        if futures_lines:
            message += "**Perpetual:**\n"
            message += "\n".join(futures_lines)
            message += f"\n• Total: ${futures_total:,.2f}\n\n"
        
        message += f"**Total Portfolio Value:** ${total_usd_value:,.2f}"
        
        return message
        
    except Exception as e:
        logger.error(f"Error getting Hyperliquid balance: {e}")
        return "💰 **Hyperliquid Balance**\n\n❌ Failed to fetch balance data."


async def _get_aster_balance(service_manager) -> str:
    """Get Aster balance data"""
    try:
        # Get spot and futures services
        spot_service = service_manager.get_spot_service("aster")
        futures_service = service_manager.get_futures_service("aster")
        
        spot_balances = []
        futures_balances = []
        total_usd_value = 0
        
        # Get spot balances
        if spot_service and service_manager.is_service_connected("aster", "spot"):
            try:
                spot_balances = await spot_service.get_balances()
            except Exception as e:
                logger.warning(f"Failed to get Aster spot balances: {e}")
                # Try to reconnect if connection lost
                try:
                    await spot_service.connect()
                    if spot_service.is_connected:
                        spot_balances = await spot_service.get_balances()
                except Exception as reconnect_e:
                    logger.error(f"Failed to reconnect Aster spot service: {reconnect_e}")
        
        # Get futures balances
        if futures_service and service_manager.is_service_connected("aster", "futures"):
            try:
                futures_balances = await futures_service.get_balances()
            except Exception as e:
                logger.warning(f"Failed to get Aster futures balances: {e}")
                # Try to reconnect if connection lost
                try:
                    await futures_service.connect()
                    if futures_service.is_connected:
                        futures_balances = await futures_service.get_balances()
                except Exception as reconnect_e:
                    logger.error(f"Failed to reconnect Aster futures service: {reconnect_e}")
        
        if not spot_balances and not futures_balances:
            return "💰 **Aster Balance**\n\n❌ No balance data available. Please check your connection."
        
        # Format spot balances
        spot_lines = []
        spot_total = 0
        for balance in spot_balances:
            if balance.total > 0:
                price = await _get_asset_price_usd(balance.asset, service_manager)
                if price is not None:
                    usd_value = float(balance.total) * price
                    spot_total += usd_value
                    spot_lines.append(f"• **{balance.asset}:** {balance.total:,.4f} (${usd_value:,.2f})")
                else:
                    spot_lines.append(f"• **{balance.asset}:** {balance.total:,.4f} (无法获取price)")
        
        # Format futures balances
        futures_lines = []
        futures_total = 0
        for balance in futures_balances:
            if balance.total > 0:
                price = await _get_asset_price_usd(balance.asset, service_manager)
                if price is not None:
                    usd_value = float(balance.total) * price
                    futures_total += usd_value
                    futures_lines.append(f"• **{balance.asset}:** {balance.total:,.4f} (${usd_value:,.2f})")
                else:
                    futures_lines.append(f"• **{balance.asset}:** {balance.total:,.4f} (无法获取price)")
        
        total_usd_value = spot_total + futures_total
        
        # Build message
        message = "💰 **Aster Balance**\n\n"
        
        if spot_lines:
            message += "**Spot:**\n"
            message += "\n".join(spot_lines)
            message += f"\n• Total: ${spot_total:,.2f}\n\n"
        
        if futures_lines:
            message += "**Perpetual:**\n"
            message += "\n".join(futures_lines)
            message += f"\n• Total: ${futures_total:,.2f}\n\n"
        
        message += f"**Total Portfolio Value:** ${total_usd_value:,.2f}"
        
        return message
        
    except Exception as e:
        logger.error(f"Error getting Aster balance: {e}")
        return "💰 **Aster Balance**\n\n❌ Failed to fetch balance data."


async def _get_all_balances(service_manager) -> str:
    """Get all exchange balances"""
    try:
        hyperliquid_balance = await _get_hyperliquid_balance(service_manager)
        aster_balance = await _get_aster_balance(service_manager)
        
        # Extract totals from balance messages (simplified parsing)
        hyperliquid_total = _extract_total_from_balance_message(hyperliquid_balance)
        aster_total = _extract_total_from_balance_message(aster_balance)
        combined_total = hyperliquid_total + aster_total
        
        # Extract spot and perpetual sections from each exchange
        hyperliquid_spot = _extract_section_from_message(hyperliquid_balance, "Spot")
        hyperliquid_perp = _extract_section_from_message(hyperliquid_balance, "Perpetual")
        aster_spot = _extract_section_from_message(aster_balance, "Spot")
        aster_perp = _extract_section_from_message(aster_balance, "Perpetual")
        
        message = "💰 **All Exchange Balances**\n\n"
        
        # Hyperliquid section
        message += "**Hyperliquid:**\n"
        if hyperliquid_spot:
            message += f"**Spot:**\n{hyperliquid_spot}\n"
        if hyperliquid_perp:
            message += f"**Perpetual:**\n{hyperliquid_perp}\n"
        message += f"• Total: ${hyperliquid_total:,.2f}\n\n"
        
        # Aster section
        message += "**Aster:**\n"
        if aster_spot:
            message += f"**Spot:**\n{aster_spot}\n"
        if aster_perp:
            message += f"**Perpetual:**\n{aster_perp}\n"
        message += f"• Total: ${aster_total:,.2f}\n\n"
        
        message += f"**Combined Total:** ${combined_total:,.2f}"
        
        return message
        
    except Exception as e:
        logger.error(f"Error getting all balances: {e}")
        return "💰 **All Exchange Balances**\n\n❌ Failed to fetch balance data."


async def _get_asset_price_usd(asset: str, service_manager=None) -> float:
    """Get USD price for an asset from exchange APIs"""
    # Stablecoins are always $1
    if asset.upper() in ['USDC', 'USDT', 'USDD', 'BUSD', 'DAI']:
        return 1.0
    
    # Try to get price from exchanges (with reduced logging)
    if service_manager:
        try:
            # Try Hyperliquid first
            hyperliquid_spot = service_manager.get_spot_service("hyperliquid")
            if hyperliquid_spot and service_manager.is_service_connected("hyperliquid", "spot"):
                try:
                    # For Hyperliquid, try different symbol formats
                    # Based on list_markets.py output, prioritize existing formats
                    symbols_to_try = [
                        f"{asset}/USDC",  # Most common spot pair format
                        f"{asset}/USDH",  # Alternative quote asset (USDH)
                        f"{asset}/USDT0", # USDT with "0" suffix
                        asset,            # Perpetual format (if exists)
                        f"{asset}USDC",   # Legacy concatenated format
                        f"{asset}USDT"    # Legacy concatenated format
                    ]
                    for symbol in symbols_to_try:
                        try:
                            ticker = await hyperliquid_spot.get_ticker(symbol)
                            if ticker and hasattr(ticker, 'last_price') and ticker.last_price > 0:
                                return float(ticker.last_price)
                        except Exception:
                            # Silently continue to next symbol
                            continue
                except Exception:
                    pass
            
            # Try Aster as fallback
            aster_spot = service_manager.get_spot_service("aster")
            if aster_spot and service_manager.is_service_connected("aster", "spot"):
                try:
                    # For Aster, try different symbol formats
                    symbols_to_try = [f"{asset}USDT", f"{asset}USDC", asset]
                    for symbol in symbols_to_try:
                        try:
                            ticker = await aster_spot.get_ticker(symbol)
                            if ticker and hasattr(ticker, 'last_price') and ticker.last_price > 0:
                                return float(ticker.last_price)
                        except Exception:
                            # Silently continue to next symbol
                            continue
                except Exception:
                    pass
        except Exception as e:
            # Only log if it's a serious error, not just missing symbol
            if "Invalid symbol" not in str(e) and "Failed to get ticker" not in str(e):
                logger.warning(f"Failed to get price for {asset} from exchanges: {e}")
    
    # No static price fallback - return None if price cannot be obtained
    logger.warning(f"Unable to get price for asset: {asset}")
    return None


def _extract_total_from_balance_message(message: str) -> float:
    """Extract total USD value from balance message"""
    try:
        lines = message.split('\n')
        for line in lines:
            if 'Total Portfolio Value:' in line:
                # Extract number from line like "**Total Portfolio Value:** $5,250.00"
                import re
                match = re.search(r'\$([0-9,]+\.?[0-9]*)', line)
                if match:
                    return float(match.group(1).replace(',', ''))
        return 0.0
    except Exception:
        return 0.0


def _extract_balance_lines_from_message(message: str) -> str:
    """Extract balance lines from balance message"""
    try:
        lines = message.split('\n')
        balance_lines = []
        for line in lines:
            if line.strip().startswith('• **') and ':**' in line:
                balance_lines.append(line.strip())
        return '\n'.join(balance_lines) if balance_lines else "• No balances available"
    except Exception:
        return "• No balances available"


def _extract_section_from_message(message: str, section_name: str) -> str:
    """Extract a specific section (Spot/Perpetual) from balance message"""
    try:
        lines = message.split('\n')
        section_lines = []
        in_section = False
        
        for line in lines:
            line = line.strip()
            if f"**{section_name}:**" in line:
                in_section = True
                continue
            elif in_section:
                if line.startswith('• **') and ':**' in line:
                    section_lines.append(line)
                elif line.startswith('• Total:') or line.startswith('**Total'):
                    break
                elif line.startswith('**') and ':**' in line and section_name not in line:
                    # Start of another section
                    break
        
        return '\n'.join(section_lines) if section_lines else ""
    except Exception:
        return ""


async def _get_all_positions(service_manager) -> str:
    """Get all exchange positions"""
    try:
        # Get position data and totals directly
        hyperliquid_data = await _get_hyperliquid_positions_with_total(service_manager)
        aster_data = await _get_aster_positions_with_total(service_manager)
        
        hyperliquid_positions, hyperliquid_total = hyperliquid_data
        aster_positions, aster_total = aster_data
        combined_total = hyperliquid_total + aster_total
        
        message = "📊 **Current Positions**\n\n"
        
        # Hyperliquid section
        message += "**Hyperliquid:**\n"
        if hyperliquid_positions:
            message += hyperliquid_positions + "\n"
        else:
            message += "• No positions\n"
        message += f"• Total PnL: ${hyperliquid_total:,.2f}\n\n"
        
        # Aster section
        message += "**Aster:**\n"
        if aster_positions:
            message += aster_positions + "\n"
        else:
            message += "• No positions\n"
        message += f"• Total PnL: ${aster_total:,.2f}\n\n"
        
        message += f"**Combined PnL:** ${combined_total:,.2f}\n\n"
        message += "Use /positions [exchange] for detailed position information."
        
        return message
        
    except Exception as e:
        logger.error(f"Error getting all positions: {e}")
        return "📊 **Current Positions**\n\n❌ Failed to fetch position data."


async def _get_hyperliquid_positions_with_total(service_manager) -> tuple[str, float]:
    """Get Hyperliquid positions with total PnL"""
    try:
        futures_service = service_manager.get_futures_service("hyperliquid")
        if not futures_service or not service_manager.is_service_connected("hyperliquid", "futures"):
            return "❌ Hyperliquid futures service not connected", 0.0
        
        positions = await futures_service.get_futures_positions()
        
        if not positions:
            return "No positions", 0.0
        
        message = ""
        total_pnl = 0.0
        
        for position in positions:
            if position.size > 0:  # Only show non-zero positions
                side_emoji = "🟢" if position.side.lower() == "long" else "🔴"
                pnl_emoji = "📈" if position.pnl >= 0 else "📉"
                
                # Format PnL with proper sign
                pnl_str = f"+${position.pnl:,.2f}" if position.pnl >= 0 else f"-${abs(position.pnl):,.2f}"
                
                message += f"• {side_emoji} {position.symbol}: {position.side.title()} {position.size} {position.leverage}x "
                message += f"({pnl_emoji}{pnl_str})\n"
                total_pnl += float(position.pnl)
        
        if not message:
            return "No positions", 0.0
        
        return message, total_pnl
        
    except Exception as e:
        logger.error(f"Error getting Hyperliquid positions: {e}")
        return "❌ Failed to fetch Hyperliquid positions", 0.0


async def _get_hyperliquid_positions(service_manager) -> str:
    """Get Hyperliquid positions (legacy function)"""
    message, _ = await _get_hyperliquid_positions_with_total(service_manager)
    return message


async def _get_aster_positions(service_manager) -> str:
    """Get Aster positions"""
    try:
        futures_service = service_manager.get_futures_service("aster")
        if not futures_service or not service_manager.is_service_connected("aster", "futures"):
            return "❌ Aster futures service not connected"
        
        positions = await futures_service.get_futures_positions()
        
        if not positions:
            return "No positions"
        
        message = ""
        total_pnl = 0.0
        
        for position in positions:
            if position.size > 0:  # Only show non-zero positions
                side_emoji = "🟢" if position.side.lower() == "long" else "🔴"
                pnl_emoji = "📈" if position.pnl >= 0 else "📉"
                
                # Debug logging
                # logger.info(f"Aster position debug - Symbol: {position.symbol}, PnL: {position.pnl}, "
                #            f"Entry: {position.entry_price}, Mark: {position.mark_price}, "
                #            f"Size: {position.size}, Side: {position.side}, Leverage: {position.leverage}")
                
                # Additional debug for PnL calculation
                if position.pnl == 0:
                    logger.warning(f"PnL is 0 for {position.symbol} - Entry: {position.entry_price}, Mark: {position.mark_price}, Size: {position.size}")
                
                # Format PnL with proper sign
                pnl_str = f"+${position.pnl:,.2f}" if position.pnl >= 0 else f"-${abs(position.pnl):,.2f}"
                
                message += f"• {side_emoji} {position.symbol}: {position.side.title()} {position.size} {position.leverage}x "
                message += f"({pnl_emoji}{pnl_str})\n"
                total_pnl += float(position.pnl)
        
        if not message:
            return "No positions"
        
        return message
        
    except Exception as e:
        logger.error(f"Error getting Aster positions: {e}")
        return "❌ Failed to fetch Aster positions"


async def _get_aster_positions_with_total(service_manager) -> tuple[str, float]:
    """Get Aster positions with total PnL"""
    try:
        futures_service = service_manager.get_futures_service("aster")
        if not futures_service or not service_manager.is_service_connected("aster", "futures"):
            return "❌ Aster futures service not connected", 0.0
        
        positions = await futures_service.get_futures_positions()
        
        if not positions:
            return "No positions", 0.0
        
        message = ""
        total_pnl = 0.0
        
        for position in positions:
            if position.size > 0:  # Only show non-zero positions
                side_emoji = "🟢" if position.side.lower() == "long" else "🔴"
                pnl_emoji = "📈" if position.pnl >= 0 else "📉"
                
                # Format PnL with proper sign
                pnl_str = f"+${position.pnl:,.2f}" if position.pnl >= 0 else f"-${abs(position.pnl):,.2f}"
                
                message += f"• {side_emoji} {position.symbol}: {position.side.title()} {position.size} {position.leverage}x "
                message += f"({pnl_emoji}{pnl_str})\n"
                total_pnl += float(position.pnl)
        
        if not message:
            return "No positions", 0.0
        
        return message, total_pnl
        
    except Exception as e:
        logger.error(f"Error getting Aster positions: {e}")
        return "❌ Failed to fetch Aster positions", 0.0


def _extract_total_from_positions_message(message: str) -> float:
    """Extract total PnL from positions message"""
    try:
        lines = message.split('\n')
        for line in lines:
            if 'Total PnL:' in line:
                # Extract number from line like "• Total PnL: $1,700.00"
                import re
                match = re.search(r'\$([0-9,]+\.?[0-9]*)', line)
                if match:
                    return float(match.group(1).replace(',', ''))
        return 0.0
    except Exception:
        return 0.0


def _extract_position_lines_from_message(message: str) -> str:
    """Extract position lines from positions message"""
    try:
        lines = message.split('\n')
        position_lines = []
        for line in lines:
            if line.strip().startswith('• ') and ('🟢' in line or '🔴' in line):
                position_lines.append(line.strip())
        return '\n'.join(position_lines) if position_lines else "• No positions"
    except Exception:
        return "• No positions"
