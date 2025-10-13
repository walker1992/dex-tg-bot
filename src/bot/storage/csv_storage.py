"""
CSV Storage System for Bot Data
"""
import csv
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, asdict

from bot.utils.exceptions import StorageError

logger = logging.getLogger(__name__)


@dataclass
class User:
    """User data model"""
    telegram_id: int
    username: str
    first_name: str
    last_name: str
    is_active: bool = True
    created_at: str = ""
    updated_at: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = datetime.now().isoformat()


@dataclass
class ExchangeAccount:
    """Exchange account data model"""
    user_id: int
    exchange: str
    api_key_encrypted: str
    api_secret_encrypted: str
    is_active: bool = True
    created_at: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


@dataclass
class AlertSetting:
    """Alert setting data model"""
    user_id: int
    exchange: str
    symbol: str
    alert_type: str
    condition_type: str
    threshold_value: float
    is_active: bool = True
    created_at: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


@dataclass
class Trade:
    """Trade data model"""
    user_id: int
    exchange: str
    symbol: str
    side: str
    order_type: str
    quantity: float
    price: Optional[float]
    status: str
    order_id: str
    created_at: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


@dataclass
class PriceHistory:
    """Price history data model"""
    exchange: str
    symbol: str
    price: float
    volume: float
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


@dataclass
class FundingRate:
    """Funding rate data model"""
    exchange: str
    symbol: str
    funding_rate: float
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class CSVStorage:
    """CSV-based storage system"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # File paths
        self.users_file = self.data_dir / "users.csv"
        self.exchange_accounts_file = self.data_dir / "exchange_accounts.csv"
        self.alert_settings_file = self.data_dir / "alert_settings.csv"
        self.trades_file = self.data_dir / "trades.csv"
        self.price_history_file = self.data_dir / "price_history.csv"
        self.funding_rates_file = self.data_dir / "funding_rates.csv"
        
        # Initialize files
        self._initialize_files()
    
    def _initialize_files(self):
        """Initialize CSV files with headers if they don't exist"""
        files_config = {
            self.users_file: [
                "telegram_id", "username", "first_name", "last_name", 
                "is_active", "created_at", "updated_at"
            ],
            self.exchange_accounts_file: [
                "user_id", "exchange", "api_key_encrypted", "api_secret_encrypted",
                "is_active", "created_at"
            ],
            self.alert_settings_file: [
                "user_id", "exchange", "symbol", "alert_type", "condition_type",
                "threshold_value", "is_active", "created_at"
            ],
            self.trades_file: [
                "user_id", "exchange", "symbol", "side", "order_type",
                "quantity", "price", "status", "order_id", "created_at"
            ],
            self.price_history_file: [
                "exchange", "symbol", "price", "volume", "timestamp"
            ],
            self.funding_rates_file: [
                "exchange", "symbol", "funding_rate", "timestamp"
            ]
        }
        
        for file_path, headers in files_config.items():
            if not file_path.exists():
                with open(file_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(headers)
                logger.info(f"Initialized CSV file: {file_path}")
    
    def _read_csv(self, file_path: Path) -> List[Dict[str, Any]]:
        """Read data from CSV file"""
        try:
            data = []
            if file_path.exists():
                with open(file_path, 'r', newline='', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    data = list(reader)
            return data
        except Exception as e:
            raise StorageError(f"Failed to read CSV file {file_path}: {e}")
    
    def _write_csv(self, file_path: Path, data: List[Dict[str, Any]], headers: List[str]):
        """Write data to CSV file"""
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
                writer.writerows(data)
        except Exception as e:
            raise StorageError(f"Failed to write CSV file {file_path}: {e}")
    
    def _append_csv(self, file_path: Path, data: Dict[str, Any], headers: List[str]):
        """Append data to CSV file"""
        try:
            with open(file_path, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writerow(data)
        except Exception as e:
            raise StorageError(f"Failed to append to CSV file {file_path}: {e}")
    
    # User management
    def create_user(self, user: User) -> bool:
        """Create a new user"""
        try:
            # Check if user already exists
            existing_users = self._read_csv(self.users_file)
            for existing_user in existing_users:
                if int(existing_user['telegram_id']) == user.telegram_id:
                    logger.warning(f"User {user.telegram_id} already exists")
                    return False
            
            # Add new user
            user_data = asdict(user)
            headers = list(user_data.keys())
            self._append_csv(self.users_file, user_data, headers)
            
            logger.info(f"Created user: {user.telegram_id} (@{user.username})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            raise StorageError(f"Failed to create user: {e}")
    
    def get_user(self, telegram_id: int) -> Optional[User]:
        """Get user by telegram ID"""
        try:
            users = self._read_csv(self.users_file)
            for user_data in users:
                if int(user_data['telegram_id']) == telegram_id:
                    return User(
                        telegram_id=int(user_data['telegram_id']),
                        username=user_data['username'],
                        first_name=user_data['first_name'],
                        last_name=user_data['last_name'],
                        is_active=user_data['is_active'].lower() == 'true',
                        created_at=user_data['created_at'],
                        updated_at=user_data['updated_at']
                    )
            return None
        except Exception as e:
            logger.error(f"Failed to get user: {e}")
            raise StorageError(f"Failed to get user: {e}")
    
    def update_user(self, user: User) -> bool:
        """Update user information"""
        try:
            users = self._read_csv(self.users_file)
            updated = False
            
            for i, user_data in enumerate(users):
                if int(user_data['telegram_id']) == user.telegram_id:
                    user.updated_at = datetime.now().isoformat()
                    users[i] = asdict(user)
                    updated = True
                    break
            
            if updated:
                headers = list(asdict(user).keys())
                self._write_csv(self.users_file, users, headers)
                logger.info(f"Updated user: {user.telegram_id}")
                return True
            else:
                logger.warning(f"User {user.telegram_id} not found for update")
                return False
                
        except Exception as e:
            logger.error(f"Failed to update user: {e}")
            raise StorageError(f"Failed to update user: {e}")
    
    # Exchange account management
    def create_exchange_account(self, account: ExchangeAccount) -> bool:
        """Create a new exchange account"""
        try:
            account_data = asdict(account)
            headers = list(account_data.keys())
            self._append_csv(self.exchange_accounts_file, account_data, headers)
            
            logger.info(f"Created exchange account: {account.exchange} for user {account.user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create exchange account: {e}")
            raise StorageError(f"Failed to create exchange account: {e}")
    
    def get_exchange_accounts(self, user_id: int) -> List[ExchangeAccount]:
        """Get exchange accounts for a user"""
        try:
            accounts = self._read_csv(self.exchange_accounts_file)
            user_accounts = []
            
            for account_data in accounts:
                if int(account_data['user_id']) == user_id:
                    account = ExchangeAccount(
                        user_id=int(account_data['user_id']),
                        exchange=account_data['exchange'],
                        api_key_encrypted=account_data['api_key_encrypted'],
                        api_secret_encrypted=account_data['api_secret_encrypted'],
                        is_active=account_data['is_active'].lower() == 'true',
                        created_at=account_data['created_at']
                    )
                    user_accounts.append(account)
            
            return user_accounts
            
        except Exception as e:
            logger.error(f"Failed to get exchange accounts: {e}")
            raise StorageError(f"Failed to get exchange accounts: {e}")
    
    def get_exchange_account(self, user_id: int, exchange: str) -> Optional[ExchangeAccount]:
        """Get specific exchange account for a user"""
        try:
            accounts = self.get_exchange_accounts(user_id)
            for account in accounts:
                if account.exchange == exchange:
                    return account
            return None
            
        except Exception as e:
            logger.error(f"Failed to get exchange account: {e}")
            raise StorageError(f"Failed to get exchange account: {e}")
    
    def delete_exchange_account(self, user_id: int, exchange: str) -> bool:
        """Delete exchange account"""
        try:
            accounts = self._read_csv(self.exchange_accounts_file)
            updated_accounts = []
            deleted = False
            
            for account_data in accounts:
                if (int(account_data['user_id']) == user_id and 
                    account_data['exchange'] == exchange):
                    deleted = True
                    logger.info(f"Deleted exchange account: {exchange} for user {user_id}")
                else:
                    updated_accounts.append(account_data)
            
            if deleted:
                headers = list(accounts[0].keys()) if accounts else []
                self._write_csv(self.exchange_accounts_file, updated_accounts, headers)
                return True
            else:
                logger.warning(f"Exchange account {exchange} not found for user {user_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete exchange account: {e}")
            raise StorageError(f"Failed to delete exchange account: {e}")
    
    # Alert management
    def create_alert(self, alert: AlertSetting) -> bool:
        """Create a new alert"""
        try:
            alert_data = asdict(alert)
            headers = list(alert_data.keys())
            self._append_csv(self.alert_settings_file, alert_data, headers)
            
            logger.info(f"Created alert: {alert.alert_type} for {alert.symbol} on {alert.exchange}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create alert: {e}")
            raise StorageError(f"Failed to create alert: {e}")
    
    def get_user_alerts(self, user_id: int) -> List[AlertSetting]:
        """Get alerts for a user"""
        try:
            alerts = self._read_csv(self.alert_settings_file)
            user_alerts = []
            
            for alert_data in alerts:
                if int(alert_data['user_id']) == user_id:
                    alert = AlertSetting(
                        user_id=int(alert_data['user_id']),
                        exchange=alert_data['exchange'],
                        symbol=alert_data['symbol'],
                        alert_type=alert_data['alert_type'],
                        condition_type=alert_data['condition_type'],
                        threshold_value=float(alert_data['threshold_value']),
                        is_active=alert_data['is_active'].lower() == 'true',
                        created_at=alert_data['created_at']
                    )
                    user_alerts.append(alert)
            
            return user_alerts
            
        except Exception as e:
            logger.error(f"Failed to get user alerts: {e}")
            raise StorageError(f"Failed to get user alerts: {e}")
    
    def delete_alert(self, user_id: int, alert_id: str) -> bool:
        """Delete alert by ID"""
        try:
            alerts = self._read_csv(self.alert_settings_file)
            updated_alerts = []
            deleted = False
            
            for alert_data in alerts:
                # Generate alert ID for comparison
                current_alert_id = f"{alert_data['alert_type']}_{alert_data['symbol']}_{alert_data['condition_type']}_{alert_data['threshold_value']}_{alert_data['exchange']}"
                
                if (int(alert_data['user_id']) == user_id and 
                    current_alert_id == alert_id):
                    deleted = True
                    logger.info(f"Deleted alert: {alert_id}")
                else:
                    updated_alerts.append(alert_data)
            
            if deleted:
                headers = list(alerts[0].keys()) if alerts else []
                self._write_csv(self.alert_settings_file, updated_alerts, headers)
                return True
            else:
                logger.warning(f"Alert {alert_id} not found for user {user_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete alert: {e}")
            raise StorageError(f"Failed to delete alert: {e}")
    
    # Trade management
    def create_trade(self, trade: Trade) -> bool:
        """Create a new trade record"""
        try:
            trade_data = asdict(trade)
            headers = list(trade_data.keys())
            self._append_csv(self.trades_file, trade_data, headers)
            
            logger.info(f"Created trade: {trade.side} {trade.quantity} {trade.symbol} on {trade.exchange}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create trade: {e}")
            raise StorageError(f"Failed to create trade: {e}")
    
    def get_user_trades(self, user_id: int, limit: int = 100) -> List[Trade]:
        """Get trades for a user"""
        try:
            trades = self._read_csv(self.trades_file)
            user_trades = []
            
            for trade_data in trades:
                if int(trade_data['user_id']) == user_id:
                    trade = Trade(
                        user_id=int(trade_data['user_id']),
                        exchange=trade_data['exchange'],
                        symbol=trade_data['symbol'],
                        side=trade_data['side'],
                        order_type=trade_data['order_type'],
                        quantity=float(trade_data['quantity']),
                        price=float(trade_data['price']) if trade_data['price'] else None,
                        status=trade_data['status'],
                        order_id=trade_data['order_id'],
                        created_at=trade_data['created_at']
                    )
                    user_trades.append(trade)
            
            # Sort by created_at descending and limit
            user_trades.sort(key=lambda x: x.created_at, reverse=True)
            return user_trades[:limit]
            
        except Exception as e:
            logger.error(f"Failed to get user trades: {e}")
            raise StorageError(f"Failed to get user trades: {e}")
    
    # Price history management
    def add_price_history(self, price_history: PriceHistory) -> bool:
        """Add price history record"""
        try:
            price_data = asdict(price_history)
            headers = list(price_data.keys())
            self._append_csv(self.price_history_file, price_data, headers)
            return True
            
        except Exception as e:
            logger.error(f"Failed to add price history: {e}")
            raise StorageError(f"Failed to add price history: {e}")
    
    def get_price_history(self, exchange: str, symbol: str, limit: int = 100) -> List[PriceHistory]:
        """Get price history for a symbol"""
        try:
            prices = self._read_csv(self.price_history_file)
            symbol_prices = []
            
            for price_data in prices:
                if (price_data['exchange'] == exchange and 
                    price_data['symbol'] == symbol):
                    price = PriceHistory(
                        exchange=price_data['exchange'],
                        symbol=price_data['symbol'],
                        price=float(price_data['price']),
                        volume=float(price_data['volume']),
                        timestamp=price_data['timestamp']
                    )
                    symbol_prices.append(price)
            
            # Sort by timestamp descending and limit
            symbol_prices.sort(key=lambda x: x.timestamp, reverse=True)
            return symbol_prices[:limit]
            
        except Exception as e:
            logger.error(f"Failed to get price history: {e}")
            raise StorageError(f"Failed to get price history: {e}")
    
    # Funding rate management
    def add_funding_rate(self, funding_rate: FundingRate) -> bool:
        """Add funding rate record"""
        try:
            funding_data = asdict(funding_rate)
            headers = list(funding_data.keys())
            self._append_csv(self.funding_rates_file, funding_data, headers)
            return True
            
        except Exception as e:
            logger.error(f"Failed to add funding rate: {e}")
            raise StorageError(f"Failed to add funding rate: {e}")
    
    def get_funding_rates(self, exchange: str, symbol: str, limit: int = 100) -> List[FundingRate]:
        """Get funding rates for a symbol"""
        try:
            rates = self._read_csv(self.funding_rates_file)
            symbol_rates = []
            
            for rate_data in rates:
                if (rate_data['exchange'] == exchange and 
                    rate_data['symbol'] == symbol):
                    rate = FundingRate(
                        exchange=rate_data['exchange'],
                        symbol=rate_data['symbol'],
                        funding_rate=float(rate_data['funding_rate']),
                        timestamp=rate_data['timestamp']
                    )
                    symbol_rates.append(rate)
            
            # Sort by timestamp descending and limit
            symbol_rates.sort(key=lambda x: x.timestamp, reverse=True)
            return symbol_rates[:limit]
            
        except Exception as e:
            logger.error(f"Failed to get funding rates: {e}")
            raise StorageError(f"Failed to get funding rates: {e}")
    
    # Utility methods
    def backup_data(self, backup_dir: str = "data/backups") -> bool:
        """Create backup of all data"""
        try:
            backup_path = Path(backup_dir)
            backup_path.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            files_to_backup = [
                self.users_file,
                self.exchange_accounts_file,
                self.alert_settings_file,
                self.trades_file,
                self.price_history_file,
                self.funding_rates_file
            ]
            
            for file_path in files_to_backup:
                if file_path.exists():
                    backup_file = backup_path / f"{file_path.stem}_{timestamp}.csv"
                    import shutil
                    shutil.copy2(file_path, backup_file)
            
            logger.info(f"Data backup created: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            raise StorageError(f"Failed to create backup: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        try:
            stats = {}
            
            # Count records in each file
            stats['users'] = len(self._read_csv(self.users_file))
            stats['exchange_accounts'] = len(self._read_csv(self.exchange_accounts_file))
            stats['alerts'] = len(self._read_csv(self.alert_settings_file))
            stats['trades'] = len(self._read_csv(self.trades_file))
            stats['price_history'] = len(self._read_csv(self.price_history_file))
            stats['funding_rates'] = len(self._read_csv(self.funding_rates_file))
            
            # File sizes
            stats['file_sizes'] = {}
            for file_path in [
                self.users_file, self.exchange_accounts_file, self.alert_settings_file,
                self.trades_file, self.price_history_file, self.funding_rates_file
            ]:
                if file_path.exists():
                    stats['file_sizes'][file_path.name] = file_path.stat().st_size
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            raise StorageError(f"Failed to get stats: {e}")