"""
Aster exchange client implementation
"""
import asyncio
import hmac
import hashlib
import logging
import time
import urllib.parse
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

import aiohttp

from ..base import (
    ExchangeService, Balance, Position, Order, Ticker, OrderBook, 
    FundingRate, SymbolInfo, OrderSide, OrderType, OrderStatus, 
    TimeInForce, ExchangeError, AuthenticationError, InvalidSymbolError
)


logger = logging.getLogger(__name__)


class AsterClient(ExchangeService):
    """Aster exchange client"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get("api_key")
        self.api_secret = config.get("api_secret")
        self.base_url = config.get("base_url", "https://fapi.asterdex.com")
        self.spot_base_url = config.get("spot_base_url", "https://sapi.asterdex.com")
        self.testnet = config.get("testnet", False)
        
        # Rate limiting
        self.rate_limit = config.get("rate_limit", {})
        self.requests_per_minute = self.rate_limit.get("requests_per_minute", 1200)
        self.weight_limit = self.rate_limit.get("weight_limit", 1200)
        
        # Time sync
        self.server_time_offset = 0
        self.last_time_sync = 0
        self.time_sync_interval = 60000  # 1 minute
        
        # Session
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def connect(self) -> bool:
        """Connect to Aster"""
        try:
            if not self.api_key or not self.api_secret:
                raise AuthenticationError("API key and secret required")
            
            # Create HTTP session
            self.session = aiohttp.ClientSession()
            
            # Sync server time
            await self._sync_server_time()
            
            # Verify connection by getting account info
            await self.get_account_info()
            
            self.is_connected = True
            logger.info("Connected to Aster successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Aster: {e}")
            raise AuthenticationError(f"Connection failed: {e}")
    
    async def disconnect(self) -> None:
        """Disconnect from Aster"""
        self.is_connected = False
        
        if self.session:
            await self.session.close()
            self.session = None
        
        logger.info("Disconnected from Aster")
    
    async def _sync_server_time(self):
        """Sync server time"""
        try:
            async with self.session.get(f"{self.base_url}/fapi/v1/time") as response:
                if response.status == 200:
                    data = await response.json()
                    server_time = data.get("serverTime", 0)
                    local_time = int(time.time() * 1000)
                    self.server_time_offset = server_time - local_time
                    self.last_time_sync = local_time
                    logger.debug(f"Server time synced, offset: {self.server_time_offset}ms")
        except Exception as e:
            logger.warning(f"Failed to sync server time: {e}")
    
    def _get_timestamp(self) -> int:
        """Get current timestamp with server offset"""
        return int(time.time() * 1000) + self.server_time_offset
    
    def _generate_signature(self, params_str: str) -> str:
        """Generate HMAC SHA256 signature"""
        return hmac.new(
            self.api_secret.encode("utf-8"),
            params_str.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
    
    async def _make_signed_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        is_spot: bool = False
    ) -> Dict[str, Any]:
        """Make signed request to Aster API"""
        if not self.session:
            raise ExchangeError("Not connected")
        
        # Sync time if needed
        current_time = int(time.time() * 1000)
        if current_time - self.last_time_sync > self.time_sync_interval:
            await self._sync_server_time()
        
        if params is None:
            params = {}
        
        # Add timestamp and recv window
        params["timestamp"] = self._get_timestamp()
        params["recvWindow"] = 5000
        
        # Create query string
        query_string = urllib.parse.urlencode(sorted(params.items()))
        signature = self._generate_signature(query_string)
        
        # Build URL
        base_url = self.spot_base_url if is_spot else self.base_url
        url = f"{base_url}{endpoint}?{query_string}&signature={signature}"
        
        headers = {"X-MBX-APIKEY": self.api_key}
        
        try:
            async with self.session.request(method, url, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    try:
                        error_data = await response.json()
                        error_code = error_data.get("code", response.status)
                        error_msg = error_data.get("msg", error_text)
                    except:
                        error_code = response.status
                        error_msg = error_text
                    
                    if error_code == -1021:  # Timestamp out of sync
                        await self._sync_server_time()
                        # Retry once
                        params["timestamp"] = self._get_timestamp()
                        query_string = urllib.parse.urlencode(sorted(params.items()))
                        signature = self._generate_signature(query_string)
                        url = f"{base_url}{endpoint}?{query_string}&signature={signature}"
                        
                        async with self.session.request(method, url, headers=headers) as retry_response:
                            if retry_response.status == 200:
                                return await retry_response.json()
                            else:
                                error_text = await retry_response.text()
                                raise ExchangeError(f"HTTP {retry_response.status}: {error_text}")
                    else:
                        raise ExchangeError(f"HTTP {response.status}: {error_msg}")
                        
        except aiohttp.ClientError as e:
            raise ExchangeError(f"Request failed: {e}")
    
    async def _make_public_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        is_spot: bool = False
    ) -> Dict[str, Any]:
        """Make public request to Aster API"""
        if not self.session:
            raise ExchangeError("Not connected")
        
        base_url = self.spot_base_url if is_spot else self.base_url
        url = f"{base_url}{endpoint}"
        
        try:
            async with self.session.request(method, url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise ExchangeError(f"HTTP {response.status}: {error_text}")
                    
        except aiohttp.ClientError as e:
            raise ExchangeError(f"Request failed: {e}")
    
    async def get_account_info(self) -> Dict[str, Any]:
        """Get account information"""
        try:
            data = await self._make_signed_request("GET", "/fapi/v1/account")
            return {
                "total_wallet_balance": data.get("totalWalletBalance", 0),
                "total_unrealized_pnl": data.get("totalUnrealizedProfit", 0),
                "total_margin_balance": data.get("totalMarginBalance", 0),
                "total_position_initial_margin": data.get("totalPositionInitialMargin", 0),
                "total_open_order_initial_margin": data.get("totalOpenOrderInitialMargin", 0),
                "total_cross_wallet_balance": data.get("totalCrossWalletBalance", 0),
                "total_cross_un_pnl": data.get("totalCrossUnPnl", 0),
                "available_balance": data.get("availableBalance", 0),
                "max_withdraw_amount": data.get("maxWithdrawAmount", 0)
            }
        except Exception as e:
            logger.error(f"Failed to get account info: {e}")
            raise ExchangeError(f"Failed to get account info: {e}")
    
    async def get_balances(self) -> List[Balance]:
        """Get account balances"""
        try:
            data = await self._make_signed_request("GET", "/fapi/v1/account")
            balances = []
            
            for asset in data.get("assets", []):
                asset_name = asset.get("asset", "")
                wallet_balance = Decimal(str(asset.get("walletBalance", 0)))
                cross_wallet_balance = Decimal(str(asset.get("crossWalletBalance", 0)))
                cross_un_pnl = Decimal(str(asset.get("crossUnPnl", 0)))
                
                # Calculate locked balance
                locked = wallet_balance - cross_wallet_balance
                free = cross_wallet_balance
                total = wallet_balance
                
                balances.append(Balance(
                    asset=asset_name,
                    free=free,
                    locked=locked,
                    total=total
                ))
            
            return balances
            
        except Exception as e:
            logger.error(f"Failed to get balances: {e}")
            raise ExchangeError(f"Failed to get balances: {e}")
    
    async def get_positions(self) -> List[Position]:
        """Get current positions"""
        try:
            data = await self._make_signed_request("GET", "/fapi/v1/account")
            positions = []
            
            # Debug logging
            # logger.info(f"Aster API response for positions: {data}")
            
            for position_data in data.get("positions", []):
                symbol = position_data.get("symbol", "")
                position_amt = Decimal(str(position_data.get("positionAmt", 0)))
                
                if position_amt == 0:  # Skip zero positions
                    continue
                
                entry_price = Decimal(str(position_data.get("entryPrice", 0)))
                mark_price = Decimal(str(position_data.get("markPrice", 0)))
                unrealized_pnl = Decimal(str(position_data.get("unrealizedPnl", 0)))
                percentage = Decimal(str(position_data.get("percentage", 0)))
                isolated_margin = Decimal(str(position_data.get("isolatedMargin", 0)))
                leverage = int(position_data.get("leverage", 1))
                
                # Try alternative field names for PnL
                if unrealized_pnl == 0:
                    unrealized_pnl = Decimal(str(position_data.get("unRealizedProfit", 0)))
                if unrealized_pnl == 0:
                    unrealized_pnl = Decimal(str(position_data.get("unrealizedProfit", 0)))
                if unrealized_pnl == 0:
                    unrealized_pnl = Decimal(str(position_data.get("pnl", 0)))
                
                # Debug logging for each position
                logger.info(f"Aster position raw data - Symbol: {symbol}, PositionAmt: {position_amt}, "
                           f"EntryPrice: {entry_price}, MarkPrice: {mark_price}, "
                           f"UnrealizedPnl: {unrealized_pnl}, Percentage: {percentage}")
                logger.info(f"Full position data: {position_data}")
                
                # If unrealized_pnl is 0, try to calculate it manually
                if unrealized_pnl == 0 and entry_price > 0 and mark_price > 0:
                    if position_amt > 0:  # Long position
                        calculated_pnl = (mark_price - entry_price) * abs(position_amt)
                    else:  # Short position
                        calculated_pnl = (entry_price - mark_price) * abs(position_amt)
                    
                    logger.info(f"Calculated PnL for {symbol}: {calculated_pnl} (Entry: {entry_price}, Mark: {mark_price}, Size: {abs(position_amt)})")
                    unrealized_pnl = calculated_pnl
                
                # Determine side
                side = "LONG" if position_amt > 0 else "SHORT"
                
                positions.append(Position(
                    symbol=symbol,
                    side=side,
                    size=abs(position_amt),
                    entry_price=entry_price,
                    mark_price=mark_price,
                    pnl=unrealized_pnl,
                    percentage=percentage,
                    margin=isolated_margin,
                    leverage=leverage
                ))
            
            return positions
            
        except Exception as e:
            logger.error(f"Failed to get positions: {e}")
            raise ExchangeError(f"Failed to get positions: {e}")
    
    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Order]:
        """Get open orders"""
        try:
            params = {}
            if symbol:
                params["symbol"] = symbol
            
            data = await self._make_signed_request("GET", "/fapi/v1/openOrders", params)
            orders = []
            
            for order_data in data:
                order_id = str(order_data.get("orderId", 0))
                order_symbol = order_data.get("symbol", "")
                side = OrderSide.BUY if order_data.get("side") == "BUY" else OrderSide.SELL
                
                # Map order type
                order_type_map = {
                    "MARKET": OrderType.MARKET,
                    "LIMIT": OrderType.LIMIT,
                    "STOP": OrderType.STOP_LOSS,
                    "TAKE_PROFIT": OrderType.TAKE_PROFIT,
                    "TRAILING_STOP": OrderType.TRAILING_STOP
                }
                order_type = order_type_map.get(order_data.get("type", "LIMIT"), OrderType.LIMIT)
                
                quantity = Decimal(str(order_data.get("origQty", 0)))
                price = Decimal(str(order_data.get("price", 0))) if order_data.get("price") else None
                
                # Map order status
                status_map = {
                    "NEW": OrderStatus.NEW,
                    "PARTIALLY_FILLED": OrderStatus.PARTIALLY_FILLED,
                    "FILLED": OrderStatus.FILLED,
                    "CANCELED": OrderStatus.CANCELED,
                    "REJECTED": OrderStatus.REJECTED,
                    "EXPIRED": OrderStatus.EXPIRED
                }
                status = status_map.get(order_data.get("status", "NEW"), OrderStatus.NEW)
                
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
            logger.error(f"Failed to get open orders: {e}")
            raise ExchangeError(f"Failed to get open orders: {e}")
    
    async def get_order(self, order_id: str, symbol: str) -> Order:
        """Get specific order"""
        try:
            params = {
                "symbol": symbol,
                "orderId": order_id
            }
            
            data = await self._make_signed_request("GET", "/fapi/v1/order", params)
            
            # Convert to Order object (similar to get_open_orders)
            order_id = str(data.get("orderId", 0))
            order_symbol = data.get("symbol", "")
            side = OrderSide.BUY if data.get("side") == "BUY" else OrderSide.SELL
            
            order_type_map = {
                "MARKET": OrderType.MARKET,
                "LIMIT": OrderType.LIMIT,
                "STOP": OrderType.STOP_LOSS,
                "TAKE_PROFIT": OrderType.TAKE_PROFIT,
                "TRAILING_STOP": OrderType.TRAILING_STOP
            }
            order_type = order_type_map.get(data.get("type", "LIMIT"), OrderType.LIMIT)
            
            quantity = Decimal(str(data.get("origQty", 0)))
            price = Decimal(str(data.get("price", 0))) if data.get("price") else None
            
            status_map = {
                "NEW": OrderStatus.NEW,
                "PARTIALLY_FILLED": OrderStatus.PARTIALLY_FILLED,
                "FILLED": OrderStatus.FILLED,
                "CANCELED": OrderStatus.CANCELED,
                "REJECTED": OrderStatus.REJECTED,
                "EXPIRED": OrderStatus.EXPIRED
            }
            status = status_map.get(data.get("status", "NEW"), OrderStatus.NEW)
            
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
            logger.error(f"Failed to get order: {e}")
            raise ExchangeError(f"Failed to get order: {e}")
    
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
        try:
            # Handle both enum and string inputs
            side_str = side.value if hasattr(side, 'value') else str(side).upper()
            order_type_str = order_type.value if hasattr(order_type, 'value') else str(order_type).upper()
            
            params = {
                "symbol": symbol,
                "side": side_str,
                "type": order_type_str,
                "quantity": str(quantity)
            }
            
            # Only add timeInForce for limit orders
            if order_type_str == "LIMIT":
                time_in_force_str = time_in_force.value if hasattr(time_in_force, 'value') else str(time_in_force)
                params["timeInForce"] = time_in_force_str
            
            if price:
                params["price"] = str(price)
            
            if client_order_id:
                params["newClientOrderId"] = client_order_id
            
            data = await self._make_signed_request("POST", "/fapi/v1/order", params)
            
            # Create order object from response
            order_id = str(data.get("orderId", 0))
            
            from ..base import OrderStatus
            
            return Order(
                order_id=order_id,
                symbol=symbol,
                side=side,
                order_type=order_type,
                quantity=quantity,
                price=price,
                status=OrderStatus.NEW,
                filled_qty=Decimal(0),
                avg_price=None,
                time_in_force=time_in_force,
                created_at=int(time.time() * 1000),
                updated_at=int(time.time() * 1000),
                client_order_id=client_order_id
            )
            
        except Exception as e:
            logger.error(f"Failed to place order: {e}")
            raise ExchangeError(f"Failed to place order: {e}")
    
    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        """Cancel an order"""
        try:
            params = {
                "symbol": symbol,
                "orderId": order_id
            }
            
            data = await self._make_signed_request("DELETE", "/fapi/v1/order", params)
            return data.get("status") == "CANCELED"
            
        except Exception as e:
            logger.error(f"Failed to cancel order: {e}")
            raise ExchangeError(f"Failed to cancel order: {e}")
    
    async def cancel_all_orders(self, symbol: Optional[str] = None) -> bool:
        """Cancel all orders"""
        try:
            params = {}
            if symbol:
                params["symbol"] = symbol
            
            data = await self._make_signed_request("DELETE", "/fapi/v1/allOpenOrders", params)
            return data.get("code") == 200
            
        except Exception as e:
            logger.error(f"Failed to cancel all orders: {e}")
            raise ExchangeError(f"Failed to cancel all orders: {e}")
    
    async def get_ticker(self, symbol: str) -> Ticker:
        """Get ticker information"""
        try:
            params = {"symbol": symbol}
            data = await self._make_public_request("GET", "/fapi/v1/ticker/24hr", params)
            
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
            logger.error(f"Failed to get ticker: {e}")
            raise ExchangeError(f"Failed to get ticker: {e}")
    
    async def get_order_book(self, symbol: str, limit: int = 100) -> OrderBook:
        """Get order book"""
        try:
            params = {
                "symbol": symbol,
                "limit": limit
            }
            
            data = await self._make_public_request("GET", "/fapi/v1/depth", params)
            
            bids = [[Decimal(str(bid[0])), Decimal(str(bid[1]))] for bid in data.get("bids", [])]
            asks = [[Decimal(str(ask[0])), Decimal(str(ask[1]))] for ask in data.get("asks", [])]
            
            return OrderBook(
                symbol=symbol,
                bids=bids,
                asks=asks,
                timestamp=data.get("lastUpdateId", 0)
            )
            
        except Exception as e:
            logger.error(f"Failed to get order book: {e}")
            raise ExchangeError(f"Failed to get order book: {e}")
    
    async def get_funding_rate(self, symbol: str) -> FundingRate:
        """Get funding rate"""
        try:
            params = {"symbol": symbol}
            data = await self._make_public_request("GET", "/fapi/v1/premiumIndex", params)
            
            return FundingRate(
                symbol=symbol,
                funding_rate=Decimal(str(data.get("lastFundingRate", 0))),
                funding_time=data.get("nextFundingTime", 0),
                next_funding_time=data.get("nextFundingTime", 0)
            )
            
        except Exception as e:
            logger.error(f"Failed to get funding rate: {e}")
            raise ExchangeError(f"Failed to get funding rate: {e}")
    
    async def get_symbol_info(self, symbol: str) -> SymbolInfo:
        """Get symbol information"""
        try:
            data = await self._make_public_request("GET", "/fapi/v1/exchangeInfo")
            
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
                    
                    return SymbolInfo(
                        symbol=symbol,
                        base_asset=base_asset,
                        quote_asset=quote_asset,
                        tick_size=tick_size,
                        step_size=step_size,
                        min_qty=min_qty,
                        min_notional=min_notional,
                        is_spot=False,
                        is_futures=True
                    )
            
            raise InvalidSymbolError(f"Symbol {symbol} not found")
            
        except Exception as e:
            logger.error(f"Failed to get symbol info: {e}")
            raise ExchangeError(f"Failed to get symbol info: {e}")
    
    async def get_exchange_info(self) -> Dict[str, Any]:
        """Get exchange information"""
        try:
            data = await self._make_public_request("GET", "/fapi/v1/exchangeInfo")
            
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
                "server_time": data.get("serverTime", int(time.time() * 1000)),
                "symbols": symbols
            }
            
        except Exception as e:
            logger.error(f"Failed to get exchange info: {e}")
            raise ExchangeError(f"Failed to get exchange info: {e}")
