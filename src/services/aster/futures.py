"""
Aster futures trading service
"""
import logging
from decimal import Decimal
from typing import Any, Dict, List, Optional

from ..base import (
    FuturesService, Balance, Position, Order, FundingRate, 
    OrderSide, OrderType, TimeInForce, ExchangeError
)
from .client import AsterClient


logger = logging.getLogger(__name__)


class AsterFuturesService(FuturesService):
    """Aster futures trading service"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.client = AsterClient(config)
    
    async def connect(self) -> bool:
        """Connect to Aster futures"""
        return await self.client.connect()
    
    async def disconnect(self) -> None:
        """Disconnect from Aster futures"""
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
        try:
            params = {
                "symbol": symbol,
                "side": side.value,
                "type": order_type.value,
                "quantity": str(quantity),
                "timeInForce": time_in_force.value
            }
            
            if price:
                params["price"] = str(price)
            
            if reduce_only:
                params["reduceOnly"] = "true"
            
            data = await self.client._make_signed_request("POST", "/fapi/v1/order", params)
            
            # Create order object from response
            order_id = str(data.get("orderId", 0))
            
            return Order(
                order_id=order_id,
                symbol=symbol,
                side=side,
                order_type=order_type,
                quantity=quantity,
                price=price,
                status="NEW",
                filled_qty=Decimal(0),
                avg_price=None,
                time_in_force=time_in_force,
                created_at=int(self.client._get_timestamp()),
                updated_at=int(self.client._get_timestamp())
            )
            
        except Exception as e:
            logger.error(f"Failed to place futures order: {e}")
            raise ExchangeError(f"Failed to place futures order: {e}")
    
    async def set_leverage(self, symbol: str, leverage: int) -> bool:
        """Set leverage for symbol"""
        try:
            params = {
                "symbol": symbol,
                "leverage": leverage
            }
            
            data = await self.client._make_signed_request("POST", "/fapi/v1/leverage", params)
            return data.get("leverage") == leverage
            
        except Exception as e:
            logger.error(f"Failed to set leverage: {e}")
            raise ExchangeError(f"Failed to set leverage: {e}")
    
    async def get_funding_rates(self) -> List[FundingRate]:
        """Get all funding rates"""
        try:
            data = await self.client._make_public_request("GET", "/fapi/v1/premiumIndex")
            funding_rates = []
            
            for funding_data in data:
                symbol = funding_data.get("symbol", "")
                if symbol:
                    funding_rates.append(FundingRate(
                        symbol=symbol,
                        funding_rate=Decimal(str(funding_data.get("lastFundingRate", 0))),
                        funding_time=funding_data.get("nextFundingTime", 0),
                        next_funding_time=funding_data.get("nextFundingTime", 0)
                    ))
            
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
            params = {
                "symbol": symbol,
                "limit": limit
            }
            
            data = await self.client._make_public_request("GET", "/fapi/v1/fundingRate", params)
            
            history = []
            for funding_data in data:
                history.append({
                    "symbol": funding_data.get("symbol", ""),
                    "funding_rate": Decimal(str(funding_data.get("fundingRate", 0))),
                    "funding_time": funding_data.get("fundingTime", 0)
                })
            
            return history
            
        except Exception as e:
            logger.error(f"Failed to get funding rate history: {e}")
            raise ExchangeError(f"Failed to get funding rate history: {e}")
    
    async def get_income_history(self, symbol: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get income history (funding fees, realized PnL, etc.)"""
        try:
            params = {"limit": limit}
            if symbol:
                params["symbol"] = symbol
            
            data = await self.client._make_signed_request("GET", "/fapi/v1/income", params)
            
            history = []
            for income_data in data:
                history.append({
                    "symbol": income_data.get("symbol", ""),
                    "income_type": income_data.get("incomeType", ""),
                    "income": Decimal(str(income_data.get("income", 0))),
                    "asset": income_data.get("asset", ""),
                    "time": income_data.get("time", 0),
                    "info": income_data.get("info", "")
                })
            
            return history
            
        except Exception as e:
            logger.error(f"Failed to get income history: {e}")
            raise ExchangeError(f"Failed to get income history: {e}")
    
    async def get_force_orders(self, symbol: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get force orders (liquidations)"""
        try:
            params = {"limit": limit}
            if symbol:
                params["symbol"] = symbol
            
            data = await self.client._make_signed_request("GET", "/fapi/v1/forceOrders", params)
            
            force_orders = []
            for order_data in data:
                force_orders.append({
                    "symbol": order_data.get("symbol", ""),
                    "order_id": order_data.get("orderId", 0),
                    "side": order_data.get("side", ""),
                    "order_type": order_data.get("type", ""),
                    "quantity": Decimal(str(order_data.get("origQty", 0))),
                    "price": Decimal(str(order_data.get("price", 0))),
                    "avg_price": Decimal(str(order_data.get("avgPrice", 0))),
                    "order_status": order_data.get("orderStatus", ""),
                    "time_in_force": order_data.get("timeInForce", ""),
                    "time": order_data.get("time", 0)
                })
            
            return force_orders
            
        except Exception as e:
            logger.error(f"Failed to get force orders: {e}")
            raise ExchangeError(f"Failed to get force orders: {e}")
    
    async def get_account_trades(self, symbol: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get account trade history"""
        try:
            params = {"limit": limit}
            if symbol:
                params["symbol"] = symbol
            
            data = await self.client._make_signed_request("GET", "/fapi/v1/userTrades", params)
            
            trades = []
            for trade_data in data:
                trades.append({
                    "symbol": trade_data.get("symbol", ""),
                    "id": trade_data.get("id", 0),
                    "order_id": trade_data.get("orderId", 0),
                    "side": trade_data.get("side", ""),
                    "quantity": Decimal(str(trade_data.get("qty", 0))),
                    "price": Decimal(str(trade_data.get("price", 0))),
                    "quote_qty": Decimal(str(trade_data.get("quoteQty", 0))),
                    "commission": Decimal(str(trade_data.get("commission", 0))),
                    "commission_asset": trade_data.get("commissionAsset", ""),
                    "time": trade_data.get("time", 0),
                    "is_buyer": trade_data.get("isBuyer", False),
                    "is_maker": trade_data.get("isMaker", False)
                })
            
            return trades
            
        except Exception as e:
            logger.error(f"Failed to get account trades: {e}")
            raise ExchangeError(f"Failed to get account trades: {e}")
    
    async def change_margin_type(self, symbol: str, margin_type: str) -> bool:
        """Change margin type (ISOLATED or CROSSED)"""
        try:
            params = {
                "symbol": symbol,
                "marginType": margin_type.upper()
            }
            
            data = await self.client._make_signed_request("POST", "/fapi/v1/marginType", params)
            return data.get("code") == 200
            
        except Exception as e:
            logger.error(f"Failed to change margin type: {e}")
            raise ExchangeError(f"Failed to change margin type: {e}")
    
    async def change_position_margin(self, symbol: str, amount: Decimal, margin_type: int) -> Dict[str, Any]:
        """Change position margin"""
        try:
            params = {
                "symbol": symbol,
                "amount": str(amount),
                "type": margin_type  # 1: Add margin, 2: Reduce margin
            }
            
            data = await self.client._make_signed_request("POST", "/fapi/v1/positionMargin", params)
            return data
            
        except Exception as e:
            logger.error(f"Failed to change position margin: {e}")
            raise ExchangeError(f"Failed to change position margin: {e}")
