"""
Service factory for creating and managing exchange services
"""
import logging
from typing import Any, Dict, Optional, Type, Union

from .base import ExchangeService, SpotService, FuturesService, WebSocketService
from .hyperliquid.client import HyperliquidClient
from .hyperliquid.spot import HyperliquidSpotService
from .hyperliquid.futures import HyperliquidFuturesService
from .hyperliquid.websocket import HyperliquidWebSocketService
from .aster.client import AsterClient
from .aster.spot import AsterSpotService
from .aster.futures import AsterFuturesService
from .aster.websocket import AsterWebSocketService
from .config import ServiceConfig, HyperliquidConfig, AsterConfig
from .exceptions import ConfigurationError, ValidationError


logger = logging.getLogger(__name__)


class ServiceFactory:
    """Factory for creating exchange services"""
    
    def __init__(self, config: ServiceConfig):
        self.config = config
        self._services: Dict[str, Any] = {}
    
    def create_hyperliquid_client(self) -> HyperliquidClient:
        """Create Hyperliquid client"""
        if not self.config.exchanges.get("hyperliquid"):
            raise ConfigurationError("Hyperliquid configuration not found")
        
        hyperliquid_config = self.config.exchanges["hyperliquid"]
        if not hyperliquid_config.enabled:
            raise ConfigurationError("Hyperliquid is not enabled")
        
        config_dict = {
            "account_address": hyperliquid_config.account_address,
            "secret_key": hyperliquid_config.secret_key,
            "base_url": hyperliquid_config.base_url,
            "testnet": hyperliquid_config.testnet,
            "rate_limit": hyperliquid_config.rate_limit
        }
        
        return HyperliquidClient(config_dict)
    
    def create_hyperliquid_spot_service(self) -> HyperliquidSpotService:
        """Create Hyperliquid spot service"""
        if not self.config.exchanges.get("hyperliquid"):
            raise ConfigurationError("Hyperliquid configuration not found")
        
        hyperliquid_config = self.config.exchanges["hyperliquid"]
        if not hyperliquid_config.enabled:
            raise ConfigurationError("Hyperliquid is not enabled")
        
        config_dict = {
            "account_address": hyperliquid_config.account_address,
            "secret_key": hyperliquid_config.secret_key,
            "base_url": hyperliquid_config.base_url,
            "testnet": hyperliquid_config.testnet,
            "rate_limit": hyperliquid_config.rate_limit
        }
        
        return HyperliquidSpotService(config_dict)
    
    def create_hyperliquid_futures_service(self) -> HyperliquidFuturesService:
        """Create Hyperliquid futures service"""
        if not self.config.exchanges.get("hyperliquid"):
            raise ConfigurationError("Hyperliquid configuration not found")
        
        hyperliquid_config = self.config.exchanges["hyperliquid"]
        if not hyperliquid_config.enabled:
            raise ConfigurationError("Hyperliquid is not enabled")
        
        config_dict = {
            "account_address": hyperliquid_config.account_address,
            "secret_key": hyperliquid_config.secret_key,
            "base_url": hyperliquid_config.base_url,
            "testnet": hyperliquid_config.testnet,
            "rate_limit": hyperliquid_config.rate_limit
        }
        
        return HyperliquidFuturesService(config_dict)
    
    def create_hyperliquid_websocket_service(self) -> HyperliquidWebSocketService:
        """Create Hyperliquid WebSocket service"""
        if not self.config.exchanges.get("hyperliquid"):
            raise ConfigurationError("Hyperliquid configuration not found")
        
        hyperliquid_config = self.config.exchanges["hyperliquid"]
        if not hyperliquid_config.enabled:
            raise ConfigurationError("Hyperliquid is not enabled")
        
        config_dict = {
            "ws_url": hyperliquid_config.ws_url,
            "account_address": hyperliquid_config.account_address,
            "testnet": hyperliquid_config.testnet
        }
        
        return HyperliquidWebSocketService(config_dict)
    
    def create_aster_client(self) -> AsterClient:
        """Create Aster client"""
        if not self.config.exchanges.get("aster"):
            raise ConfigurationError("Aster configuration not found")
        
        aster_config = self.config.exchanges["aster"]
        if not aster_config.enabled:
            raise ConfigurationError("Aster is not enabled")
        
        config_dict = {
            "api_key": aster_config.api_key,
            "api_secret": aster_config.api_secret,
            "base_url": aster_config.base_url,
            "spot_base_url": aster_config.spot_base_url,
            "testnet": aster_config.testnet,
            "rate_limit": aster_config.rate_limit
        }
        
        return AsterClient(config_dict)
    
    def create_aster_spot_service(self) -> AsterSpotService:
        """Create Aster spot service"""
        if not self.config.exchanges.get("aster"):
            raise ConfigurationError("Aster configuration not found")
        
        aster_config = self.config.exchanges["aster"]
        if not aster_config.enabled:
            raise ConfigurationError("Aster is not enabled")
        
        config_dict = {
            "api_key": aster_config.api_key,
            "api_secret": aster_config.api_secret,
            "base_url": aster_config.base_url,
            "spot_base_url": aster_config.spot_base_url,
            "testnet": aster_config.testnet,
            "rate_limit": aster_config.rate_limit
        }
        
        return AsterSpotService(config_dict)
    
    def create_aster_futures_service(self) -> AsterFuturesService:
        """Create Aster futures service"""
        if not self.config.exchanges.get("aster"):
            raise ConfigurationError("Aster configuration not found")
        
        aster_config = self.config.exchanges["aster"]
        if not aster_config.enabled:
            raise ConfigurationError("Aster is not enabled")
        
        config_dict = {
            "api_key": aster_config.api_key,
            "api_secret": aster_config.api_secret,
            "base_url": aster_config.base_url,
            "spot_base_url": aster_config.spot_base_url,
            "testnet": aster_config.testnet,
            "rate_limit": aster_config.rate_limit
        }
        
        return AsterFuturesService(config_dict)
    
    def create_aster_websocket_service(self) -> AsterWebSocketService:
        """Create Aster WebSocket service"""
        if not self.config.exchanges.get("aster"):
            raise ConfigurationError("Aster configuration not found")
        
        aster_config = self.config.exchanges["aster"]
        if not aster_config.enabled:
            raise ConfigurationError("Aster is not enabled")
        
        config_dict = {
            "ws_url": aster_config.ws_url,
            "spot_ws_url": aster_config.spot_ws_url,
            "api_key": aster_config.api_key,
            "api_secret": aster_config.api_secret,
            "testnet": aster_config.testnet
        }
        
        return AsterWebSocketService(config_dict)
    
    def get_service(self, exchange: str, service_type: str) -> Any:
        """Get service instance"""
        service_key = f"{exchange}_{service_type}"
        
        if service_key in self._services:
            return self._services[service_key]
        
        # Create service based on type
        if exchange == "hyperliquid":
            if service_type == "client":
                service = self.create_hyperliquid_client()
            elif service_type == "spot":
                service = self.create_hyperliquid_spot_service()
            elif service_type == "futures":
                service = self.create_hyperliquid_futures_service()
            elif service_type == "websocket":
                service = self.create_hyperliquid_websocket_service()
            else:
                raise ValidationError(f"Unknown service type: {service_type}")
        
        elif exchange == "aster":
            if service_type == "client":
                service = self.create_aster_client()
            elif service_type == "spot":
                service = self.create_aster_spot_service()
            elif service_type == "futures":
                service = self.create_aster_futures_service()
            elif service_type == "websocket":
                service = self.create_aster_websocket_service()
            else:
                raise ValidationError(f"Unknown service type: {service_type}")
        
        else:
            raise ValidationError(f"Unknown exchange: {exchange}")
        
        # Cache service
        self._services[service_key] = service
        return service
    
    def get_spot_service(self, exchange: str) -> SpotService:
        """Get spot service for exchange"""
        return self.get_service(exchange, "spot")
    
    def get_futures_service(self, exchange: str) -> FuturesService:
        """Get futures service for exchange"""
        return self.get_service(exchange, "futures")
    
    def get_websocket_service(self, exchange: str) -> WebSocketService:
        """Get WebSocket service for exchange"""
        return self.get_service(exchange, "websocket")
    
    def get_client(self, exchange: str) -> ExchangeService:
        """Get client for exchange"""
        return self.get_service(exchange, "client")
    
    def get_enabled_exchanges(self) -> list[str]:
        """Get list of enabled exchanges"""
        enabled = []
        for exchange_name, exchange_config in self.config.exchanges.items():
            if exchange_config.enabled:
                enabled.append(exchange_name)
        return enabled
    
    def is_exchange_enabled(self, exchange: str) -> bool:
        """Check if exchange is enabled"""
        exchange_config = self.config.exchanges.get(exchange)
        return exchange_config is not None and exchange_config.enabled
    
    def cleanup_services(self):
        """Cleanup all services"""
        for service_key, service in self._services.items():
            try:
                if hasattr(service, 'disconnect'):
                    import asyncio
                    if asyncio.iscoroutinefunction(service.disconnect):
                        asyncio.create_task(service.disconnect())
                    else:
                        service.disconnect()
                logger.info(f"Cleaned up service: {service_key}")
            except Exception as e:
                logger.error(f"Error cleaning up service {service_key}: {e}")
        
        self._services.clear()


