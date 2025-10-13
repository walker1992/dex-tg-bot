"""
Hyperliquid WebSocket service
"""
import asyncio
import json
import logging
import websockets
from typing import Any, Dict, List, Optional, Callable

from ..base import WebSocketService, Ticker, OrderBook, ExchangeError


logger = logging.getLogger(__name__)


class HyperliquidWebSocketService(WebSocketService):
    """Hyperliquid WebSocket service"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.ws_url = config.get("ws_url", "wss://api.hyperliquid.xyz/ws")
        self.account_address = config.get("account_address")
        self.websocket = None
        self.subscriptions: Dict[str, str] = {}
        self.reconnect_interval = 5
        self.max_reconnect_attempts = 10
        self.reconnect_attempts = 0
    
    async def connect(self) -> bool:
        """Connect to Hyperliquid WebSocket"""
        try:
            self.websocket = await websockets.connect(self.ws_url)
            self.is_connected = True
            self.reconnect_attempts = 0
            
            # Start message handler
            asyncio.create_task(self._message_handler())
            
            logger.info("Connected to Hyperliquid WebSocket")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Hyperliquid WebSocket: {e}")
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from Hyperliquid WebSocket"""
        self.is_connected = False
        
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
        
        self.subscriptions.clear()
        logger.info("Disconnected from Hyperliquid WebSocket")
    
    async def subscribe_ticker(self, symbol: str, callback: Callable) -> bool:
        """Subscribe to ticker updates"""
        if not self.websocket or not self.is_connected:
            raise ExchangeError("WebSocket not connected")
        
        try:
            subscription_id = f"ticker_{symbol}"
            self.subscriptions[subscription_id] = symbol
            self.callbacks[subscription_id] = callback
            
            # Subscribe to l2 book updates for ticker data
            subscribe_msg = {
                "method": "subscribe",
                "subscription": {
                    "type": "l2Book",
                    "coin": symbol
                }
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
            
            subscribe_msg = {
                "method": "subscribe",
                "subscription": {
                    "type": "l2Book",
                    "coin": symbol
                }
            }
            
            await self.websocket.send(json.dumps(subscribe_msg))
            logger.info(f"Subscribed to order book updates for {symbol}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to subscribe to order book: {e}")
            return False
    
    async def subscribe_user_data(self, callback: Callable) -> bool:
        """Subscribe to user data updates"""
        if not self.websocket or not self.is_connected:
            raise ExchangeError("WebSocket not connected")
        
        if not self.account_address:
            raise ExchangeError("Account address required for user data subscription")
        
        try:
            subscription_id = "user_data"
            self.subscriptions[subscription_id] = "user_data"
            self.callbacks[subscription_id] = callback
            
            subscribe_msg = {
                "method": "subscribe",
                "subscription": {
                    "type": "allMids",
                    "user": self.account_address
                }
            }
            
            await self.websocket.send(json.dumps(subscribe_msg))
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
                
                unsubscribe_msg = {
                    "method": "unsubscribe",
                    "subscription": {
                        "type": "l2Book",
                        "coin": symbol
                    }
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
    
    async def _process_message(self, data: Dict[str, Any]):
        """Process incoming WebSocket message"""
        try:
            if "channel" in data:
                channel = data["channel"]
                
                if channel == "l2Book":
                    await self._handle_l2_book_update(data)
                elif channel == "allMids":
                    await self._handle_user_data_update(data)
                elif channel == "trades":
                    await self._handle_trades_update(data)
                    
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    async def _handle_l2_book_update(self, data: Dict[str, Any]):
        """Handle L2 book updates"""
        try:
            coin = data.get("coin", "")
            levels = data.get("levels", [])
            
            if len(levels) >= 2:
                bids = levels[0]
                asks = levels[1]
                
                # Create order book
                order_book = OrderBook(
                    symbol=coin,
                    bids=[[float(bid["px"]), float(bid["sz"])] for bid in bids],
                    asks=[[float(ask["px"]), float(ask["sz"])] for ask in asks],
                    timestamp=int(asyncio.get_event_loop().time() * 1000)
                )
                
                # Create ticker from best bid/ask
                if bids and asks:
                    ticker = Ticker(
                        symbol=coin,
                        bid_price=float(bids[0]["px"]),
                        ask_price=float(asks[0]["px"]),
                        last_price=float(bids[0]["px"]),  # Use bid as last price
                        volume=0,  # Not available in l2 book
                        price_change=0,
                        price_change_percent=0,
                        high_price=0,
                        low_price=0,
                        timestamp=int(asyncio.get_event_loop().time() * 1000)
                    )
                    
                    # Call callbacks
                    ticker_key = f"ticker_{coin}"
                    orderbook_key = f"orderbook_{coin}"
                    
                    if ticker_key in self.callbacks:
                        await self.callbacks[ticker_key](ticker)
                    
                    if orderbook_key in self.callbacks:
                        await self.callbacks[orderbook_key](order_book)
                        
        except Exception as e:
            logger.error(f"Error handling L2 book update: {e}")
    
    async def _handle_user_data_update(self, data: Dict[str, Any]):
        """Handle user data updates"""
        try:
            if "user_data" in self.callbacks:
                await self.callbacks["user_data"](data)
                
        except Exception as e:
            logger.error(f"Error handling user data update: {e}")
    
    async def _handle_trades_update(self, data: Dict[str, Any]):
        """Handle trades updates"""
        try:
            # Process trades data if needed
            pass
            
        except Exception as e:
            logger.error(f"Error handling trades update: {e}")
    
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
            
            subscribe_msg = {
                "method": "subscribe",
                "subscription": {
                    "type": "trades",
                    "coin": symbol
                }
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
            
            # Note: Hyperliquid doesn't have a dedicated funding rate stream
            # We would need to poll the REST API for funding rates
            logger.warning("Hyperliquid doesn't support real-time funding rate updates via WebSocket")
            return False
            
        except Exception as e:
            logger.error(f"Failed to subscribe to funding rates: {e}")
            return False
