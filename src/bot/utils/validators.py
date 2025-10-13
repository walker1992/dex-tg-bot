"""
Validation utilities for bot inputs
"""
import logging
import re
from typing import Any, Dict, List, Optional, Union

from bot.utils.exceptions import ValidationError

logger = logging.getLogger(__name__)


class InputValidator:
    """Input validation utilities"""
    
    @staticmethod
    def validate_symbol(symbol: str) -> bool:
        """Validate trading symbol format"""
        try:
            if not symbol:
                return False
            
            symbol_upper = symbol.upper()
            
            # Check if it's a valid symbol format (alphanumeric, 3-10 characters)
            if not re.match(r'^[A-Z0-9]{3,10}$', symbol_upper):
                return False
            
            # Additional checks for common trading symbols
            # Must contain at least one letter (not just numbers)
            if not re.search(r'[A-Z]', symbol_upper):
                return False
            
            # Common valid symbols
            valid_symbols = [
                'BTC', 'ETH', 'USDT', 'USDC', 'BNB', 'ADA', 'SOL', 'DOT', 'MATIC', 'AVAX',
                'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'SOLUSDT', 'DOTUSDT',
                'BTCUSDC', 'ETHUSDC', 'BNBUSDC', 'ADAUSDC', 'SOLUSDC', 'DOTUSDC',
                'BTC-PERP', 'ETH-PERP', 'SOL-PERP', 'AVAX-PERP'
            ]
            
            # Check if it's a known valid symbol or follows common patterns
            if symbol_upper in valid_symbols:
                return True
            
            # Check common patterns: BASEQUOTE (e.g., BTCUSDT, ETHUSDC)
            if re.match(r'^[A-Z]{3,6}[A-Z]{3,6}$', symbol_upper):
                return True
            
            # Check perpetual patterns: SYMBOL-PERP
            if re.match(r'^[A-Z]{3,6}-PERP$', symbol_upper):
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to validate symbol: {e}")
            return False
    
    @staticmethod
    def validate_quantity(quantity: Union[str, float]) -> bool:
        """Validate quantity value"""
        try:
            if isinstance(quantity, str):
                quantity = float(quantity)
            
            if quantity <= 0:
                return False
            
            # Check for reasonable limits (adjust as needed)
            if quantity > 1000000:  # 1 million max
                return False
            
            return True
            
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_price(price: Union[str, float]) -> bool:
        """Validate price value"""
        try:
            if isinstance(price, str):
                price = float(price)
            
            if price <= 0:
                return False
            
            # Check for reasonable limits
            if price > 10000000:  # 10 million max
                return False
            
            return True
            
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_exchange(exchange: str) -> bool:
        """Validate exchange name"""
        try:
            valid_exchanges = ['hyperliquid', 'aster']
            return exchange.lower() in valid_exchanges
        except Exception:
            return False
    
    @staticmethod
    def validate_side(side: str) -> bool:
        """Validate order side"""
        try:
            valid_sides = ['buy', 'sell', 'long', 'short']
            return side.lower() in valid_sides
        except Exception:
            return False
    
    @staticmethod
    def validate_order_type(order_type: str) -> bool:
        """Validate order type"""
        try:
            valid_types = ['market', 'limit', 'stop', 'stop_limit']
            return order_type.lower() in valid_types
        except Exception:
            return False
    
    @staticmethod
    def validate_condition(condition: str, alert_type: str) -> bool:
        """Validate alert condition"""
        try:
            if alert_type == "price":
                valid_conditions = ['above', 'below', 'equals']
            elif alert_type == "funding":
                valid_conditions = ['above', 'below']
            elif alert_type == "position":
                valid_conditions = ['pnl_above', 'pnl_below', 'margin_above', 'margin_below']
            else:
                return False
            
            return condition.lower() in valid_conditions
        except Exception:
            return False
    
    @staticmethod
    def validate_threshold(threshold: Union[str, float], alert_type: str) -> bool:
        """Validate alert threshold value"""
        try:
            if isinstance(threshold, str):
                threshold = float(threshold)
            
            if alert_type == "price":
                return 0 < threshold < 10000000  # Reasonable price range
            elif alert_type == "funding":
                return -1 < threshold < 1  # Funding rate range
            elif alert_type == "position":
                return -1000000 < threshold < 1000000  # PnL range
            else:
                return False
                
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_telegram_id(telegram_id: Union[str, int]) -> bool:
        """Validate Telegram user ID"""
        try:
            if isinstance(telegram_id, str):
                telegram_id = int(telegram_id)
            
            # Telegram IDs are positive integers
            return isinstance(telegram_id, int) and telegram_id > 0
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_ethereum_address(address: str) -> bool:
        """Validate Ethereum address format"""
        try:
            if not address:
                return False
            
            # Check if it starts with 0x and is 42 characters long
            if not re.match(r'^0x[a-fA-F0-9]{40}$', address):
                return False
            
            return True
        except Exception:
            return False
    
    @staticmethod
    def validate_private_key(private_key: str) -> bool:
        """Validate private key format"""
        try:
            if not private_key:
                return False
            
            # Check if it starts with 0x and is 66 characters long
            if not re.match(r'^0x[a-fA-F0-9]{64}$', private_key):
                return False
            
            return True
        except Exception:
            return False
    
    @staticmethod
    def validate_api_key(api_key: str) -> bool:
        """Validate API key format"""
        try:
            if not api_key:
                return False
            
            # Basic validation - should be alphanumeric and reasonable length
            if not re.match(r'^[a-zA-Z0-9_-]{20,100}$', api_key):
                return False
            
            return True
        except Exception:
            return False
    
    @staticmethod
    def validate_api_secret(api_secret: str) -> bool:
        """Validate API secret format"""
        try:
            if not api_secret:
                return False
            
            # Basic validation - should be alphanumeric and reasonable length
            if not re.match(r'^[a-zA-Z0-9_-]{20,100}$', api_secret):
                return False
            
            return True
        except Exception:
            return False


