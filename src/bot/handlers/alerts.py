"""
Alert Command Handlers
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

from bot.middleware.auth import require_user
from bot.utils.exceptions import BotError, ValidationError

logger = logging.getLogger(__name__)


@require_user
async def alert_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /alert_price command"""
    try:
        user = update.effective_user
        if not user:
            return
        
        # Parse command arguments
        args = context.args
        if len(args) < 3:
            await update.message.reply_text(
                "❌ Invalid command format.\n"
                "Usage: /alert_price <symbol> <condition> <value> [exchange]\n"
                "Conditions: above, below, equals\n"
                "Example: /alert_price BTC above 60000 hyperliquid"
            )
            return
        
        symbol = args[0].upper()
        condition = args[1].lower()
        value = float(args[2])
        exchange = args[3].lower() if len(args) > 3 else 'hyperliquid'
        
        if condition not in ['above', 'below', 'equals']:
            await update.message.reply_text(
                "❌ Invalid condition. Available conditions: above, below, equals"
            )
            return
        
        if exchange not in ['hyperliquid', 'aster']:
            await update.message.reply_text(
                "❌ Invalid exchange. Available exchanges: hyperliquid, aster"
            )
            return
        
        if value <= 0:
            await update.message.reply_text("❌ Price value must be positive")
            return
        
        # TODO: Implement actual alert creation
        # For now, show confirmation
        
        alert_id = f"price_{symbol}_{condition}_{value}_{exchange}"
        
        message = f"""
🔔 **Price Alert Created**

**Alert ID:** {alert_id}
**Symbol:** {symbol}
**Condition:** {condition.title()}
**Value:** ${value:,.2f}
**Exchange:** {exchange.title()}
**Status:** Active

You will be notified when {symbol} price goes {condition} ${value:,.2f} on {exchange}.

Use /alerts to view all your alerts.
        """
        
        await update.message.reply_text(message, parse_mode='Markdown')
        
        logger.info(f"Price alert created by user {user.id} (@{user.username}): {symbol} {condition} ${value} on {exchange}")
        
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid number format. Please check your price value."
        )
    except Exception as e:
        logger.error(f"Error in alert_price handler: {e}")
        await update.message.reply_text(
            "❌ An error occurred. Please try again later."
        )


@require_user
async def alert_funding(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /alert_funding command"""
    try:
        user = update.effective_user
        if not user:
            return
        
        # Parse command arguments
        args = context.args
        if len(args) < 2:
            await update.message.reply_text(
                "❌ Invalid command format.\n"
                "Usage: /alert_funding <symbol> <value> [exchange]\n"
                "Example: /alert_funding BTC 0.001 hyperliquid"
            )
            return
        
        symbol = args[0].upper()
        value = float(args[2])
        exchange = args[3].lower() if len(args) > 3 else 'hyperliquid'
        
        if exchange not in ['hyperliquid', 'aster']:
            await update.message.reply_text(
                "❌ Invalid exchange. Available exchanges: hyperliquid, aster"
            )
            return
        
        # TODO: Implement actual alert creation
        # For now, show confirmation
        
        alert_id = f"funding_{symbol}_{value}_{exchange}"
        
        message = f"""
🔔 **Funding Rate Alert Created**

**Alert ID:** {alert_id}
**Symbol:** {symbol}
**Funding Rate Threshold:** {value:.4f} ({value*100:.2f}%)
**Exchange:** {exchange.title()}
**Status:** Active

You will be notified when {symbol} funding rate exceeds {value:.4f} ({value*100:.2f}%) on {exchange}.

Use /alerts to view all your alerts.
        """
        
        await update.message.reply_text(message, parse_mode='Markdown')
        
        logger.info(f"Funding alert created by user {user.id} (@{user.username}): {symbol} {value} on {exchange}")
        
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid number format. Please check your funding rate value."
        )
    except Exception as e:
        logger.error(f"Error in alert_funding handler: {e}")
        await update.message.reply_text(
            "❌ An error occurred. Please try again later."
        )


@require_user
async def alert_position(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /alert_position command"""
    try:
        user = update.effective_user
        if not user:
            return
        
        # Parse command arguments
        args = context.args
        if len(args) < 3:
            await update.message.reply_text(
                "❌ Invalid command format.\n"
                "Usage: /alert_position <symbol> <condition> <value> [exchange]\n"
                "Conditions: pnl_above, pnl_below, margin_above, margin_below\n"
                "Example: /alert_position BTC pnl_above 1000 hyperliquid"
            )
            return
        
        symbol = args[0].upper()
        condition = args[1].lower()
        value = float(args[2])
        exchange = args[3].lower() if len(args) > 3 else 'hyperliquid'
        
        valid_conditions = ['pnl_above', 'pnl_below', 'margin_above', 'margin_below']
        if condition not in valid_conditions:
            await update.message.reply_text(
                f"❌ Invalid condition. Available conditions: {', '.join(valid_conditions)}"
            )
            return
        
        if exchange not in ['hyperliquid', 'aster']:
            await update.message.reply_text(
                "❌ Invalid exchange. Available exchanges: hyperliquid, aster"
            )
            return
        
        # TODO: Implement actual alert creation
        # For now, show confirmation
        
        alert_id = f"position_{symbol}_{condition}_{value}_{exchange}"
        
        condition_text = {
            'pnl_above': f"PnL above ${value:,.2f}",
            'pnl_below': f"PnL below ${value:,.2f}",
            'margin_above': f"Margin ratio above {value:.2%}",
            'margin_below': f"Margin ratio below {value:.2%}"
        }
        
        message = f"""
🔔 **Position Alert Created**

**Alert ID:** {alert_id}
**Symbol:** {symbol}
**Condition:** {condition_text[condition]}
**Exchange:** {exchange.title()}
**Status:** Active

You will be notified when your {symbol} position on {exchange} meets the condition: {condition_text[condition]}.

Use /alerts to view all your alerts.
        """
        
        await update.message.reply_text(message, parse_mode='Markdown')
        
        logger.info(f"Position alert created by user {user.id} (@{user.username}): {symbol} {condition} {value} on {exchange}")
        
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid number format. Please check your value."
        )
    except Exception as e:
        logger.error(f"Error in alert_position handler: {e}")
        await update.message.reply_text(
            "❌ An error occurred. Please try again later."
        )


