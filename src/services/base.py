"""
Base interfaces and abstract classes for exchange services
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Dict, List, Optional, Union
from enum import Enum


class OrderSide(Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_LOSS = "STOP_LOSS"
    TAKE_PROFIT = "TAKE_PROFIT"
    TRAILING_STOP = "TRAILING_STOP"


class OrderStatus(Enum):
    NEW = "NEW"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELED = "CANCELED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class TimeInForce(Enum):
    GTC = "Gtc"  # Good Till Canceled (Hyperliquid format)
    IOC = "Ioc"  # Immediate or Cancel (Hyperliquid format)
    FOK = "Fok"  # Fill or Kill (Hyperliquid format)


@dataclass
class SymbolInfo:
    symbol: str
    base_asset: str
    quote_asset: str
    tick_size: Decimal
    step_size: Decimal
    min_qty: Decimal
    min_notional: Decimal
    is_spot: bool
    is_futures: bool


@dataclass
class Balance:
    asset: str
    free: Decimal
    locked: Decimal
    total: Decimal


@dataclass
class Position:
    symbol: str
    side: str
    size: Decimal
    entry_price: Decimal
    mark_price: Decimal
    pnl: Decimal
    percentage: Decimal
    margin: Decimal
    leverage: int


@dataclass
class Order:
    order_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: Decimal
    price: Optional[Decimal]
    status: OrderStatus
    filled_qty: Decimal
    avg_price: Optional[Decimal]
    time_in_force: TimeInForce
    created_at: int
    updated_at: int
    client_order_id: Optional[str] = None


@dataclass
class Ticker:
    symbol: str
    bid_price: Decimal
    ask_price: Decimal
    last_price: Decimal
    volume: Decimal
    price_change: Decimal
    price_change_percent: Decimal
    high_price: Decimal
    low_price: Decimal
    timestamp: int


@dataclass
class FundingRate:
    symbol: str
    funding_rate: Decimal
    funding_time: int
    next_funding_time: int


@dataclass
class OrderBook:
    symbol: str
    bids: List[List[Decimal]]  # [[price, quantity], ...]
    asks: List[List[Decimal]]  # [[price, quantity], ...]
    timestamp: int


class ExchangeError(Exception):
    """Base exception for exchange-related errors"""
    pass


class AuthenticationError(ExchangeError):
    """Authentication failed"""
    pass


class InsufficientBalanceError(ExchangeError):
    """Insufficient balance for operation"""
    pass


class OrderNotFoundError(ExchangeError):
    """Order not found"""
    pass


class InvalidSymbolError(ExchangeError):
    """Invalid trading symbol"""
    pass


class RateLimitError(ExchangeError):
    """Rate limit exceeded"""
    pass


class ExchangeService(ABC):
    """Base abstract class for exchange services"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.is_connected = False
    
    @abstractmethod
    async def connect(self) -> bool:
        """Connect to exchange"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from exchange"""
        pass
    
    @abstractmethod
    async def get_account_info(self) -> Dict[str, Any]:
        """Get account information"""
        pass
    
    @abstractmethod
    async def get_balances(self) -> List[Balance]:
        """Get account balances"""
        pass
    
    @abstractmethod
    async def get_positions(self) -> List[Position]:
        """Get current positions"""
        pass
    
    @abstractmethod
    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Order]:
        """Get open orders"""
        pass
    
    @abstractmethod
    async def get_order(self, order_id: str, symbol: str) -> Order:
        """Get specific order"""
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        """Cancel an order"""
        pass
    
    @abstractmethod
    async def cancel_all_orders(self, symbol: Optional[str] = None) -> bool:
        """Cancel all orders"""
        pass
    
    @abstractmethod
    async def get_ticker(self, symbol: str) -> Ticker:
        """Get ticker information"""
        pass
    
    @abstractmethod
    async def get_order_book(self, symbol: str, limit: int = 100) -> OrderBook:
        """Get order book"""
        pass
    
    @abstractmethod
    async def get_funding_rate(self, symbol: str) -> FundingRate:
        """Get funding rate (for futures)"""
        pass
    
    @abstractmethod
    async def get_symbol_info(self, symbol: str) -> SymbolInfo:
        """Get symbol information"""
        pass
    
    @abstractmethod
    async def get_exchange_info(self) -> Dict[str, Any]:
        """Get exchange information"""
        pass


class SpotService(ExchangeService):
    """Base class for spot trading services"""
    
    @abstractmethod
    async def get_spot_balances(self) -> List[Balance]:
        """Get spot balances"""
        pass
    
    @abstractmethod
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
        pass


class FuturesService(ExchangeService):
    """Base class for futures trading services"""
    
    @abstractmethod
    async def get_futures_balances(self) -> List[Balance]:
        """Get futures balances"""
        pass
    
    @abstractmethod
    async def get_futures_positions(self) -> List[Position]:
        """Get futures positions"""
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    async def set_leverage(self, symbol: str, leverage: int) -> bool:
        """Set leverage for symbol"""
        pass
    
    @abstractmethod
    async def get_funding_rates(self) -> List[FundingRate]:
        """Get all funding rates"""
        pass


class WebSocketService(ABC):
    """Base class for WebSocket services"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.is_connected = False
        self.callbacks: Dict[str, callable] = {}
    
    @abstractmethod
    async def connect(self) -> bool:
        """Connect to WebSocket"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from WebSocket"""
        pass
    
    @abstractmethod
    async def subscribe_ticker(self, symbol: str, callback: callable) -> bool:
        """Subscribe to ticker updates"""
        pass
    
    @abstractmethod
    async def subscribe_order_book(self, symbol: str, callback: callable) -> bool:
        """Subscribe to order book updates"""
        pass
    
    @abstractmethod
    async def subscribe_user_data(self, callback: callable) -> bool:
        """Subscribe to user data updates"""
        pass
    
    @abstractmethod
    async def unsubscribe(self, stream: str) -> bool:
        """Unsubscribe from stream"""
        pass