class CommandValidator:
    """Command-specific validation"""
    
    @staticmethod
    def validate_buy_command(args: List[str]) -> Dict[str, Any]:
        """Validate /buy command arguments"""
        try:
            if len(args) < 2:
                raise ValidationError("Usage: /buy <symbol> <quantity> [price] [exchange]")
            
            symbol = args[0].upper()
            if not InputValidator.validate_symbol(symbol):
                raise ValidationError("Invalid symbol format")
            
            quantity = float(args[1])
            if not InputValidator.validate_quantity(quantity):
                raise ValidationError("Invalid quantity (must be positive)")
            
            price = None
            if len(args) > 2 and args[2] != 'market':
                price = float(args[2])
                if not InputValidator.validate_price(price):
                    raise ValidationError("Invalid price (must be positive)")
            
            exchange = args[3].lower() if len(args) > 3 else 'hyperliquid'
            if not InputValidator.validate_exchange(exchange):
                raise ValidationError("Invalid exchange (hyperliquid, aster)")
            
            return {
                'symbol': symbol,
                'quantity': quantity,
                'price': price,
                'exchange': exchange
            }
            
        except ValueError as e:
            raise ValidationError("Invalid number format")
        except Exception as e:
            raise ValidationError(str(e))
    
    @staticmethod
    def validate_sell_command(args: List[str]) -> Dict[str, Any]:
        """Validate /sell command arguments"""
        try:
            if len(args) < 2:
                raise ValidationError("Usage: /sell <symbol> <quantity> [price] [exchange]")
            
            symbol = args[0].upper()
            if not InputValidator.validate_symbol(symbol):
                raise ValidationError("Invalid symbol format")
            
            quantity = float(args[1])
            if not InputValidator.validate_quantity(quantity):
                raise ValidationError("Invalid quantity (must be positive)")
            
            price = None
            if len(args) > 2 and args[2] != 'market':
                price = float(args[2])
                if not InputValidator.validate_price(price):
                    raise ValidationError("Invalid price (must be positive)")
            
            exchange = args[3].lower() if len(args) > 3 else 'hyperliquid'
            if not InputValidator.validate_exchange(exchange):
                raise ValidationError("Invalid exchange (hyperliquid, aster)")
            
            return {
                'symbol': symbol,
                'quantity': quantity,
                'price': price,
                'exchange': exchange
            }
            
        except ValueError as e:
            raise ValidationError("Invalid number format")
        except Exception as e:
            raise ValidationError(str(e))
    
    @staticmethod
    def validate_price_command(args: List[str]) -> Dict[str, Any]:
        """Validate /price command arguments"""
        try:
            if len(args) < 1:
                raise ValidationError("Usage: /price <symbol> [exchange]")
            
            symbol = args[0].upper()
            if not InputValidator.validate_symbol(symbol):
                raise ValidationError("Invalid symbol format")
            
            exchange = args[1].lower() if len(args) > 1 else 'hyperliquid'
            if not InputValidator.validate_exchange(exchange):
                raise ValidationError("Invalid exchange (hyperliquid, aster)")
            
            return {
                'symbol': symbol,
                'exchange': exchange
            }
            
        except Exception as e:
            raise ValidationError(str(e))
    
    @staticmethod
    def validate_alert_price_command(args: List[str]) -> Dict[str, Any]:
        """Validate /alert_price command arguments"""
        try:
            if len(args) < 3:
                raise ValidationError("Usage: /alert_price <symbol> <condition> <value> [exchange]")
            
            symbol = args[0].upper()
            if not InputValidator.validate_symbol(symbol):
                raise ValidationError("Invalid symbol format")
            
            condition = args[1].lower()
            if not InputValidator.validate_condition(condition, "price"):
                raise ValidationError("Invalid condition (above, below, equals)")
            
            value = float(args[2])
            if not InputValidator.validate_threshold(value, "price"):
                raise ValidationError("Invalid price value")
            
            exchange = args[3].lower() if len(args) > 3 else 'hyperliquid'
            if not InputValidator.validate_exchange(exchange):
                raise ValidationError("Invalid exchange (hyperliquid, aster)")
            
            return {
                'symbol': symbol,
                'condition': condition,
                'value': value,
                'exchange': exchange
            }
            
        except ValueError as e:
            raise ValidationError("Invalid number format")
        except Exception as e:
            raise ValidationError(str(e))
    
    @staticmethod
    def validate_alert_funding_command(args: List[str]) -> Dict[str, Any]:
        """Validate /alert_funding command arguments"""
        try:
            if len(args) < 2:
                raise ValidationError("Usage: /alert_funding <symbol> <value> [exchange]")
            
            symbol = args[0].upper()
            if not InputValidator.validate_symbol(symbol):
                raise ValidationError("Invalid symbol format")
            
            value = float(args[1])
            if not InputValidator.validate_threshold(value, "funding"):
                raise ValidationError("Invalid funding rate value")
            
            exchange = args[2].lower() if len(args) > 2 else 'hyperliquid'
            if not InputValidator.validate_exchange(exchange):
                raise ValidationError("Invalid exchange (hyperliquid, aster)")
            
            return {
                'symbol': symbol,
                'value': value,
                'exchange': exchange
            }
            
        except ValueError as e:
            raise ValidationError("Invalid number format")
        except Exception as e:
            raise ValidationError(str(e))
    
    @staticmethod
    def validate_alert_position_command(args: List[str]) -> Dict[str, Any]:
        """Validate /alert_position command arguments"""
        try:
            if len(args) < 3:
                raise ValidationError("Usage: /alert_position <symbol> <condition> <value> [exchange]")
            
            symbol = args[0].upper()
            if not InputValidator.validate_symbol(symbol):
                raise ValidationError("Invalid symbol format")
            
            condition = args[1].lower()
            if not InputValidator.validate_condition(condition, "position"):
                raise ValidationError("Invalid condition (pnl_above, pnl_below, margin_above, margin_below)")
            
            value = float(args[2])
            if not InputValidator.validate_threshold(value, "position"):
                raise ValidationError("Invalid threshold value")
            
            exchange = args[3].lower() if len(args) > 3 else 'hyperliquid'
            if not InputValidator.validate_exchange(exchange):
                raise ValidationError("Invalid exchange (hyperliquid, aster)")
            
            return {
                'symbol': symbol,
                'condition': condition,
                'value': value,
                'exchange': exchange
            }
            
        except ValueError as e:
            raise ValidationError("Invalid number format")
        except Exception as e:
            raise ValidationError(str(e))


