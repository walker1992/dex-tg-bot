"""
Formatting utilities for bot messages
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


def format_currency(amount: float, currency: str = "USD", precision: int = 2) -> str:
    """Format currency amount"""
    try:
        if currency == "USD":
            return f"${amount:,.{precision}f}"
        elif currency == "BTC":
            return f"{amount:.{precision}f} BTC"
        elif currency == "ETH":
            return f"{amount:.{precision}f} ETH"
        else:
            return f"{amount:,.{precision}f} {currency}"
    except Exception as e:
        logger.error(f"Failed to format currency: {e}")
        return f"{amount} {currency}"


def format_percentage(value: float, precision: int = 2) -> str:
    """Format percentage value"""
    try:
        return f"{value:.{precision}f}%"
    except Exception as e:
        logger.error(f"Failed to format percentage: {e}")
        return f"{value}%"


def format_number(value: float, precision: int = 2) -> str:
    """Format number with precision"""
    try:
        return f"{value:,.{precision}f}"
    except Exception as e:
        logger.error(f"Failed to format number: {e}")
        return str(value)


def format_timestamp(timestamp: Union[str, datetime], format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format timestamp"""
    try:
        if isinstance(timestamp, str):
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        else:
            dt = timestamp
        
        return dt.strftime(format_str)
    except Exception as e:
        logger.error(f"Failed to format timestamp: {e}")
        return str(timestamp)


def format_duration(seconds: int) -> str:
    """Format duration in seconds to human readable format"""
    try:
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            minutes = seconds // 60
            remaining_seconds = seconds % 60
            return f"{minutes}m {remaining_seconds}s"
        elif seconds < 86400:
            hours = seconds // 3600
            remaining_minutes = (seconds % 3600) // 60
            return f"{hours}h {remaining_minutes}m"
        else:
            days = seconds // 86400
            remaining_hours = (seconds % 86400) // 3600
            return f"{days}d {remaining_hours}h"
    except Exception as e:
        logger.error(f"Failed to format duration: {e}")
        return f"{seconds}s"


def format_balance(balance: Dict[str, Any]) -> str:
    """Format balance information"""
    try:
        asset = balance.get('asset', 'Unknown')
        total = balance.get('total', 0)
        free = balance.get('free', 0)
        locked = balance.get('locked', 0)
        
        return f"**{asset}:** {format_number(total, 8)} (Free: {format_number(free, 8)}, Locked: {format_number(locked, 8)})"
    except Exception as e:
        logger.error(f"Failed to format balance: {e}")
        return str(balance)


def format_position(position: Dict[str, Any]) -> str:
    """Format position information"""
    try:
        symbol = position.get('symbol', 'Unknown')
        side = position.get('side', 'Unknown')
        size = position.get('size', 0)
        entry_price = position.get('entry_price', 0)
        current_price = position.get('current_price', 0)
        pnl = position.get('pnl', 0)
        pnl_percent = position.get('pnl_percent', 0)
        
        pnl_emoji = "📈" if pnl >= 0 else "📉"
        
        return f"""
**{symbol} {side.title()}**
• Size: {format_number(size, 8)}
• Entry: {format_currency(entry_price)}
• Current: {format_currency(current_price)}
• PnL: {pnl_emoji} {format_currency(pnl)} ({format_percentage(pnl_percent)})
        """.strip()
    except Exception as e:
        logger.error(f"Failed to format position: {e}")
        return str(position)


def format_order(order: Dict[str, Any]) -> str:
    """Format order information"""
    try:
        symbol = order.get('symbol', 'Unknown')
        side = order.get('side', 'Unknown')
        order_type = order.get('order_type', 'Unknown')
        quantity = order.get('quantity', 0)
        price = order.get('price', 0)
        status = order.get('status', 'Unknown')
        order_id = order.get('order_id', 'Unknown')
        created_at = order.get('created_at', '')
        
        status_emoji = {
            'pending': '⏳',
            'filled': '✅',
            'cancelled': '❌',
            'rejected': '🚫'
        }.get(status.lower(), '❓')
        
        price_text = format_currency(price) if price > 0 else "Market"
        
        return f"""
**{symbol} {side.title()} {order_type.title()}** {status_emoji}
• Quantity: {format_number(quantity, 8)}
• Price: {price_text}
• Status: {status.title()}
• ID: {order_id}
• Time: {format_timestamp(created_at)}
        """.strip()
    except Exception as e:
        logger.error(f"Failed to format order: {e}")
        return str(order)


def format_ticker(ticker: Dict[str, Any]) -> str:
    """Format ticker information"""
    try:
        symbol = ticker.get('symbol', 'Unknown')
        last_price = ticker.get('last_price', 0)
        bid_price = ticker.get('bid_price', 0)
        ask_price = ticker.get('ask_price', 0)
        volume = ticker.get('volume', 0)
        change_24h = ticker.get('change_24h', 0)
        change_percent_24h = ticker.get('change_percent_24h', 0)
        
        change_emoji = "📈" if change_24h >= 0 else "📉"
        
        return f"""
**{symbol} Price**
• Last: {format_currency(last_price)}
• Bid: {format_currency(bid_price)}
• Ask: {format_currency(ask_price)}
• 24h Change: {change_emoji} {format_currency(change_24h)} ({format_percentage(change_percent_24h)})
• 24h Volume: {format_number(volume, 2)}
        """.strip()
    except Exception as e:
        logger.error(f"Failed to format ticker: {e}")
        return str(ticker)


