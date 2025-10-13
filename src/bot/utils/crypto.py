"""
Encryption utilities for secure storage
"""
import base64
import logging
from typing import Optional, List
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from bot.utils.exceptions import BotError

logger = logging.getLogger(__name__)


class CryptoManager:
    """Encryption manager for sensitive data"""
    
    def __init__(self, encryption_key: str):
        """
        Initialize encryption manager
        
        Args:
            encryption_key: Base64 encoded encryption key or password
        """
        self.encryption_key = encryption_key
        self.cipher = self._create_cipher()
    
    def _create_cipher(self) -> Fernet:
        """Create Fernet cipher from encryption key"""
        try:
            # If key is already base64 encoded, use it directly
            if len(self.encryption_key) == 44 and self.encryption_key.endswith('='):
                key = base64.urlsafe_b64decode(self.encryption_key.encode())
            else:
                # Derive key from password using PBKDF2
                salt = b'dex_trading_bot_salt'  # In production, use random salt
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=salt,
                    iterations=100000,
                )
                key = base64.urlsafe_b64encode(kdf.derive(self.encryption_key.encode()))
            
            return Fernet(key)
            
        except Exception as e:
            logger.error(f"Failed to create cipher: {e}")
            raise BotError(f"Failed to initialize encryption: {e}")
    
    def encrypt(self, data: str) -> str:
        """Encrypt string data"""
        try:
            if not data:
                return ""
            
            encrypted_data = self.cipher.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted_data).decode()
            
        except Exception as e:
            logger.error(f"Failed to encrypt data: {e}")
            raise BotError(f"Encryption failed: {e}")
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt string data"""
        try:
            if not encrypted_data:
                return ""
            
            decoded_data = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_data = self.cipher.decrypt(decoded_data)
            return decrypted_data.decode()
            
        except Exception as e:
            logger.error(f"Failed to decrypt data: {e}")
            raise BotError(f"Decryption failed: {e}")
    
    def encrypt_dict(self, data: dict) -> dict:
        """Encrypt sensitive fields in dictionary"""
        try:
            encrypted_data = data.copy()
            
            # Fields to encrypt
            sensitive_fields = [
                'api_key', 'api_secret', 'private_key', 'secret_key',
                'api_key_encrypted', 'api_secret_encrypted'
            ]
            
            for field in sensitive_fields:
                if field in encrypted_data and encrypted_data[field]:
                    encrypted_data[field] = self.encrypt(str(encrypted_data[field]))
            
            return encrypted_data
            
        except Exception as e:
            logger.error(f"Failed to encrypt dict: {e}")
            raise BotError(f"Dict encryption failed: {e}")
    
    def decrypt_dict(self, data: dict) -> dict:
        """Decrypt sensitive fields in dictionary"""
        try:
            decrypted_data = data.copy()
            
            # Fields to decrypt
            sensitive_fields = [
                'api_key_encrypted', 'api_secret_encrypted'
            ]
            
            for field in sensitive_fields:
                if field in decrypted_data and decrypted_data[field]:
                    decrypted_data[field] = self.decrypt(str(decrypted_data[field]))
            
            return decrypted_data
            
        except Exception as e:
            logger.error(f"Failed to decrypt dict: {e}")
            raise BotError(f"Dict decryption failed: {e}")


def generate_encryption_key() -> str:
    """Generate a new encryption key"""
    try:
        key = Fernet.generate_key()
        return base64.urlsafe_b64encode(key).decode()
    except Exception as e:
        logger.error(f"Failed to generate encryption key: {e}")
        raise BotError(f"Key generation failed: {e}")


def validate_encryption_key(key: str) -> bool:
    """Validate encryption key format"""
    try:
        if not key:
            return False
        
        # Check if it's a valid base64 encoded key
        if len(key) == 44 and key.endswith('='):
            base64.urlsafe_b64decode(key.encode())
            return True
        
        # Check if it's a password (minimum 8 characters)
        if len(key) >= 8:
            return True
        
        return False
        
    except Exception:
        return False


class SecureStorage:
    """Secure storage wrapper with encryption"""
    
    def __init__(self, storage, crypto_manager: CryptoManager):
        self.storage = storage
        self.crypto = crypto_manager
    
    def create_exchange_account(self, account_data: dict) -> bool:
        """Create exchange account with encrypted credentials"""
        try:
            # Encrypt sensitive data
            encrypted_data = self.crypto.encrypt_dict(account_data)
            
            # Create account object
            from bot.storage.csv_storage import ExchangeAccount
            account = ExchangeAccount(
                user_id=encrypted_data['user_id'],
                exchange=encrypted_data['exchange'],
                api_key_encrypted=encrypted_data.get('api_key_encrypted', ''),
                api_secret_encrypted=encrypted_data.get('api_secret_encrypted', ''),
                is_active=encrypted_data.get('is_active', True)
            )
            
            return self.storage.create_exchange_account(account)
            
        except Exception as e:
            logger.error(f"Failed to create secure exchange account: {e}")
            raise BotError(f"Secure account creation failed: {e}")
    
    def get_exchange_account(self, user_id: int, exchange: str) -> Optional[dict]:
        """Get exchange account with decrypted credentials"""
        try:
            account = self.storage.get_exchange_account(user_id, exchange)
            if not account:
                return None
            
            # Decrypt sensitive data
            account_dict = {
                'user_id': account.user_id,
                'exchange': account.exchange,
                'api_key_encrypted': account.api_key_encrypted,
                'api_secret_encrypted': account.api_secret_encrypted,
                'is_active': account.is_active,
                'created_at': account.created_at
            }
            
            decrypted_data = self.crypto.decrypt_dict(account_dict)
            
            # Add decrypted fields
            decrypted_data['api_key'] = decrypted_data.get('api_key_encrypted', '')
            decrypted_data['api_secret'] = decrypted_data.get('api_secret_encrypted', '')
            
            return decrypted_data
            
        except Exception as e:
            logger.error(f"Failed to get secure exchange account: {e}")
            raise BotError(f"Secure account retrieval failed: {e}")
    
    def get_exchange_accounts(self, user_id: int) -> List[dict]:
        """Get all exchange accounts with decrypted credentials"""
        try:
            accounts = self.storage.get_exchange_accounts(user_id)
            decrypted_accounts = []
            
            for account in accounts:
                account_dict = {
                    'user_id': account.user_id,
                    'exchange': account.exchange,
                    'api_key_encrypted': account.api_key_encrypted,
                    'api_secret_encrypted': account.api_secret_encrypted,
                    'is_active': account.is_active,
                    'created_at': account.created_at
                }
                
                decrypted_data = self.crypto.decrypt_dict(account_dict)
                decrypted_data['api_key'] = decrypted_data.get('api_key_encrypted', '')
                decrypted_data['api_secret'] = decrypted_data.get('api_secret_encrypted', '')
                
                decrypted_accounts.append(decrypted_data)
            
            return decrypted_accounts
            
        except Exception as e:
            logger.error(f"Failed to get secure exchange accounts: {e}")
            raise BotError(f"Secure accounts retrieval failed: {e}")


# Global crypto manager instance
_crypto_manager = None


def get_crypto_manager(encryption_key: str = None) -> CryptoManager:
    """Get global crypto manager instance"""
    global _crypto_manager
    
    if _crypto_manager is None:
        if not encryption_key:
            raise BotError("Encryption key is required")
        _crypto_manager = CryptoManager(encryption_key)
    
    return _crypto_manager


def set_crypto_manager(crypto_manager: CryptoManager):
    """Set global crypto manager instance"""
    global _crypto_manager
    _crypto_manager = crypto_manager
