"""
Hyperliquid futures trading service
"""
import logging
from decimal import Decimal
from typing import Any, Dict, List, Optional

from ..base import (
    FuturesService, Balance, Position, Order, FundingRate, 
    OrderSide, OrderType, TimeInForce, ExchangeError
)
from .client import HyperliquidClient


logger = logging.getLogger(__name__)


class HyperliquidFuturesService(FuturesService):
    """Hyperliquid futures trading service"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.client = HyperliquidClient(config)
    
    async def connect(self) -> bool:
        """Connect to Hyperliquid futures"""
        return await self.client.connect()
    
    async def disconnect(self) -> None:
        """Disconnect from Hyperliquid futures"""
        await self.client.disconnect()
    
    async def get_account_info(self) -> Dict[str, Any]:
        """Get account information"""
        return await self.client.get_account_info()
    
    async def get_balances(self) -> List[Balance]:
        """Get account balances"""
        return await self.client.get_balances()
    
    async def get_positions(self) -> List[Position]:
        """Get current positions"""
        return await self.client.get_positions()
    
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
    
    async def get_funding_rate(self, symbol: str) -> FundingRate:
        """Get funding rate"""
        return await self.client.get_funding_rate(symbol)
    
    async def get_symbol_info(self, symbol: str) -> Any:
        """Get symbol information"""
        return await self.client.get_symbol_info(symbol)
    
    async def get_exchange_info(self) -> Dict[str, Any]:
        """Get exchange information"""
        return await self.client.get_exchange_info()
    
    async def get_futures_balances(self) -> List[Balance]:
        """Get futures balances"""
        return await self.get_balances()
    
    async def get_futures_positions(self) -> List[Position]:
        """Get futures positions"""
        return await self.get_positions()
    
    async def place_futures_order(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        quantity: Decimal,
        price: Optional[Decimal] = None,
        time_in_force: TimeInForce = TimeInForce.GTC,
        reduce_only: bool = False
    ) -> Order:
        """Place futures order"""
        # Note: Hyperliquid doesn't have a separate reduce_only parameter
        # The reduce_only logic is handled internally by the exchange
        return await self.place_order(symbol, side, order_type, quantity, price, time_in_force)
    
    async def set_leverage(self, symbol: str, leverage: int) -> bool:
        """Set leverage for symbol"""
        if not self.client.exchange:
            raise ExchangeError("Not connected")
        
        try:
            # Hyperliquid uses 1x leverage by default and doesn't support custom leverage
            # This is a no-op for Hyperliquid
            logger.info(f"Hyperliquid uses 1x leverage by default, ignoring leverage setting for {symbol}")
            return True
        except Exception as e:
            logger.error(f"Failed to set leverage: {e}")
            raise ExchangeError(f"Failed to set leverage: {e}")
    
    async def get_funding_rates(self) -> List[FundingRate]:
        """Get all funding rates"""
        try:
            exchange_info = await self.get_exchange_info()
            funding_rates = []
            
            for symbol_info in exchange_info.get("symbols", []):
                symbol = symbol_info.get("symbol", "")
                if symbol:
                    try:
                        funding_rate = await self.get_funding_rate(symbol)
                        funding_rates.append(funding_rate)
                    except Exception as e:
                        logger.warning(f"Failed to get funding rate for {symbol}: {e}")
                        continue
            
            return funding_rates
            
        except Exception as e:
            logger.error(f"Failed to get funding rates: {e}")
            raise ExchangeError(f"Failed to get funding rates: {e}")
    
    async def get_futures_ticker(self, symbol: str) -> Any:
        """Get futures ticker"""
        return await self.get_ticker(symbol)
    
    async def get_futures_order_book(self, symbol: str, limit: int = 100) -> Any:
        """Get futures order book"""
        return await self.get_order_book(symbol, limit)
    
    async def get_futures_symbols(self) -> List[str]:
        """Get available futures symbols"""
        try:
            exchange_info = await self.get_exchange_info()
            symbols = []
            for symbol_info in exchange_info.get("symbols", []):
                symbol = symbol_info.get("symbol", "")
                if symbol:
                    symbols.append(symbol)
            return symbols
        except Exception as e:
            logger.error(f"Failed to get futures symbols: {e}")
            return []
    
    async def get_futures_trading_pairs(self) -> List[Dict[str, Any]]:
        """Get futures trading pairs"""
        try:
            exchange_info = await self.get_exchange_info()
            pairs = []
            for symbol_info in exchange_info.get("symbols", []):
                pairs.append({
                    "symbol": symbol_info.get("symbol", ""),
                    "base_asset": symbol_info.get("base_asset", ""),
                    "quote_asset": symbol_info.get("quote_asset", ""),
                    "status": symbol_info.get("status", "TRADING"),
                    "contract_type": "PERPETUAL"
                })
            return pairs
        except Exception as e:
            logger.error(f"Failed to get futures trading pairs: {e}")
            return []
    
    async def get_position_risk(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """Get position risk information"""
        try:
            positions = await self.get_futures_positions()
            
            if symbol:
                positions = [p for p in positions if p.symbol == symbol]
            
            total_pnl = sum(p.pnl for p in positions)
            total_margin = sum(p.margin for p in positions)
            total_notional = sum(p.size * p.mark_price for p in positions)
            
            return {
                "total_pnl": total_pnl,
                "total_margin": total_margin,
                "total_notional": total_notional,
                "margin_ratio": total_margin / total_notional if total_notional > 0 else 0,
                "positions": [
                    {
                        "symbol": p.symbol,
                        "side": p.side,
                        "size": p.size,
                        "entry_price": p.entry_price,
                        "mark_price": p.mark_price,
                        "pnl": p.pnl,
                        "percentage": p.percentage,
                        "margin": p.margin
                    }
                    for p in positions
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to get position risk: {e}")
            raise ExchangeError(f"Failed to get position risk: {e}")
    
    async def get_funding_rate_history(self, symbol: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get funding rate history"""
        try:
            # Hyperliquid doesn't provide historical funding rates in their API
            # We can only get the current funding rate
            current_funding = await self.get_funding_rate(symbol)
            
            return [{
                "symbol": current_funding.symbol,
                "funding_rate": current_funding.funding_rate,
                "funding_time": current_funding.funding_time,
                "next_funding_time": current_funding.next_funding_time
            }]
            
        except Exception as e:
            logger.error(f"Failed to get funding rate history: {e}")
            raise ExchangeError(f"Failed to get funding rate history: {e}")
