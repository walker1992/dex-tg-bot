"""
Example usage of exchange services
"""
import asyncio
import logging
from decimal import Decimal

from .config import load_config, create_example_config
from .factory import ServiceManager
from .base import OrderSide, OrderType, TimeInForce
from .exceptions import ExchangeServiceError

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def example_hyperliquid_usage():
    """Example usage of Hyperliquid services"""
    try:
        # Load configuration
        config = load_config("config/config.json")
        
        # Create service manager
        service_manager = ServiceManager(config)
        
        # Connect to all services
        connection_results = await service_manager.connect_all_services()
        logger.info(f"Connection results: {connection_results}")
        
        # Get Hyperliquid services
        hyperliquid_spot = service_manager.get_spot_service("hyperliquid")
        hyperliquid_futures = service_manager.get_futures_service("hyperliquid")
        hyperliquid_ws = service_manager.get_websocket_service("hyperliquid")
        
        if hyperliquid_spot:
            # Get account info
            account_info = await hyperliquid_spot.get_account_info()
            logger.info(f"Hyperliquid account info: {account_info}")
            
            # Get balances
            balances = await hyperliquid_spot.get_balances()
            logger.info(f"Hyperliquid balances: {balances}")
            
            # Get ticker
            ticker = await hyperliquid_spot.get_ticker("BTC")
            logger.info(f"BTC ticker: {ticker}")
        
        if hyperliquid_futures:
            # Get positions
            positions = await hyperliquid_futures.get_positions()
            logger.info(f"Hyperliquid positions: {positions}")
            
            # Get funding rate
            funding_rate = await hyperliquid_futures.get_funding_rate("BTC")
            logger.info(f"BTC funding rate: {funding_rate}")
        
        if hyperliquid_ws:
            # Subscribe to ticker updates
            async def ticker_callback(ticker):
                logger.info(f"Ticker update: {ticker}")
            
            await hyperliquid_ws.subscribe_ticker("BTC", ticker_callback)
            
            # Keep running for a while to receive updates
            await asyncio.sleep(10)
        
        # Disconnect all services
        await service_manager.disconnect_all_services()
        
    except ExchangeServiceError as e:
        logger.error(f"Exchange service error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")


async def example_aster_usage():
    """Example usage of Aster services"""
    try:
        # Load configuration
        config = load_config("config/config.json")
        
        # Create service manager
        service_manager = ServiceManager(config)
        
        # Connect to all services
        connection_results = await service_manager.connect_all_services()
        logger.info(f"Connection results: {connection_results}")
        
        # Get Aster services
        aster_spot = service_manager.get_spot_service("aster")
        aster_futures = service_manager.get_futures_service("aster")
        aster_ws = service_manager.get_websocket_service("aster")
        
        if aster_spot:
            # Get account info
            account_info = await aster_spot.get_account_info()
            logger.info(f"Aster account info: {account_info}")
            
            # Get balances
            balances = await aster_spot.get_balances()
            logger.info(f"Aster balances: {balances}")
            
            # Get ticker
            ticker = await aster_spot.get_ticker("BTCUSDT")
            logger.info(f"BTCUSDT ticker: {ticker}")
        
        if aster_futures:
            # Get positions
            positions = await aster_futures.get_positions()
            logger.info(f"Aster positions: {positions}")
            
            # Get funding rate
            funding_rate = await aster_futures.get_funding_rate("BTCUSDT")
            logger.info(f"BTCUSDT funding rate: {funding_rate}")
        
        if aster_ws:
            # Subscribe to ticker updates
            async def ticker_callback(ticker):
                logger.info(f"Ticker update: {ticker}")
            
            await aster_ws.subscribe_ticker("BTCUSDT", ticker_callback)
            
            # Keep running for a while to receive updates
            await asyncio.sleep(10)
        
        # Disconnect all services
        await service_manager.disconnect_all_services()
        
    except ExchangeServiceError as e:
        logger.error(f"Exchange service error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")


async def example_trading_operations():
    """Example trading operations"""
    try:
        # Load configuration
        config = load_config("config/config.json")
        
        # Create service manager
        service_manager = ServiceManager(config)
        
        # Connect to services
        await service_manager.connect_all_services()
        
        # Get futures service (for trading)
        hyperliquid_futures = service_manager.get_futures_service("hyperliquid")
        aster_futures = service_manager.get_futures_service("aster")
        
        if hyperliquid_futures:
            # Place a limit order (example - don't actually place orders in production)
            logger.info("Example: Placing limit order on Hyperliquid")
            # order = await hyperliquid_futures.place_order(
            #     symbol="BTC",
            #     side=OrderSide.BUY,
            #     order_type=OrderType.LIMIT,
            #     quantity=Decimal("0.001"),
            #     price=Decimal("50000"),
            #     time_in_force=TimeInForce.GTC
            # )
            # logger.info(f"Order placed: {order}")
        
        if aster_futures:
            # Place a limit order (example - don't actually place orders in production)
            logger.info("Example: Placing limit order on Aster")
            # order = await aster_futures.place_order(
            #     symbol="BTCUSDT",
            #     side=OrderSide.BUY,
            #     order_type=OrderType.LIMIT,
            #     quantity=Decimal("0.001"),
            #     price=Decimal("50000"),
            #     time_in_force=TimeInForce.GTC
            # )
            # logger.info(f"Order placed: {order}")
        
        # Disconnect all services
        await service_manager.disconnect_all_services()
        
    except ExchangeServiceError as e:
        logger.error(f"Exchange service error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")


async def example_funding_rate_monitoring():
    """Example funding rate monitoring"""
    try:
        # Load configuration
        config = load_config("config/config.json")
        
        # Create service manager
        service_manager = ServiceManager(config)
        
        # Connect to services
        await service_manager.connect_all_services()
        
        # Get futures services
        hyperliquid_futures = service_manager.get_futures_service("hyperliquid")
        aster_futures = service_manager.get_futures_service("aster")
        
        if hyperliquid_futures:
            # Get funding rates
            funding_rates = await hyperliquid_futures.get_funding_rates()
            logger.info(f"Hyperliquid funding rates: {funding_rates}")
        
        if aster_futures:
            # Get funding rates
            funding_rates = await aster_futures.get_funding_rates()
            logger.info(f"Aster funding rates: {funding_rates}")
        
        # Disconnect all services
        await service_manager.disconnect_all_services()
        
    except ExchangeServiceError as e:
        logger.error(f"Exchange service error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")


def create_example_config_file():
    """Create example configuration file"""
    try:
        create_example_config("config/config.example.json")
        logger.info("Example configuration file created at config/config.example.json")
    except Exception as e:
        logger.error(f"Failed to create example configuration: {e}")


async def main():
    """Main example function"""
    logger.info("Starting exchange services examples")
    
    # Create example configuration file
    create_example_config_file()
    
    # Run examples
    logger.info("Running Hyperliquid example...")
    await example_hyperliquid_usage()
    
    logger.info("Running Aster example...")
    await example_aster_usage()
    
    logger.info("Running trading operations example...")
    await example_trading_operations()
    
    logger.info("Running funding rate monitoring example...")
    await example_funding_rate_monitoring()
    
    logger.info("Examples completed")


if __name__ == "__main__":
    asyncio.run(main())
