"""
Main Keyboard Layouts
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton


def get_main_keyboard() -> InlineKeyboardMarkup:
    """Get main menu keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("💰 Balance", callback_data="menu_balance"),
            InlineKeyboardButton("📊 Positions", callback_data="menu_positions")
        ],
        [
            InlineKeyboardButton("📋 Orders", callback_data="menu_orders"),
            InlineKeyboardButton("📈 Market Data", callback_data="menu_market")
        ],
        [
            InlineKeyboardButton("🛒 Trading", callback_data="menu_trading"),
            InlineKeyboardButton("🔔 Alerts", callback_data="menu_alerts")
        ],
        [
            InlineKeyboardButton("⚙️ Settings", callback_data="menu_settings"),
            InlineKeyboardButton("🔗 Connect Exchange", callback_data="menu_connect")
        ],
        [
            InlineKeyboardButton("❓ Help", callback_data="menu_help")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_exchange_keyboard() -> InlineKeyboardMarkup:
    """Get exchange selection keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("🔷 Hyperliquid", callback_data="exchange_hyperliquid"),
            InlineKeyboardButton("🔶 Aster", callback_data="exchange_aster")
        ],
        [
            InlineKeyboardButton("📊 Both Exchanges", callback_data="exchange_both")
        ],
        [
            InlineKeyboardButton("🔙 Back to Main", callback_data="menu_main")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_trading_keyboard() -> InlineKeyboardMarkup:
    """Get trading keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("💰 Balance", callback_data="trading_balance"),
            InlineKeyboardButton("📊 Positions", callback_data="trading_positions")
        ],
        [
            InlineKeyboardButton("📋 Orders", callback_data="trading_orders"),
            InlineKeyboardButton("📈 Price", callback_data="trading_price")
        ],
        [
            InlineKeyboardButton("🛒 Quick Buy", callback_data="trading_quick_buy"),
            InlineKeyboardButton("🛍️ Quick Sell", callback_data="trading_quick_sell")
        ],
        [
            InlineKeyboardButton("🔙 Back to Main", callback_data="menu_main")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_market_keyboard() -> InlineKeyboardMarkup:
    """Get market data keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("📈 Price", callback_data="market_price"),
            InlineKeyboardButton("📊 Depth", callback_data="market_depth")
        ],
        [
            InlineKeyboardButton("💰 Funding Rate", callback_data="market_funding"),
            InlineKeyboardButton("📊 24h Stats", callback_data="market_24h")
        ],
        [
            InlineKeyboardButton("🔍 Search Symbol", callback_data="market_search"),
            InlineKeyboardButton("⭐ Favorites", callback_data="market_favorites")
        ],
        [
            InlineKeyboardButton("🔙 Back to Main", callback_data="menu_main")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_alerts_keyboard() -> InlineKeyboardMarkup:
    """Get alerts keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("🔔 My Alerts", callback_data="alerts_list"),
            InlineKeyboardButton("➕ New Alert", callback_data="alerts_new")
        ],
        [
            InlineKeyboardButton("📈 Price Alert", callback_data="alerts_price"),
            InlineKeyboardButton("💰 Funding Alert", callback_data="alerts_funding")
        ],
        [
            InlineKeyboardButton("📊 Position Alert", callback_data="alerts_position"),
            InlineKeyboardButton("⚙️ Alert Settings", callback_data="alerts_settings")
        ],
        [
            InlineKeyboardButton("🔙 Back to Main", callback_data="menu_main")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_settings_keyboard() -> InlineKeyboardMarkup:
    """Get settings keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("🔗 Exchange Accounts", callback_data="settings_accounts"),
            InlineKeyboardButton("🔐 Security", callback_data="settings_security")
        ],
        [
            InlineKeyboardButton("🔔 Notifications", callback_data="settings_notifications"),
            InlineKeyboardButton("🎨 Theme", callback_data="settings_theme")
        ],
        [
            InlineKeyboardButton("📊 Trading Settings", callback_data="settings_trading"),
            InlineKeyboardButton("🛡️ Risk Management", callback_data="settings_risk")
        ],
        [
            InlineKeyboardButton("🔙 Back to Main", callback_data="menu_main")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_connect_keyboard() -> InlineKeyboardMarkup:
    """Get connect exchange keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("🔷 Connect Hyperliquid", callback_data="connect_hyperliquid"),
            InlineKeyboardButton("🔶 Connect Aster", callback_data="connect_aster")
        ],
        [
            InlineKeyboardButton("📊 View Accounts", callback_data="connect_accounts"),
            InlineKeyboardButton("🔌 Disconnect", callback_data="connect_disconnect")
        ],
        [
            InlineKeyboardButton("🔙 Back to Main", callback_data="menu_main")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_symbol_keyboard(symbols: list) -> InlineKeyboardMarkup:
    """Get symbol selection keyboard"""
    keyboard = []
    
    # Create rows of 2 buttons each
    for i in range(0, len(symbols), 2):
        row = []
        for j in range(2):
            if i + j < len(symbols):
                symbol = symbols[i + j]
                row.append(InlineKeyboardButton(symbol, callback_data=f"symbol_{symbol}"))
        keyboard.append(row)
    
    # Add back button
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="menu_market")])
    
    return InlineKeyboardMarkup(keyboard)