class RiskValidator:
    """Risk management validation"""
    
    @staticmethod
    def validate_position_size(size: float, max_size: float = 1000.0) -> bool:
        """Validate position size against limits"""
        try:
            return 0 < size <= max_size
        except Exception:
            return False
    
    @staticmethod
    def validate_leverage(leverage: float, max_leverage: float = 10.0) -> bool:
        """Validate leverage against limits"""
        try:
            return 1 <= leverage <= max_leverage
        except Exception:
            return False
    
    @staticmethod
    def validate_daily_loss_limit(loss: float, limit: float = 100.0) -> bool:
        """Validate daily loss against limit"""
        try:
            return abs(loss) <= limit
        except Exception:
            return False
    
    @staticmethod
    def validate_margin_ratio(ratio: float, min_ratio: float = 0.1) -> bool:
        """Validate margin ratio"""
        try:
            return ratio >= min_ratio
        except Exception:
            return False


def validate_user_input(user_id: int, input_type: str, value: Any) -> bool:
    """General user input validation"""
    try:
        if not InputValidator.validate_telegram_id(user_id):
            return False
        
        if input_type == "symbol":
            return InputValidator.validate_symbol(value)
        elif input_type == "quantity":
            return InputValidator.validate_quantity(value)
        elif input_type == "price":
            return InputValidator.validate_price(value)
        elif input_type == "exchange":
            return InputValidator.validate_exchange(value)
        elif input_type == "ethereum_address":
            return InputValidator.validate_ethereum_address(value)
        elif input_type == "private_key":
            return InputValidator.validate_private_key(value)
        elif input_type == "api_key":
            return InputValidator.validate_api_key(value)
        elif input_type == "api_secret":
            return InputValidator.validate_api_secret(value)
        else:
            return False
            
    except Exception as e:
        logger.error(f"Validation error: {e}")
        return False
