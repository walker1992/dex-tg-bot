# Exchange Services

This module provides a unified interface for interacting with Hyperliquid and Aster exchanges. It includes support for spot trading, futures trading, and WebSocket real-time data streams.

## Features

- **Unified Interface**: Common interface for all exchanges
- **Spot Trading**: Support for spot market operations
- **Futures Trading**: Support for futures/perpetual contracts
- **WebSocket Streams**: Real-time market data and user updates
- **Error Handling**: Comprehensive error handling and exceptions
- **Configuration Management**: Flexible configuration system
- **Rate Limiting**: Built-in rate limiting support
- **Type Safety**: Full type hints and validation

## Architecture

```
services/
├── base.py              # Base interfaces and abstract classes
├── config.py            # Configuration management
├── exceptions.py        # Custom exceptions
├── factory.py           # Service factory and manager
├── example.py           # Usage examples
├── hyperliquid/         # Hyperliquid exchange services
│   ├── client.py        # Main client implementation
│   ├── spot.py          # Spot trading service
│   ├── futures.py       # Futures trading service
│   └── websocket.py     # WebSocket service
└── aster/               # Aster exchange services
    ├── client.py        # Main client implementation
    ├── spot.py          # Spot trading service
    ├── futures.py       # Futures trading service
    └── websocket.py     # WebSocket service
```

## Quick Start

### 1. Configuration

First, create a configuration file:

```python
from src.services.config import create_example_config

# Create example configuration
create_example_config("config/config.json")
```

Edit `config/config.json` with your API credentials:

```json
{
  "telegram": {
    "bot_token": "YOUR_BOT_TOKEN",
    "chat_id": "YOUR_CHAT_ID"
  },
  "exchanges": {
    "hyperliquid": {
      "enabled": true,
      "account_address": "0x...",
      "secret_key": "0x...",
      "base_url": "https://api.hyperliquid.xyz"
    },
    "aster": {
      "enabled": true,
      "api_key": "YOUR_API_KEY",
      "api_secret": "YOUR_API_SECRET",
      "base_url": "https://fapi.asterdex.com"
    }
  }
}
```

### 2. Basic Usage

```python
import asyncio
from src.services.config import load_config
from src.services.factory import ServiceManager

async def main():
    # Load configuration
    config = load_config("config/config.json")
    
    # Create service manager
    service_manager = ServiceManager(config)
    
    # Connect to all services
    await service_manager.connect_all_services()
    
    # Get services
    hyperliquid_spot = service_manager.get_spot_service("hyperliquid")
    aster_futures = service_manager.get_futures_service("aster")
    
    # Use services
    if hyperliquid_spot:
        balances = await hyperliquid_spot.get_balances()
        print(f"Balances: {balances}")
    
    if aster_futures:
        positions = await aster_futures.get_positions()
        print(f"Positions: {positions}")
    
    # Disconnect
    await service_manager.disconnect_all_services()

asyncio.run(main())
```

## Service Types

### Spot Services

Spot services handle spot market operations:

```python
# Get spot service
spot_service = service_manager.get_spot_service("hyperliquid")

# Get balances
balances = await spot_service.get_balances()

# Get ticker
ticker = await spot_service.get_ticker("BTC")

# Place order
from src.services.base import OrderSide, OrderType, TimeInForce
from decimal import Decimal

order = await spot_service.place_order(
    symbol="BTC",
    side=OrderSide.BUY,
    order_type=OrderType.LIMIT,
    quantity=Decimal("0.001"),
    price=Decimal("50000"),
    time_in_force=TimeInForce.GTC
)
```

### Futures Services

Futures services handle futures/perpetual contracts:

```python
# Get futures service
futures_service = service_manager.get_futures_service("aster")

# Get positions
positions = await futures_service.get_positions()

# Get funding rate
funding_rate = await futures_service.get_funding_rate("BTCUSDT")

# Set leverage
await futures_service.set_leverage("BTCUSDT", 5)

# Place futures order
order = await futures_service.place_futures_order(
    symbol="BTCUSDT",
    side=OrderSide.BUY,
    order_type=OrderType.LIMIT,
    quantity=Decimal("0.001"),
    price=Decimal("50000"),
    reduce_only=False
)
```

### WebSocket Services

WebSocket services provide real-time data streams:

