"""
Aster spot trading service
"""
import logging
from decimal import Decimal
from typing import Any, Dict, List, Optional

from ..base import SpotService, Balance, Order, OrderSide, OrderType, TimeInForce, ExchangeError
from .client import AsterClient


logger = logging.getLogger(__name__)


class AsterSpotService(SpotService):
    """Aster spot trading service"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.client = AsterClient(config)
    
    async def connect(self) -> bool:
        """Connect to Aster spot"""
        return await self.client.connect()
    
    async def disconnect(self) -> None:
        """Disconnect from Aster spot"""
        await self.client.disconnect()
    
    async def get_account_info(self) -> Dict[str, Any]:
        """Get account information"""
        return await self.client.get_account_info()
    
    async def get_balances(self) -> List[Balance]:
        """Get account balances"""
        return await self.get_spot_balances()
    
    async def get_positions(self) -> List[Any]:
        """Get current positions (empty for spot)"""
        return []  # Spot trading doesn't have positions
    
    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Order]:
        """Get open orders"""
        return await self._get_spot_open_orders(symbol)
    
    async def get_order(self, order_id: str, symbol: str) -> Order:
        """Get specific order"""
        return await self._get_spot_order(order_id, symbol)
    
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
        return await self._place_spot_order(symbol, side, order_type, quantity, price, time_in_force, client_order_id)
    
    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        """Cancel an order"""
        return await self._cancel_spot_order(order_id, symbol)
    
    async def cancel_all_orders(self, symbol: Optional[str] = None) -> bool:
        """Cancel all orders"""
        return await self._cancel_all_spot_orders(symbol)
    
    async def get_ticker(self, symbol: str) -> Any:
        """Get ticker information"""
        return await self._get_spot_ticker(symbol)
    
    async def get_order_book(self, symbol: str, limit: int = 100) -> Any:
        """Get order book"""
        return await self._get_spot_order_book(symbol, limit)
    
    async def get_funding_rate(self, symbol: str) -> Any:
        """Get funding rate (not applicable for spot)"""
        raise ExchangeError("Funding rate not applicable for spot trading")
    
    async def get_symbol_info(self, symbol: str) -> Any:
        """Get symbol information"""
        return await self._get_spot_symbol_info(symbol)
    
    async def get_exchange_info(self) -> Dict[str, Any]:
        """Get exchange information"""
        return await self._get_spot_exchange_info()
    
    async def get_spot_balances(self) -> List[Balance]:
        """Get spot balances"""
        try:
            data = await self.client._make_signed_request("GET", "/api/v1/account", is_spot=True)
            balances = []
            
            for balance_data in data.get("balances", []):
                asset = balance_data.get("asset", "")
                free = Decimal(str(balance_data.get("free", 0)))
                locked = Decimal(str(balance_data.get("locked", 0)))
                total = free + locked
                
                if total > 0:  # Only include non-zero balances
                    balances.append(Balance(
                        asset=asset,
                        free=free,
                        locked=locked,
                        total=total
                    ))
            
            return balances
            
        except Exception as e:
            logger.error(f"Failed to get spot balances: {e}")
            raise ExchangeError(f"Failed to get spot balances: {e}")
    
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
        return await self._place_spot_order(symbol, side, order_type, quantity, price, time_in_force)
    
    async def _get_spot_open_orders(self, symbol: Optional[str] = None) -> List[Order]:
        """Get spot open orders"""
        try:
            params = {}
            if symbol:
                params["symbol"] = symbol
            
            data = await self.client._make_signed_request("GET", "/api/v1/openOrders", params, is_spot=True)
            orders = []
            
            for order_data in data:
                order_id = str(order_data.get("orderId", 0))
                order_symbol = order_data.get("symbol", "")
                side = OrderSide.BUY if order_data.get("side") == "BUY" else OrderSide.SELL
                
                # Map order type
                order_type_map = {
                    "MARKET": OrderType.MARKET,
                    "LIMIT": OrderType.LIMIT,
                    "STOP_LOSS": OrderType.STOP_LOSS,
                    "TAKE_PROFIT": OrderType.TAKE_PROFIT,
                    "TRAILING_STOP": OrderType.TRAILING_STOP
                }
                order_type = order_type_map.get(order_data.get("type", "LIMIT"), OrderType.LIMIT)
                
                quantity = Decimal(str(order_data.get("origQty", 0)))
                price = Decimal(str(order_data.get("price", 0))) if order_data.get("price") else None
                
                # Map order status
                status_map = {
                    "NEW": "NEW",
                    "PARTIALLY_FILLED": "PARTIALLY_FILLED",
                    "FILLED": "FILLED",
                    "CANCELED": "CANCELED",
                    "REJECTED": "REJECTED",
                    "EXPIRED": "EXPIRED"
                }
                status = status_map.get(order_data.get("status", "NEW"), "NEW")
                
                filled_qty = Decimal(str(order_data.get("executedQty", 0)))
                avg_price = Decimal(str(order_data.get("avgPrice", 0))) if order_data.get("avgPrice") else None
                
                # Map time in force
                tif_map = {
                    "GTC": TimeInForce.GTC,
                    "IOC": TimeInForce.IOC,
                    "FOK": TimeInForce.FOK
                }
                time_in_force = tif_map.get(order_data.get("timeInForce", "GTC"), TimeInForce.GTC)
                
                orders.append(Order(
                    order_id=order_id,
                    symbol=order_symbol,
                    side=side,
                    order_type=order_type,
                    quantity=quantity,
                    price=price,
                    status=status,
                    filled_qty=filled_qty,
                    avg_price=avg_price,
                    time_in_force=time_in_force,
                    created_at=order_data.get("time", 0),
                    updated_at=order_data.get("updateTime", 0),
                    client_order_id=order_data.get("clientOrderId")
                ))
            
            return orders
            
        except Exception as e:
            logger.error(f"Failed to get spot open orders: {e}")
            raise ExchangeError(f"Failed to get spot open orders: {e}")
    
    async def _get_spot_order(self, order_id: str, symbol: str) -> Order:
        """Get specific spot order"""
        try:
            params = {
                "symbol": symbol,
                "orderId": order_id
            }
            
            data = await self.client._make_signed_request("GET", "/api/v1/order", params, is_spot=True)
            
            # Convert to Order object (similar to _get_spot_open_orders)
            order_id = str(data.get("orderId", 0))
            order_symbol = data.get("symbol", "")
            side = OrderSide.BUY if data.get("side") == "BUY" else OrderSide.SELL
            
            order_type_map = {
                "MARKET": OrderType.MARKET,
                "LIMIT": OrderType.LIMIT,
                "STOP_LOSS": OrderType.STOP_LOSS,
                "TAKE_PROFIT": OrderType.TAKE_PROFIT,
                "TRAILING_STOP": OrderType.TRAILING_STOP
            }
            order_type = order_type_map.get(data.get("type", "LIMIT"), OrderType.LIMIT)
            
            quantity = Decimal(str(data.get("origQty", 0)))
            price = Decimal(str(data.get("price", 0))) if data.get("price") else None
            
            status_map = {
                "NEW": "NEW",
                "PARTIALLY_FILLED": "PARTIALLY_FILLED",
                "FILLED": "FILLED",
                "CANCELED": "CANCELED",
                "REJECTED": "REJECTED",
                "EXPIRED": "EXPIRED"
            }
            status = status_map.get(data.get("status", "NEW"), "NEW")
            
            filled_qty = Decimal(str(data.get("executedQty", 0)))
            avg_price = Decimal(str(data.get("avgPrice", 0))) if data.get("avgPrice") else None
            
            tif_map = {
                "GTC": TimeInForce.GTC,
                "IOC": TimeInForce.IOC,
                "FOK": TimeInForce.FOK
            }
            time_in_force = tif_map.get(data.get("timeInForce", "GTC"), TimeInForce.GTC)
            
            return Order(
                order_id=order_id,
                symbol=order_symbol,
                side=side,
                order_type=order_type,
                quantity=quantity,
                price=price,
                status=status,
                filled_qty=filled_qty,
                avg_price=avg_price,
                time_in_force=time_in_force,
                created_at=data.get("time", 0),
                updated_at=data.get("updateTime", 0),
                client_order_id=data.get("clientOrderId")
            )
            
        except Exception as e:
            logger.error(f"Failed to get spot order: {e}")
            raise ExchangeError(f"Failed to get spot order: {e}")
    
    async def _place_spot_order(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        quantity: Decimal,
        price: Optional[Decimal] = None,
        time_in_force: TimeInForce = TimeInForce.GTC,
        client_order_id: Optional[str] = None
    ) -> Order:
        """Place spot order"""
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
            
            if client_order_id:
                params["newClientOrderId"] = client_order_id
            
            data = await self.client._make_signed_request("POST", "/api/v1/order", params, is_spot=True)
            
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
                updated_at=int(self.client._get_timestamp()),
                client_order_id=client_order_id
            )
            
        except Exception as e:
            logger.error(f"Failed to place spot order: {e}")
            raise ExchangeError(f"Failed to place spot order: {e}")
    
    async def _cancel_spot_order(self, order_id: str, symbol: str) -> bool:
        """Cancel spot order"""
        try:
            params = {
                "symbol": symbol,
                "orderId": order_id
            }
            
            data = await self.client._make_signed_request("DELETE", "/api/v1/order", params, is_spot=True)
            return data.get("status") == "CANCELED"
            
        except Exception as e:
            logger.error(f"Failed to cancel spot order: {e}")
            raise ExchangeError(f"Failed to cancel spot order: {e}")
    
    async def _cancel_all_spot_orders(self, symbol: Optional[str] = None) -> bool:
        """Cancel all spot orders"""
        try:
            params = {}
            if symbol:
                params["symbol"] = symbol
            
            data = await self.client._make_signed_request("DELETE", "/api/v1/openOrders", params, is_spot=True)
            return data.get("code") == 200
            
        except Exception as e:
            logger.error(f"Failed to cancel all spot orders: {e}")
            raise ExchangeError(f"Failed to cancel all spot orders: {e}")
    
    async def _get_spot_ticker(self, symbol: str) -> Any:
        """Get spot ticker"""
        try:
            params = {"symbol": symbol}
            data = await self.client._make_public_request("GET", "/api/v1/ticker/24hr", params, is_spot=True)
            
            from ..base import Ticker
            return Ticker(
                symbol=symbol,
                bid_price=Decimal(str(data.get("bidPrice", 0))),
                ask_price=Decimal(str(data.get("askPrice", 0))),
                last_price=Decimal(str(data.get("lastPrice", 0))),
                volume=Decimal(str(data.get("volume", 0))),
                price_change=Decimal(str(data.get("priceChange", 0))),
                price_change_percent=Decimal(str(data.get("priceChangePercent", 0))),
                high_price=Decimal(str(data.get("highPrice", 0))),
                low_price=Decimal(str(data.get("lowPrice", 0))),
                timestamp=data.get("closeTime", 0)
            )
            
        except Exception as e:
            logger.error(f"Failed to get spot ticker: {e}")
            raise ExchangeError(f"Failed to get spot ticker: {e}")
    
    async def _get_spot_order_book(self, symbol: str, limit: int = 100) -> Any:
        """Get spot order book"""
        try:
            params = {
                "symbol": symbol,
                "limit": limit
            }
            
            data = await self.client._make_public_request("GET", "/api/v1/depth", params, is_spot=True)
            
            from ..base import OrderBook
            bids = [[Decimal(str(bid[0])), Decimal(str(bid[1]))] for bid in data.get("bids", [])]
            asks = [[Decimal(str(ask[0])), Decimal(str(ask[1]))] for ask in data.get("asks", [])]
            
            return OrderBook(
                symbol=symbol,
                bids=bids,
                asks=asks,
                timestamp=data.get("lastUpdateId", 0)
            )
            
        except Exception as e:
            logger.error(f"Failed to get spot order book: {e}")
            raise ExchangeError(f"Failed to get spot order book: {e}")
    
    async def _get_spot_symbol_info(self, symbol: str) -> Any:
        """Get spot symbol information"""
        try:
            data = await self.client._make_public_request("GET", "/api/v1/exchangeInfo", is_spot=True)
            
            for symbol_data in data.get("symbols", []):
                if symbol_data.get("symbol") == symbol:
                    filters = symbol_data.get("filters", [])
                    
                    tick_size = Decimal("0.01")
                    step_size = Decimal("0.001")
                    min_qty = Decimal("0.001")
                    min_notional = Decimal("5.0")
                    
                    for filter_data in filters:
                        filter_type = filter_data.get("filterType")
                        if filter_type == "PRICE_FILTER":
                            tick_size = Decimal(str(filter_data.get("tickSize", "0.01")))
                        elif filter_type == "LOT_SIZE":
                            step_size = Decimal(str(filter_data.get("stepSize", "0.001")))
                            min_qty = Decimal(str(filter_data.get("minQty", "0.001")))
                        elif filter_type in ("MIN_NOTIONAL", "NOTIONAL"):
                            min_notional = Decimal(str(filter_data.get("minNotional", "5.0")))
                    
                    base_asset = symbol_data.get("baseAsset", "")
                    quote_asset = symbol_data.get("quoteAsset", "")
                    
                    from ..base import SymbolInfo
                    return SymbolInfo(
                        symbol=symbol,
                        base_asset=base_asset,
                        quote_asset=quote_asset,
                        tick_size=tick_size,
                        step_size=step_size,
                        min_qty=min_qty,
                        min_notional=min_notional,
                        is_spot=True,
                        is_futures=False
                    )
            
            raise ExchangeError(f"Symbol {symbol} not found")
            
        except Exception as e:
            logger.error(f"Failed to get spot symbol info: {e}")
            raise ExchangeError(f"Failed to get spot symbol info: {e}")
    
    async def _get_spot_exchange_info(self) -> Dict[str, Any]:
        """Get spot exchange information"""
        try:
            data = await self.client._make_public_request("GET", "/api/v1/exchangeInfo", is_spot=True)
            
            symbols = []
            for symbol_data in data.get("symbols", []):
                symbols.append({
                    "symbol": symbol_data.get("symbol", ""),
                    "base_asset": symbol_data.get("baseAsset", ""),
                    "quote_asset": symbol_data.get("quoteAsset", ""),
                    "status": symbol_data.get("status", "TRADING")
                })
            
            return {
                "timezone": "UTC",
                "server_time": data.get("serverTime", int(self.client._get_timestamp())),
                "symbols": symbols
            }
            
        except Exception as e:
            logger.error(f"Failed to get spot exchange info: {e}")
            raise ExchangeError(f"Failed to get spot exchange info: {e}")
    
    async def get_spot_ticker(self, symbol: str) -> Any:
        """Get spot ticker"""
        return await self._get_spot_ticker(symbol)
    
    async def get_spot_order_book(self, symbol: str, limit: int = 100) -> Any:
        """Get spot order book"""
        return await self._get_spot_order_book(symbol, limit)
    
    async def get_spot_symbols(self) -> List[str]:
        """Get available spot symbols"""
        try:
            exchange_info = await self._get_spot_exchange_info()
            symbols = []
            for symbol_info in exchange_info.get("symbols", []):
                symbol = symbol_info.get("symbol", "")
                if symbol:
                    symbols.append(symbol)
            return symbols
        except Exception as e:
            logger.error(f"Failed to get spot symbols: {e}")
            return []
    
    async def get_spot_trading_pairs(self) -> List[Dict[str, Any]]:
        """Get spot trading pairs"""
        try:
            exchange_info = await self._get_spot_exchange_info()
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
