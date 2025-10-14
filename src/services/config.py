"""
Configuration management for exchange services
"""
import json
import logging
import os
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, asdict
from pathlib import Path

from .exceptions import ConfigurationError, ValidationError


logger = logging.getLogger(__name__)


@dataclass
class TelegramConfig:
    """Telegram bot configuration"""
    bot_token: str
    chat_id: str
    webhook_url: str = ""
    webhook_port: int = 8443
    allowed_users: List[int] = None
    admin_users: List[int] = None
    
    def __post_init__(self):
        if self.allowed_users is None:
            self.allowed_users = []
        if self.admin_users is None:
            self.admin_users = []


@dataclass
class ExchangeConfig:
    """Base exchange configuration"""
    enabled: bool = True
    testnet: bool = False
    rate_limit: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.rate_limit is None:
            self.rate_limit = {}


@dataclass
class HyperliquidConfig(ExchangeConfig):
    """Hyperliquid exchange configuration"""
    account_address: str = ""
    secret_key: str = ""
    base_url: str = "https://api.hyperliquid.xyz"
    ws_url: str = "wss://api.hyperliquid.xyz/ws"
    
    def __post_init__(self):
        super().__post_init__()
        if not self.rate_limit:
            self.rate_limit = {
                "requests_per_minute": 60,
                "burst_limit": 10
            }


@dataclass
class AsterConfig(ExchangeConfig):
    """Aster exchange configuration"""
    api_key: str = ""
    api_secret: str = ""
    base_url: str = "https://fapi.asterdex.com"
    spot_base_url: str = "https://sapi.asterdex.com"
    ws_url: str = "wss://fstream.asterdex.com/ws"
    spot_ws_url: str = "wss://stream.asterdex.com/ws"
    
    def __post_init__(self):
        super().__post_init__()
        if not self.rate_limit:
            self.rate_limit = {
                "requests_per_minute": 1200,
                "weight_limit": 1200
            }


@dataclass
class TradingConfig:
    """Trading configuration"""
    default_leverage: int = 1
    max_leverage: int = 10
    min_order_size: float = 10.0
    max_order_size: float = 10000.0
    default_slippage: float = 0.01
    order_timeout: int = 30
    position_limits: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.position_limits is None:
            self.position_limits = {
                "max_positions_per_symbol": 1,
                "max_total_positions": 10,
                "max_position_size_usd": 5000.0
            }


@dataclass
class RiskManagementConfig:
    """Risk management configuration"""
    daily_loss_limit: float = 100.0
    max_drawdown_percent: float = 10.0
    emergency_stop_enabled: bool = True
    position_size_limit: float = 0.1
    correlation_limit: float = 0.8


@dataclass
class AlertsConfig:
    """Alerts configuration"""
    price_alerts: Dict[str, Any] = None
    funding_rate_alerts: Dict[str, Any] = None
    position_alerts: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.price_alerts is None:
            self.price_alerts = {
                "enabled": True,
                "max_alerts_per_user": 20,
                "check_interval": 5
            }
        if self.funding_rate_alerts is None:
            self.funding_rate_alerts = {
                "enabled": True,
                "threshold": 0.0001,
                "check_interval": 60
            }
        if self.position_alerts is None:
            self.position_alerts = {
                "enabled": True,
                "pnl_threshold": 50.0,
                "margin_ratio_threshold": 0.2
            }


@dataclass
class StorageConfig:
    """Storage configuration"""
    type: str = "csv"
    data_dir: str = "data"
    backup_enabled: bool = True
    backup_interval_hours: int = 24


@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: str = "WARNING"  # Reduced from INFO to WARNING to minimize logs
    file: str = "logs/bot.log"
    max_bytes: int = 10485760  # 10MB
    backup_count: int = 5
    format: str = "%(asctime)s - %(levelname)s - %(message)s"  # Simplified format


@dataclass
class SecurityConfig:
    """Security configuration"""
    encryption_key: str = ""
    session_timeout: int = 3600
    max_login_attempts: int = 5
    lockout_duration: int = 300