```python
# Get WebSocket service
ws_service = service_manager.get_websocket_service("hyperliquid")

# Subscribe to ticker updates
async def ticker_callback(ticker):
    print(f"Ticker update: {ticker}")

await ws_service.subscribe_ticker("BTC", ticker_callback)

# Subscribe to order book updates
async def orderbook_callback(orderbook):
    print(f"Order book update: {orderbook}")

await ws_service.subscribe_order_book("BTC", orderbook_callback)

# Subscribe to user data updates
async def user_data_callback(data):
    print(f"User data update: {data}")

await ws_service.subscribe_user_data(user_data_callback)
```

## Error Handling

The services include comprehensive error handling:

```python
from src.services.exceptions import (
    ExchangeServiceError,
    AuthenticationError,
    RateLimitError,
    InsufficientBalanceError,
    InvalidSymbolError,
    OrderNotFoundError
)

try:
    order = await spot_service.place_order(...)
except AuthenticationError as e:
    print(f"Authentication failed: {e}")
except RateLimitError as e:
    print(f"Rate limit exceeded: {e}")
    if e.retry_after:
        print(f"Retry after: {e.retry_after} seconds")
except InsufficientBalanceError as e:
    print(f"Insufficient balance: {e}")
except InvalidSymbolError as e:
    print(f"Invalid symbol: {e}")
except OrderNotFoundError as e:
    print(f"Order not found: {e}")
except ExchangeServiceError as e:
    print(f"Exchange error: {e}")
```

## Configuration

### Exchange Configuration

Each exchange can be configured with specific parameters:

```python
# Hyperliquid configuration
hyperliquid_config = {
    "enabled": True,
    "account_address": "0x...",
    "secret_key": "0x...",
    "base_url": "https://api.hyperliquid.xyz",
    "ws_url": "wss://api.hyperliquid.xyz/ws",
    "testnet": False,
    "rate_limit": {
        "requests_per_minute": 60,
        "burst_limit": 10
    }
}

# Aster configuration
aster_config = {
    "enabled": True,
    "api_key": "YOUR_API_KEY",
    "api_secret": "YOUR_API_SECRET",
    "base_url": "https://fapi.asterdex.com",
    "spot_base_url": "https://sapi.asterdex.com",
    "ws_url": "wss://fstream.asterdex.com/ws",
    "spot_ws_url": "wss://stream.asterdex.com/ws",
    "testnet": False,
    "rate_limit": {
        "requests_per_minute": 1200,
        "weight_limit": 1200
    }
}
```

### Trading Configuration

```python
trading_config = {
    "default_leverage": 1,
    "max_leverage": 10,
    "min_order_size": 10.0,
    "max_order_size": 10000.0,
    "default_slippage": 0.01,
    "order_timeout": 30,
    "position_limits": {
        "max_positions_per_symbol": 1,
        "max_total_positions": 10,
        "max_position_size_usd": 5000.0
    }
}
```

### Risk Management Configuration

```python
risk_config = {
    "daily_loss_limit": 100.0,
    "max_drawdown_percent": 10.0,
    "emergency_stop_enabled": True,
    "position_size_limit": 0.1,
    "correlation_limit": 0.8
}
```

## Data Models

### Balance

```python
@dataclass
class Balance:
    asset: str
    free: Decimal
    locked: Decimal
    total: Decimal
```

### Position

```python
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
```

### Order

```python
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
```

### Ticker

```python
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
```

## Examples

See `example.py` for comprehensive usage examples including:

- Basic service usage
- Trading operations
- WebSocket subscriptions
- Error handling
- Configuration management

## Dependencies

Required packages:

```
aiohttp>=3.8.0
websockets>=10.0
hyperliquid-python-sdk>=0.1.0
eth-account>=0.8.0
```

## Testing

Run the example to test your configuration:

```bash
python src/services/example.py
```

## Security Notes

- Never commit API keys or secrets to version control
- Use environment variables for sensitive configuration
- Enable IP whitelisting on exchange accounts
- Use testnet for development and testing
- Implement proper error handling and logging
- Monitor rate limits and implement backoff strategies

## Support

For issues and questions:

1. Check the example code in `example.py`
2. Review the configuration in `config.py`
3. Check error messages and logs
4. Verify API credentials and permissions
5. Test with small amounts first