class ServiceManager:
    """Service manager for handling multiple exchange services"""
    
    def __init__(self, config: ServiceConfig):
        self.config = config
        self.factory = ServiceFactory(config)
        self._connected_services: Dict[str, Any] = {}
    
    async def connect_all_services(self) -> Dict[str, bool]:
        """Connect to all enabled exchanges"""
        results = {}
        
        for exchange in self.factory.get_enabled_exchanges():
            try:
                # Connect spot service
                if self.config.features.spot_trading:
                    spot_service = self.factory.get_spot_service(exchange)
                    connected = await spot_service.connect()
                    if connected:
                        self._connected_services[f"{exchange}_spot"] = spot_service
                    results[f"{exchange}_spot"] = connected
                
                # Connect futures service
                if self.config.features.futures_trading:
                    futures_service = self.factory.get_futures_service(exchange)
                    connected = await futures_service.connect()
                    if connected:
                        self._connected_services[f"{exchange}_futures"] = futures_service
                    results[f"{exchange}_futures"] = connected
                
                # Connect WebSocket service
                websocket_service = self.factory.get_websocket_service(exchange)
                connected = await websocket_service.connect()
                if connected:
                    self._connected_services[f"{exchange}_websocket"] = websocket_service
                results[f"{exchange}_websocket"] = connected
                
            except Exception as e:
                logger.error(f"Failed to connect {exchange}: {e}")
                results[exchange] = False
        
        return results
    
    async def disconnect_all_services(self):
        """Disconnect from all services"""
        for service_key, service in self._connected_services.items():
            try:
                if hasattr(service, 'disconnect'):
                    await service.disconnect()
                logger.info(f"Disconnected service: {service_key}")
            except Exception as e:
                logger.error(f"Error disconnecting service {service_key}: {e}")
        
        self._connected_services.clear()
    
    def get_service(self, exchange: str, service_type: str) -> Optional[Any]:
        """Get connected service"""
        service_key = f"{exchange}_{service_type}"
        return self._connected_services.get(service_key)
    
    def get_spot_service(self, exchange: str) -> Optional[SpotService]:
        """Get connected spot service"""
        return self.get_service(exchange, "spot")
    
    def get_futures_service(self, exchange: str) -> Optional[FuturesService]:
        """Get connected futures service"""
        return self.get_service(exchange, "futures")
    
    def get_websocket_service(self, exchange: str) -> Optional[WebSocketService]:
        """Get connected WebSocket service"""
        return self.get_service(exchange, "websocket")
    
    def get_connected_exchanges(self) -> list[str]:
        """Get list of connected exchanges"""
        exchanges = set()
        for service_key in self._connected_services.keys():
            exchange = service_key.split("_")[0]
            exchanges.add(exchange)
        return list(exchanges)
    
    def is_service_connected(self, exchange: str, service_type: str) -> bool:
        """Check if service is connected"""
        service_key = f"{exchange}_{service_type}"
        return service_key in self._connected_services