def format_funding_rate(funding_rate: Dict[str, Any]) -> str:
    """Format funding rate information"""
    try:
        symbol = funding_rate.get('symbol', 'Unknown')
        rate = funding_rate.get('funding_rate', 0)
        next_funding_time = funding_rate.get('next_funding_time', '')
        
        rate_percent = rate * 100
        rate_emoji = "📈" if rate > 0 else "📉" if rate < 0 else "➡️"
        
        return f"""
**{symbol} Funding Rate**
• Rate: {rate_emoji} {format_percentage(rate_percent, 4)}
• Next Funding: {format_timestamp(next_funding_time)}
        """.strip()
    except Exception as e:
        logger.error(f"Failed to format funding rate: {e}")
        return str(funding_rate)


def format_alert(alert: Dict[str, Any]) -> str:
    """Format alert information"""
    try:
        alert_type = alert.get('alert_type', 'Unknown')
        symbol = alert.get('symbol', 'Unknown')
        condition = alert.get('condition_type', 'Unknown')
        threshold = alert.get('threshold_value', 0)
        exchange = alert.get('exchange', 'Unknown')
        is_active = alert.get('is_active', True)
        created_at = alert.get('created_at', '')
        
        status_emoji = "🔔" if is_active else "🔕"
        
        if alert_type == "price":
            threshold_text = format_currency(threshold)
        elif alert_type == "funding":
            threshold_text = format_percentage(threshold * 100, 4)
        else:
            threshold_text = format_number(threshold)
        
        return f"""
**{alert_type.title()} Alert** {status_emoji}
• Symbol: {symbol}
• Condition: {condition.title()}
• Threshold: {threshold_text}
• Exchange: {exchange.title()}
• Created: {format_timestamp(created_at)}
        """.strip()
    except Exception as e:
        logger.error(f"Failed to format alert: {e}")
        return str(alert)


def format_portfolio_summary(portfolio: Dict[str, Any]) -> str:
    """Format portfolio summary"""
    try:
        total_value = portfolio.get('total_value', 0)
        total_pnl = portfolio.get('total_pnl', 0)
        total_pnl_percent = portfolio.get('total_pnl_percent', 0)
        positions_count = portfolio.get('positions_count', 0)
        active_orders = portfolio.get('active_orders', 0)
        
        pnl_emoji = "📈" if total_pnl >= 0 else "📉"
        
        return f"""
**Portfolio Summary**
• Total Value: {format_currency(total_value)}
• Total PnL: {pnl_emoji} {format_currency(total_pnl)} ({format_percentage(total_pnl_percent)})
• Active Positions: {positions_count}
• Open Orders: {active_orders}
        """.strip()
    except Exception as e:
        logger.error(f"Failed to format portfolio summary: {e}")
        return str(portfolio)


def format_error_message(error: str, context: str = "") -> str:
    """Format error message"""
    try:
        if context:
            return f"❌ **Error in {context}:**\n{error}"
        else:
            return f"❌ **Error:**\n{error}"
    except Exception as e:
        logger.error(f"Failed to format error message: {e}")
        return f"❌ Error: {error}"


def format_success_message(message: str, context: str = "") -> str:
    """Format success message"""
    try:
        if context:
            return f"✅ **{context}:**\n{message}"
        else:
            return f"✅ {message}"
    except Exception as e:
        logger.error(f"Failed to format success message: {e}")
        return f"✅ {message}"


def format_warning_message(message: str, context: str = "") -> str:
    """Format warning message"""
    try:
        if context:
            return f"⚠️ **Warning in {context}:**\n{message}"
        else:
            return f"⚠️ **Warning:**\n{message}"
    except Exception as e:
        logger.error(f"Failed to format warning message: {e}")
        return f"⚠️ Warning: {message}"


def format_info_message(message: str, context: str = "") -> str:
    """Format info message"""
    try:
        if context:
            return f"ℹ️ **{context}:**\n{message}"
        else:
            return f"ℹ️ {message}"
    except Exception as e:
        logger.error(f"Failed to format info message: {e}")
        return f"ℹ️ {message}"


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to maximum length"""
    try:
        if len(text) <= max_length:
            return text
        return text[:max_length - len(suffix)] + suffix
    except Exception as e:
        logger.error(f"Failed to truncate text: {e}")
        return text


def format_list(items: List[str], max_items: int = 10, separator: str = "\n") -> str:
    """Format list of items"""
    try:
        if len(items) <= max_items:
            return separator.join(items)
        else:
            visible_items = items[:max_items]
            remaining_count = len(items) - max_items
            return separator.join(visible_items) + f"\n... and {remaining_count} more"
    except Exception as e:
        logger.error(f"Failed to format list: {e}")
        return str(items)


def format_table(data: List[Dict[str, Any]], columns: List[str], max_rows: int = 10) -> str:
    """Format data as table"""
    try:
        if not data:
            return "No data available"
        
        # Limit rows
        display_data = data[:max_rows]
        
        # Create table header
        header = " | ".join(columns)
        separator = " | ".join(["-" * len(col) for col in columns])
        
        # Create table rows
        rows = []
        for row in display_data:
            row_data = []
            for col in columns:
                value = str(row.get(col, ""))
                # Truncate long values
                if len(value) > 15:
                    value = value[:12] + "..."
                row_data.append(value)
            rows.append(" | ".join(row_data))
        
        # Combine header, separator, and rows
        table_lines = [header, separator] + rows
        
        # Add summary if truncated
        if len(data) > max_rows:
            table_lines.append(f"... and {len(data) - max_rows} more rows")
        
        return "\n".join(table_lines)
        
    except Exception as e:
        logger.error(f"Failed to format table: {e}")
        return str(data)