@require_user
async def alerts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /alerts command"""
    try:
        user = update.effective_user
        if not user:
            return
        
        # TODO: Implement actual alerts fetching
        # For now, show mock data
        
        message = """
🔔 **Your Alerts**

**Active Alerts (3):**

1. **Price Alert**
   • ID: price_BTC_above_60000_hyperliquid
   • Symbol: BTC
   • Condition: Above $60,000
   • Exchange: Hyperliquid
   • Status: Active

2. **Funding Alert**
   • ID: funding_ETH_0.001_aster
   • Symbol: ETH
   • Threshold: 0.001 (0.10%)
   • Exchange: Aster
   • Status: Active

3. **Position Alert**
   • ID: position_BTC_pnl_above_1000_hyperliquid
   • Symbol: BTC
   • Condition: PnL above $1,000
   • Exchange: Hyperliquid
   • Status: Active

**Commands:**
• Delete alert: /delete_alert <alert_id>
• Create price alert: /alert_price <symbol> <condition> <value>
• Create funding alert: /alert_funding <symbol> <value>
• Create position alert: /alert_position <symbol> <condition> <value>
        """
        
        await update.message.reply_text(message, parse_mode='Markdown')
        
        logger.info(f"Alerts command executed by user {user.id} (@{user.username})")
        
    except Exception as e:
        logger.error(f"Error in alerts handler: {e}")
        await update.message.reply_text(
            "❌ An error occurred. Please try again later."
        )


@require_user
async def delete_alert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /delete_alert command"""
    try:
        user = update.effective_user
        if not user:
            return
        
        # Parse command arguments
        args = context.args
        if len(args) < 1:
            await update.message.reply_text(
                "❌ Invalid command format.\n"
                "Usage: /delete_alert <alert_id>\n"
                "Example: /delete_alert price_BTC_above_60000_hyperliquid"
            )
            return
        
        alert_id = args[0]
        
        # TODO: Implement actual alert deletion
        # For now, show confirmation
        
        message = f"""
✅ **Alert Deleted**

**Alert ID:** {alert_id}
**Status:** Deleted

The alert has been successfully removed.

Use /alerts to view your remaining alerts.
        """
        
        await update.message.reply_text(message, parse_mode='Markdown')
        
        logger.info(f"Alert deleted by user {user.id} (@{user.username}): {alert_id}")
        
    except Exception as e:
        logger.error(f"Error in delete_alert handler: {e}")
        await update.message.reply_text(
            "❌ An error occurred. Please try again later."
        )
