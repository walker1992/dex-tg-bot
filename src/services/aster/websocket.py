"""
Aster WebSocket service
"""
import asyncio
import json
import logging
import websockets
from typing import Any, Dict, List, Optional, Callable

from ..base import WebSocketService, Ticker, OrderBook, ExchangeError


logger = logging.getLogger(__name__)


class AsterWebSocketService(WebSocketService):
    """Aster WebSocket service"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.ws_url = config.get("ws_url", "wss://fstream.asterdex.com/ws")
        self.spot_ws_url = config.get("spot_ws_url", "wss://stream.asterdex.com/ws")
        self.api_key = config.get("api_key")
        self.api_secret = config.get("api_secret")
        self.websocket = None
        self.subscriptions: Dict[str, str] = {}
        self.reconnect_interval = 5
        self.max_reconnect_attempts = 10
        self.reconnect_attempts = 0
        self.listen_key = None
    
    async def connect(self) -> bool:
        """Connect to Aster WebSocket"""
        try:
            self.websocket = await websockets.connect(self.ws_url)
            self.is_connected = True
            self.reconnect_attempts = 0
            
            # Start message handler
            asyncio.create_task(self._message_handler())
            
            logger.info("Connected to Aster WebSocket")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Aster WebSocket: {e}")
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from Aster WebSocket"""
        self.is_connected = False
        
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
        
        # Close user data stream if exists
        if self.listen_key:
            await self._close_user_data_stream()
        
        self.subscriptions.clear()
        logger.info("Disconnected from Aster WebSocket")
    
    async def subscribe_ticker(self, symbol: str, callback: Callable) -> bool:
        """Subscribe to ticker updates"""
        if not self.websocket or not self.is_connected:
            raise ExchangeError("WebSocket not connected")
        
        try:
            subscription_id = f"ticker_{symbol}"
            self.subscriptions[subscription_id] = symbol
            self.callbacks[subscription_id] = callback
            
            # Subscribe to 24hr ticker stream
            stream_name = f"{symbol.lower()}@ticker"
            subscribe_msg = {
                "method": "SUBSCRIBE",
                "params": [stream_name],
                "id": 1
            }
            
            await self.websocket.send(json.dumps(subscribe_msg))
            logger.info(f"Subscribed to ticker updates for {symbol}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to subscribe to ticker: {e}")
            return False
    
    async def subscribe_order_book(self, symbol: str, callback: Callable) -> bool:
        """Subscribe to order book updates"""
        if not self.websocket or not self.is_connected:
            raise ExchangeError("WebSocket not connected")
        
        try:
            subscription_id = f"orderbook_{symbol}"
            self.subscriptions[subscription_id] = symbol
            self.callbacks[subscription_id] = callback
            
            # Subscribe to depth stream
            stream_name = f"{symbol.lower()}@depth"
            subscribe_msg = {
                "method": "SUBSCRIBE",
                "params": [stream_name],
                "id": 1
            }
            
            await self.websocket.send(json.dumps(subscribe_msg))
            logger.info(f"Subscribed to order book updates for {symbol}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to subscribe to order book: {e}")
            return False
    
    async def subscribe_user_data(self, callback: Callable) -> bool:
        """Subscribe to user data updates"""
        if not self.api_key or not self.api_secret:
            raise ExchangeError("API credentials required for user data subscription")
        
        try:
            # Create user data stream
            self.listen_key = await self._create_user_data_stream()
            
            if not self.listen_key:
                raise ExchangeError("Failed to create user data stream")
            
            subscription_id = "user_data"
            self.subscriptions[subscription_id] = "user_data"
            self.callbacks[subscription_id] = callback
            
            # Connect to user data stream
            user_data_ws_url = f"{self.ws_url}/{self.listen_key}"
            user_websocket = await websockets.connect(user_data_ws_url)
            
            # Start user data message handler
            asyncio.create_task(self._user_data_message_handler(user_websocket))
            
            logger.info("Subscribed to user data updates")
            return True
            
        except Exception as e:
            logger.error(f"Failed to subscribe to user data: {e}")
            return False
    
    async def unsubscribe(self, stream: str) -> bool:
        """Unsubscribe from stream"""
        if not self.websocket or not self.is_connected:
            raise ExchangeError("WebSocket not connected")
        
        try:
            if stream in self.subscriptions:
                symbol = self.subscriptions[stream]
                
                # Determine stream type and unsubscribe
                if stream.startswith("ticker_"):
                    stream_name = f"{symbol.lower()}@ticker"
                elif stream.startswith("orderbook_"):
                    stream_name = f"{symbol.lower()}@depth"
                else:
                    return False
                
                unsubscribe_msg = {
                    "method": "UNSUBSCRIBE",
                    "params": [stream_name],
                    "id": 1
                }
                
                await self.websocket.send(json.dumps(unsubscribe_msg))
                
                # Remove from subscriptions and callbacks
                del self.subscriptions[stream]
                if stream in self.callbacks:
                    del self.callbacks[stream]
                
                logger.info(f"Unsubscribed from {stream}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to unsubscribe from {stream}: {e}")
            return False
    
    async def _create_user_data_stream(self) -> Optional[str]:
        """Create user data stream"""
        try:
            import aiohttp
            import hmac
            import hashlib
            import urllib.parse
            import time
            
            # Create session for REST API call
            async with aiohttp.ClientSession() as session:
                # Generate signature
                timestamp = int(time.time() * 1000)
                params = {"timestamp": timestamp}
                query_string = urllib.parse.urlencode(params)
                signature = hmac.new(
                    self.api_secret.encode("utf-8"),
                    query_string.encode("utf-8"),
                    hashlib.sha256
                ).hexdigest()
                
                url = f"https://fapi.asterdex.com/fapi/v1/listenKey?{query_string}&signature={signature}"
                headers = {"X-MBX-APIKEY": self.api_key}
                
                async with session.post(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("listenKey")
                    else:
                        logger.error(f"Failed to create user data stream: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error creating user data stream: {e}")
            return None
    
    async def _close_user_data_stream(self):
        """Close user data stream"""
        if not self.listen_key:
            return
        
        try:
            import aiohttp
            import hmac
            import hashlib
            import urllib.parse
            import time
            
            async with aiohttp.ClientSession() as session:
                timestamp = int(time.time() * 1000)
                params = {"timestamp": timestamp, "listenKey": self.listen_key}
                query_string = urllib.parse.urlencode(params)
                signature = hmac.new(
                    self.api_secret.encode("utf-8"),
                    query_string.encode("utf-8"),
                    hashlib.sha256
                ).hexdigest()
                
                url = f"https://fapi.asterdex.com/fapi/v1/listenKey?{query_string}&signature={signature}"
                headers = {"X-MBX-APIKEY": self.api_key}
                
                async with session.delete(url, headers=headers) as response:
                    if response.status == 200:
                        logger.info("User data stream closed")
                    else:
                        logger.warning(f"Failed to close user data stream: {response.status}")
                        
        except Exception as e:
            logger.error(f"Error closing user data stream: {e}")
        finally:
            self.listen_key = None
    
    async def _message_handler(self):
        """Handle incoming WebSocket messages"""
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    await self._process_message(data)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse WebSocket message: {e}")
                except Exception as e:
                    logger.error(f"Error processing WebSocket message: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.warning("WebSocket connection closed")
            await self._handle_reconnect()
        except Exception as e:
            logger.error(f"WebSocket message handler error: {e}")
            await self._handle_reconnect()
    
    async def _user_data_message_handler(self, websocket):
        """Handle user data WebSocket messages"""
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    if "user_data" in self.callbacks:
                        await self.callbacks["user_data"](data)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse user data message: {e}")
                except Exception as e:
                    logger.error(f"Error processing user data message: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.warning("User data WebSocket connection closed")
        except Exception as e:
            logger.error(f"User data WebSocket message handler error: {e}")
        finally:
            await websocket.close()
    
    async def _process_message(self, data: Dict[str, Any]):
        """Process incoming WebSocket message"""
        try:
            if "stream" in data:
                stream = data["stream"]
                stream_data = data.get("data", {})
                
                if "@ticker" in stream:
                    await self._handle_ticker_update(stream, stream_data)
                elif "@depth" in stream:
                    await self._handle_depth_update(stream, stream_data)
                elif "@trade" in stream:
                    await self._handle_trade_update(stream, stream_data)
                    
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    async def _handle_ticker_update(self, stream: str, data: Dict[str, Any]):
        """Handle ticker updates"""
        try:
            symbol = stream.split("@")[0].upper()
            
            ticker = Ticker(
                symbol=symbol,
                bid_price=float(data.get("b", 0)),
                ask_price=float(data.get("a", 0)),
                last_price=float(data.get("c", 0)),
                volume=float(data.get("v", 0)),
                price_change=float(data.get("P", 0)),
                price_change_percent=float(data.get("P", 0)),
                high_price=float(data.get("h", 0)),
                low_price=float(data.get("l", 0)),
                timestamp=int(data.get("E", 0))
            )
            
            # Call ticker callback
            ticker_key = f"ticker_{symbol}"
            if ticker_key in self.callbacks:
                await self.callbacks[ticker_key](ticker)
                
        except Exception as e:
            logger.error(f"Error handling ticker update: {e}")
    
    async def _handle_depth_update(self, stream: str, data: Dict[str, Any]):
        """Handle depth updates"""
        try:
            symbol = stream.split("@")[0].upper()
            
            bids = [[float(bid[0]), float(bid[1])] for bid in data.get("b", [])]
            asks = [[float(ask[0]), float(ask[1])] for ask in data.get("a", [])]
            
            order_book = OrderBook(
                symbol=symbol,
                bids=bids,
                asks=asks,
                timestamp=int(data.get("E", 0))
            )
            
            # Call order book callback
            orderbook_key = f"orderbook_{symbol}"
            if orderbook_key in self.callbacks:
                await self.callbacks[orderbook_key](order_book)
                
        except Exception as e:
            logger.error(f"Error handling depth update: {e}")
    
    async def _handle_trade_update(self, stream: str, data: Dict[str, Any]):
        """Handle trade updates"""
        try:
            # Process trade data if needed
            pass
            
        except Exception as e:
            logger.error(f"Error handling trade update: {e}")
    
    async def _handle_reconnect(self):
        """Handle WebSocket reconnection"""
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            logger.error("Max reconnection attempts reached")
            self.is_connected = False
            return
        
        self.reconnect_attempts += 1
        logger.info(f"Attempting to reconnect ({self.reconnect_attempts}/{self.max_reconnect_attempts})")
        
        await asyncio.sleep(self.reconnect_interval)
        
        try:
            await self.connect()
            
            # Resubscribe to all previous subscriptions
            for subscription_id, symbol in self.subscriptions.items():
                if subscription_id.startswith("ticker_"):
                    await self.subscribe_ticker(symbol, self.callbacks.get(subscription_id))
                elif subscription_id.startswith("orderbook_"):
                    await self.subscribe_order_book(symbol, self.callbacks.get(subscription_id))
                elif subscription_id == "user_data":
                    await self.subscribe_user_data(self.callbacks.get(subscription_id))
                    
        except Exception as e:
            logger.error(f"Reconnection failed: {e}")
            await self._handle_reconnect()
    
    async def subscribe_trades(self, symbol: str, callback: Callable) -> bool:
        """Subscribe to trades updates"""
        if not self.websocket or not self.is_connected:
            raise ExchangeError("WebSocket not connected")
        
        try:
            subscription_id = f"trades_{symbol}"
            self.subscriptions[subscription_id] = symbol
            self.callbacks[subscription_id] = callback
            
            stream_name = f"{symbol.lower()}@trade"
            subscribe_msg = {
                "method": "SUBSCRIBE",
                "params": [stream_name],
                "id": 1
            }
            
            await self.websocket.send(json.dumps(subscribe_msg))
            logger.info(f"Subscribed to trades updates for {symbol}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to subscribe to trades: {e}")
            return False
    
    async def subscribe_funding_rates(self, callback: Callable) -> bool:
        """Subscribe to funding rate updates"""
        if not self.websocket or not self.is_connected:
            raise ExchangeError("WebSocket not connected")
        
        try:
            subscription_id = "funding_rates"
            self.subscriptions[subscription_id] = "funding_rates"
            self.callbacks[subscription_id] = callback
            
            # Note: Aster doesn't have a dedicated funding rate stream
            # We would need to poll the REST API for funding rates
            logger.warning("Aster doesn't support real-time funding rate updates via WebSocket")
            return False
            
        except Exception as e:
            logger.error(f"Failed to subscribe to funding rates: {e}")
            return False
    
    async def subscribe_kline(self, symbol: str, interval: str, callback: Callable) -> bool:
        """Subscribe to kline/candlestick updates"""
        if not self.websocket or not self.is_connected:
            raise ExchangeError("WebSocket not connected")
        
        try:
            subscription_id = f"kline_{symbol}_{interval}"
            self.subscriptions[subscription_id] = f"{symbol}_{interval}"
            self.callbacks[subscription_id] = callback
            
            stream_name = f"{symbol.lower()}@kline_{interval}"
            subscribe_msg = {
                "method": "SUBSCRIBE",
                "params": [stream_name],
                "id": 1
            }
            
            await self.websocket.send(json.dumps(subscribe_msg))
            logger.info(f"Subscribed to kline updates for {symbol} {interval}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to subscribe to kline: {e}")
            return False
