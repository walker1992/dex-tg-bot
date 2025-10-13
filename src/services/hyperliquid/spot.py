"""
Hyperliquid spot trading service
"""
import logging
from decimal import Decimal
from typing import Any, Dict, List, Optional

from ..base import SpotService, Balance, Order, OrderSide, OrderType, TimeInForce, ExchangeError
from .client import HyperliquidClient


logger = logging.getLogger(__name__)


class HyperliquidSpotService(SpotService):
    """Hyperliquid spot trading service"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.client = HyperliquidClient(config)
    
    async def connect(self) -> bool:
        """Connect to Hyperliquid spot"""
        return await self.client.connect()
    
    async def disconnect(self) -> None:
        """Disconnect from Hyperliquid spot"""
        await self.client.disconnect()
    
    async def get_account_info(self) -> Dict[str, Any]:
        """Get account information"""
        return await self.client.get_account_info()
    
    async def get_balances(self) -> List[Balance]:
        """Get spot balances using Hyperliquid's spot_user_state API"""
        if not self.client.info or not self.client.account_address:
            return []
        
        try:
            # Use the official SDK's spot_user_state method
            spot_user_state = self.client.info.spot_user_state(self.client.account_address)
            balances = []
            
            # Parse spot balances from the response
            for balance_data in spot_user_state.get("balances", []):
                asset_name = balance_data.get("coin", "")
                total = Decimal(str(balance_data.get("total", 0)))
                hold = Decimal(str(balance_data.get("hold", 0)))
                free = total - hold
                
                if total > 0:  # Only include non-zero balances
                    balances.append(Balance(
                        asset=asset_name,
                        free=free,
                        locked=hold,
                        total=total
                    ))
            
            return balances
            
        except Exception as e:
            logger.error(f"Failed to get spot balances: {e}")
            return []
    
    async def get_positions(self) -> List[Any]:
        """Get current positions (empty for spot)"""
        return []  # Spot trading doesn't have positions
    
    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Order]:
        """Get open orders"""
        return await self.client.get_open_orders(symbol)
    
    async def get_order(self, order_id: str, symbol: str) -> Order:
        """Get specific order"""
        return await self.client.get_order(order_id, symbol)
    
    async def place_order(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        quantity: Decimal,
        price: Optional[Decimal] = None,
        time_in_force: TimeInForce = TimeInForce.GTC,
        client_order_id: Optional[str] = None
    ) -> Order:
        """Place a new order"""
        return await self.client.place_order(
            symbol, side, order_type, quantity, price, time_in_force, client_order_id
        )
    
    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        """Cancel an order"""
        return await self.client.cancel_order(order_id, symbol)
    
    async def cancel_all_orders(self, symbol: Optional[str] = None) -> bool:
        """Cancel all orders"""
        return await self.client.cancel_all_orders(symbol)
    
    async def get_ticker(self, symbol: str) -> Any:
        """Get ticker information"""
        return await self.client.get_ticker(symbol)
    
    async def get_order_book(self, symbol: str, limit: int = 100) -> Any:
        """Get order book"""
        return await self.client.get_order_book(symbol, limit)
    
    async def get_funding_rate(self, symbol: str) -> Any:
        """Get funding rate (not applicable for spot)"""
        raise ExchangeError("Funding rate not applicable for spot trading")
    
    async def get_symbol_info(self, symbol: str) -> Any:
        """Get symbol information"""
        return await self.client.get_symbol_info(symbol)
    
    async def get_exchange_info(self) -> Dict[str, Any]:
        """Get exchange information"""
        return await self.client.get_exchange_info()
    
    async def get_spot_balances(self) -> List[Balance]:
        """Get spot balances"""
        return await self.get_balances()
    
    async def place_spot_order(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        quantity: Decimal,
        price: Optional[Decimal] = None,
        time_in_force: TimeInForce = TimeInForce.GTC
    ) -> Order:
        """Place spot order"""
        return await self.place_order(symbol, side, order_type, quantity, price, time_in_force)
    
    async def get_spot_ticker(self, symbol: str) -> Any:
        """Get spot ticker"""
        return await self.get_ticker(symbol)
    
    async def get_spot_order_book(self, symbol: str, limit: int = 100) -> Any:
        """Get spot order book"""
        return await self.get_order_book(symbol, limit)
    
    async def get_spot_symbols(self) -> List[str]:
        """Get available spot symbols"""
        try:
            exchange_info = await self.get_exchange_info()
            symbols = []
            for symbol_info in exchange_info.get("symbols", []):
                symbol = symbol_info.get("symbol", "")
                if symbol:  # Hyperliquid primarily supports futures, but we can list all symbols
                    symbols.append(symbol)
            return symbols
        except Exception as e:
            logger.error(f"Failed to get spot symbols: {e}")
            return []
    
    async def get_spot_trading_pairs(self) -> List[Dict[str, Any]]:
        """Get spot trading pairs"""
        try:
            exchange_info = await self.get_exchange_info()
            pairs = []
            for symbol_info in exchange_info.get("symbols", []):
                pairs.append({
                    "symbol": symbol_info.get("symbol", ""),
                    "base_asset": symbol_info.get("base_asset", ""),
                    "quote_asset": symbol_info.get("quote_asset", ""),
                    "status": symbol_info.get("status", "TRADING")
                })
            return pairs
        except Exception as e:
            logger.error(f"Failed to get spot trading pairs: {e}")
            return []