def get_alert_type_keyboard() -> InlineKeyboardMarkup:
    """Get alert type selection keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("📈 Price Alert", callback_data="alert_type_price"),
            InlineKeyboardButton("💰 Funding Alert", callback_data="alert_type_funding")
        ],
        [
            InlineKeyboardButton("📊 Position Alert", callback_data="alert_type_position"),
            InlineKeyboardButton("⏰ Time Alert", callback_data="alert_type_time")
        ],
        [
            InlineKeyboardButton("🔙 Back to Alerts", callback_data="menu_alerts")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_condition_keyboard(alert_type: str) -> InlineKeyboardMarkup:
    """Get condition selection keyboard based on alert type"""
    if alert_type == "price":
        keyboard = [
            [
                InlineKeyboardButton("📈 Above", callback_data="condition_above"),
                InlineKeyboardButton("📉 Below", callback_data="condition_below")
            ],
            [
                InlineKeyboardButton("🎯 Equals", callback_data="condition_equals")
            ]
        ]
    elif alert_type == "funding":
        keyboard = [
            [
                InlineKeyboardButton("📈 Above", callback_data="condition_above"),
                InlineKeyboardButton("📉 Below", callback_data="condition_below")
            ]
        ]
    elif alert_type == "position":
        keyboard = [
            [
                InlineKeyboardButton("💰 PnL Above", callback_data="condition_pnl_above"),
                InlineKeyboardButton("💰 PnL Below", callback_data="condition_pnl_below")
            ],
            [
                InlineKeyboardButton("🛡️ Margin Above", callback_data="condition_margin_above"),
                InlineKeyboardButton("🛡️ Margin Below", callback_data="condition_margin_below")
            ]
        ]
    else:
        keyboard = []
    
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="alerts_new")])
    
    return InlineKeyboardMarkup(keyboard)


def get_confirmation_keyboard(action: str, data: str) -> InlineKeyboardMarkup:
    """Get confirmation keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Confirm", callback_data=f"confirm_{action}_{data}"),
            InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_{action}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_pagination_keyboard(current_page: int, total_pages: int, prefix: str) -> InlineKeyboardMarkup:
    """Get pagination keyboard"""
    keyboard = []
    
    # Previous and Next buttons
    row = []
    if current_page > 1:
        row.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"{prefix}_page_{current_page-1}"))
    
    row.append(InlineKeyboardButton(f"Page {current_page}/{total_pages}", callback_data="noop"))
    
    if current_page < total_pages:
        row.append(InlineKeyboardButton("Next ➡️", callback_data=f"{prefix}_page_{current_page+1}"))
    
    keyboard.append(row)
    
    return InlineKeyboardMarkup(keyboard)


def get_quick_actions_keyboard() -> ReplyKeyboardMarkup:
    """Get quick actions reply keyboard"""
    keyboard = [
        [
            KeyboardButton("💰 Balance"),
            KeyboardButton("📊 Positions")
        ],
        [
            KeyboardButton("📈 Price BTC"),
            KeyboardButton("📈 Price ETH")
        ],
        [
            KeyboardButton("🔔 Alerts"),
            KeyboardButton("⚙️ Settings")
        ]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)


def get_trading_quick_keyboard() -> ReplyKeyboardMarkup:
    """Get trading quick actions keyboard"""
    keyboard = [
        [
            KeyboardButton("🛒 Buy BTC"),
            KeyboardButton("🛍️ Sell BTC")
        ],
        [
            KeyboardButton("🛒 Buy ETH"),
            KeyboardButton("🛍️ Sell ETH")
        ],
        [
            KeyboardButton("📊 My Positions"),
            KeyboardButton("📋 My Orders")
        ],
        [
            KeyboardButton("🔙 Main Menu")
        ]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)