@dataclass
class FeaturesConfig:
    """Features configuration"""
    spot_trading: bool = True
    futures_trading: bool = True
    funding_rate_monitoring: bool = True
    portfolio_tracking: bool = True
    backtesting: bool = False
    paper_trading: bool = False


@dataclass
class ServiceConfig:
    """Main service configuration"""
    telegram: TelegramConfig
    exchanges: Dict[str, Union[HyperliquidConfig, AsterConfig]]
    trading: TradingConfig
    risk_management: RiskManagementConfig
    alerts: AlertsConfig
    storage: StorageConfig
    logging: LoggingConfig
    security: SecurityConfig
    features: FeaturesConfig
    
    def __post_init__(self):
        # Ensure exchanges dict has proper types
        if "hyperliquid" in self.exchanges:
            if not isinstance(self.exchanges["hyperliquid"], HyperliquidConfig):
                self.exchanges["hyperliquid"] = HyperliquidConfig(**self.exchanges["hyperliquid"])
        
        if "aster" in self.exchanges:
            if not isinstance(self.exchanges["aster"], AsterConfig):
                self.exchanges["aster"] = AsterConfig(**self.exchanges["aster"])


class ConfigManager:
    """Configuration manager for exchange services"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "config.json"
        self.config: Optional[ServiceConfig] = None
    
    def load_config(self) -> ServiceConfig:
        """Load configuration from file"""
        try:
            config_file = Path(self.config_path)
            
            if not config_file.exists():
                raise ConfigurationError(f"Configuration file not found: {self.config_path}")
            
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # Remove comments if present
            if "_comments" in config_data:
                del config_data["_comments"]
            
            # Create configuration objects
            telegram_config = TelegramConfig(**config_data.get("telegram", {}))
            
            exchanges_config = {}
            if "hyperliquid" in config_data.get("exchanges", {}):
                exchanges_config["hyperliquid"] = HyperliquidConfig(**config_data["exchanges"]["hyperliquid"])
            if "aster" in config_data.get("exchanges", {}):
                exchanges_config["aster"] = AsterConfig(**config_data["exchanges"]["aster"])
            
            trading_config = TradingConfig(**config_data.get("trading", {}))
            risk_config = RiskManagementConfig(**config_data.get("risk_management", {}))
            alerts_config = AlertsConfig(**config_data.get("alerts", {}))
            storage_config = StorageConfig(**config_data.get("storage", {}))
            logging_config = LoggingConfig(**config_data.get("logging", {}))
            security_config = SecurityConfig(**config_data.get("security", {}))
            features_config = FeaturesConfig(**config_data.get("features", {}))
            
            self.config = ServiceConfig(
                telegram=telegram_config,
                exchanges=exchanges_config,
                trading=trading_config,
                risk_management=risk_config,
                alerts=alerts_config,
                storage=storage_config,
                logging=logging_config,
                security=security_config,
                features=features_config
            )
            
            # Validate configuration
            self.validate_config()
            
            # Configuration loading logging removed to reduce verbosity
            return self.config
            
        except Exception as e:
            raise ConfigurationError(f"Failed to load configuration: {e}")
    
    def save_config(self, config: Optional[ServiceConfig] = None) -> None:
        """Save configuration to file"""
        try:
            config_to_save = config or self.config
            if not config_to_save:
                raise ConfigurationError("No configuration to save")
            
            config_file = Path(self.config_path)
            config_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert to dict
            config_dict = asdict(config_to_save)
            
            # Add comments
            config_dict["_comments"] = {
                "description": "DEX Trading Telegram Bot配置文件",
                "version": "1.0.0",
                "last_updated": "2024-01-01"
            }
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
            
            # Configuration saving logging removed to reduce verbosity
            
        except Exception as e:
            raise ConfigurationError(f"Failed to save configuration: {e}")
    
    def validate_config(self) -> None:
        """Validate configuration"""
        if not self.config:
            raise ConfigurationError("No configuration loaded")
        
        # Validate required fields
        if not self.config.telegram.bot_token:
            raise ValidationError("Telegram bot token is required")
        
        if not self.config.telegram.chat_id:
            raise ValidationError("Telegram chat ID is required")
        
        # Validate exchange configurations
        for exchange_name, exchange_config in self.config.exchanges.items():
            if not exchange_config.enabled:
                continue
            
            if exchange_name == "hyperliquid":
                if not exchange_config.account_address:
                    raise ValidationError("Hyperliquid account address is required")
                if not exchange_config.secret_key:
                    raise ValidationError("Hyperliquid secret key is required")
            
            elif exchange_name == "aster":
                if not exchange_config.api_key:
                    raise ValidationError("Aster API key is required")
                if not exchange_config.api_secret:
                    raise ValidationError("Aster API secret is required")
        
        # Validate security configuration
        if not self.config.security.encryption_key:
            raise ValidationError("Encryption key is required")
        
        if len(self.config.security.encryption_key) < 32:
            raise ValidationError("Encryption key must be at least 32 characters")
        
        # Configuration validation logging removed to reduce verbosity
    
    def get_exchange_config(self, exchange_name: str) -> Optional[Union[HyperliquidConfig, AsterConfig]]:
        """Get exchange configuration"""
        if not self.config:
            return None
        
        return self.config.exchanges.get(exchange_name)
    
    def is_exchange_enabled(self, exchange_name: str) -> bool:
        """Check if exchange is enabled"""
        exchange_config = self.get_exchange_config(exchange_name)
        return exchange_config is not None and exchange_config.enabled
    
    def get_telegram_config(self) -> Optional[TelegramConfig]:
        """Get Telegram configuration"""
        return self.config.telegram if self.config else None
    
    def get_trading_config(self) -> Optional[TradingConfig]:
        """Get trading configuration"""
        return self.config.trading if self.config else None
    
    def get_risk_config(self) -> Optional[RiskManagementConfig]:
        """Get risk management configuration"""
        return self.config.risk_management if self.config else None
    
    def get_alerts_config(self) -> Optional[AlertsConfig]:
        """Get alerts configuration"""
        return self.config.alerts if self.config else None
    
    def get_storage_config(self) -> Optional[StorageConfig]:
        """Get storage configuration"""
        return self.config.storage if self.config else None
    
    def get_logging_config(self) -> Optional[LoggingConfig]:
        """Get logging configuration"""
        return self.config.logging if self.config else None
    
    def get_security_config(self) -> Optional[SecurityConfig]:
        """Get security configuration"""
        return self.config.security if self.config else None
    
    def get_features_config(self) -> Optional[FeaturesConfig]:
        """Get features configuration"""
        return self.config.features if self.config else None
    
    def create_example_config(self, output_path: str = "config.example.json") -> None:
        """Create example configuration file"""
        try:
            example_config = ServiceConfig(
                telegram=TelegramConfig(
                    bot_token="YOUR_BOT_TOKEN_HERE",
                    chat_id="YOUR_CHAT_ID_HERE"
                ),
                exchanges={
                    "hyperliquid": HyperliquidConfig(
                        account_address="0x...",
                        secret_key="0x..."
                    ),
                    "aster": AsterConfig(
                        api_key="YOUR_API_KEY",
                        api_secret="YOUR_API_SECRET"
                    )
                },
                trading=TradingConfig(),
                risk_management=RiskManagementConfig(),
                alerts=AlertsConfig(),
                storage=StorageConfig(),
                logging=LoggingConfig(),
                security=SecurityConfig(
                    encryption_key="your_32_byte_encryption_key_here"
                ),
                features=FeaturesConfig()
            )
            
            config_dict = asdict(example_config)
            config_dict["_comments"] = {
                "description": "DEX Trading Telegram Bot配置示例文件",
                "instructions": "复制此文件为config.json并填入您的配置信息"
            }
            
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Example configuration created at {output_path}")
            
        except Exception as e:
            raise ConfigurationError(f"Failed to create example configuration: {e}")


def load_config(config_path: Optional[str] = None) -> ServiceConfig:
    """Load configuration from file"""
    config_manager = ConfigManager(config_path)
    return config_manager.load_config()


def create_example_config(output_path: str = "config.example.json") -> None:
    """Create example configuration file"""
    config_manager = ConfigManager()
    config_manager.create_example_config(output_path)