def get_trading_exchange_keyboard() -> InlineKeyboardMarkup:
    """Get trading exchange selection keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("🔷 Hyperliquid", callback_data="trade_exchange_hyperliquid"),
            InlineKeyboardButton("🔶 Aster", callback_data="trade_exchange_aster")
        ],
        [
            InlineKeyboardButton("🔙 Back to Trading", callback_data="menu_trading")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_trading_market_type_keyboard(exchange: str) -> InlineKeyboardMarkup:
    """Get trading market type selection keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("💱 Spot Trading", callback_data=f"trade_market_spot_{exchange}"),
            InlineKeyboardButton("📈 Futures Trading", callback_data=f"trade_market_futures_{exchange}")
        ],
        [
            InlineKeyboardButton("🔙 Back to Exchange", callback_data="trade_exchange_select")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_trading_side_keyboard(exchange: str, market_type: str) -> InlineKeyboardMarkup:
    """Get trading side selection keyboard"""
    if market_type == "futures":
        keyboard = [
            [
                InlineKeyboardButton("🟢 Long (Buy)", callback_data=f"trade_side_long_{exchange}_{market_type}"),
                InlineKeyboardButton("🔴 Short (Sell)", callback_data=f"trade_side_short_{exchange}_{market_type}")
            ],
            [
                InlineKeyboardButton("🔙 Back to Market Type", callback_data=f"trade_exchange_{exchange}")
            ]
        ]
    else:  # spot
        keyboard = [
            [
                InlineKeyboardButton("🛒 Buy", callback_data=f"trade_side_buy_{exchange}_{market_type}"),
                InlineKeyboardButton("🛍️ Sell", callback_data=f"trade_side_sell_{exchange}_{market_type}")
            ],
            [
                InlineKeyboardButton("🔙 Back to Market Type", callback_data=f"trade_exchange_{exchange}")
            ]
        ]
    return InlineKeyboardMarkup(keyboard)


def get_leverage_keyboard(exchange: str, symbol: str) -> InlineKeyboardMarkup:
    """Get leverage selection keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("1x", callback_data=f"leverage_1_{exchange}_{symbol}"),
            InlineKeyboardButton("2x", callback_data=f"leverage_2_{exchange}_{symbol}"),
            InlineKeyboardButton("3x", callback_data=f"leverage_3_{exchange}_{symbol}")
        ],
        [
            InlineKeyboardButton("5x", callback_data=f"leverage_5_{exchange}_{symbol}"),
            InlineKeyboardButton("10x", callback_data=f"leverage_10_{exchange}_{symbol}"),
            InlineKeyboardButton("20x", callback_data=f"leverage_20_{exchange}_{symbol}")
        ],
        [
            InlineKeyboardButton("50x", callback_data=f"leverage_50_{exchange}_{symbol}"),
            InlineKeyboardButton("100x", callback_data=f"leverage_100_{exchange}_{symbol}"),
            InlineKeyboardButton("Custom", callback_data=f"leverage_custom_{exchange}_{symbol}")
        ],
        [
            InlineKeyboardButton("🔙 Back", callback_data=f"trade_symbol_{exchange}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_order_type_keyboard(exchange: str, market_type: str, side: str) -> InlineKeyboardMarkup:
    """Get order type selection keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("📈 Market Order", callback_data=f"order_type_market_{exchange}_{market_type}_{side}"),
            InlineKeyboardButton("📊 Limit Order", callback_data=f"order_type_limit_{exchange}_{market_type}_{side}")
        ],
        [
            InlineKeyboardButton("🔙 Back to Side", callback_data=f"trade_market_{market_type}_{exchange}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_quick_trade_keyboard() -> InlineKeyboardMarkup:
    """Get quick trade keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("🛒 Quick Buy", callback_data="quick_buy"),
            InlineKeyboardButton("🛍️ Quick Sell", callback_data="quick_sell")
        ],
        [
            InlineKeyboardButton("📊 Close Position", callback_data="quick_close"),
            InlineKeyboardButton("⚙️ Set Leverage", callback_data="quick_leverage")
        ],
        [
            InlineKeyboardButton("🔙 Back to Main", callback_data="menu_main")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)
