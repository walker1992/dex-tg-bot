#!/usr/bin/env python3
"""
Configuration Setup Script for DEX Trading Telegram Bot
"""
import json
import sys
from pathlib import Path

def create_config():
    """Create configuration file interactively"""
    print("🤖 DEX Trading Telegram Bot - Configuration Setup")
    print("=" * 50)
    
    config = {
        "_comments": {
            "description": "DEX Trading Telegram Bot配置文件",
            "version": "1.0.0",
            "last_updated": "2024-01-01"
        },
        "telegram": {},
        "exchanges": {
            "hyperliquid": {},
            "aster": {}
        },
        "trading": {},
        "risk_management": {},
        "alerts": {},
        "storage": {},
        "logging": {},
        "security": {},
        "features": {}
    }
    
    # Telegram configuration
    print("\n📱 Telegram Bot Configuration:")
    config["telegram"]["bot_token"] = input("Enter your Telegram Bot Token: ").strip()
    config["telegram"]["chat_id"] = input("Enter your Chat ID: ").strip()
    config["telegram"]["webhook_url"] = ""
    config["telegram"]["webhook_port"] = 8443
    config["telegram"]["allowed_users"] = []
    config["telegram"]["admin_users"] = []
    
    # Hyperliquid configuration
    print("\n🔷 Hyperliquid Configuration:")
    config["exchanges"]["hyperliquid"]["enabled"] = input("Enable Hyperliquid? (y/n): ").lower() == 'y'
    if config["exchanges"]["hyperliquid"]["enabled"]:
        config["exchanges"]["hyperliquid"]["account_address"] = input("Enter Hyperliquid Account Address: ").strip()
        config["exchanges"]["hyperliquid"]["secret_key"] = input("Enter Hyperliquid Secret Key: ").strip()
        config["exchanges"]["hyperliquid"]["base_url"] = "https://api.hyperliquid.xyz"
        config["exchanges"]["hyperliquid"]["testnet"] = False
        config["exchanges"]["hyperliquid"]["rate_limit"] = {
            "requests_per_minute": 60,
            "burst_limit": 10
        }
    
    # Aster configuration
    print("\n🔶 Aster Configuration:")
    config["exchanges"]["aster"]["enabled"] = input("Enable Aster? (y/n): ").lower() == 'y'
    if config["exchanges"]["aster"]["enabled"]:
        config["exchanges"]["aster"]["api_key"] = input("Enter Aster API Key: ").strip()
        config["exchanges"]["aster"]["api_secret"] = input("Enter Aster API Secret: ").strip()
        config["exchanges"]["aster"]["base_url"] = "https://fapi.asterdex.com"
        config["exchanges"]["aster"]["spot_base_url"] = "https://sapi.asterdex.com"
        config["exchanges"]["aster"]["testnet"] = False
        config["exchanges"]["aster"]["rate_limit"] = {
            "requests_per_minute": 1200,
            "weight_limit": 1200
        }
    
    # Security configuration
    print("\n🔐 Security Configuration:")
    encryption_key = input("Enter encryption key (32+ characters) or press Enter to generate: ").strip()
    if not encryption_key:
        import secrets
        import string
        encryption_key = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
        print(f"Generated encryption key: {encryption_key}")
    
    config["security"]["encryption_key"] = encryption_key
    config["security"]["session_timeout"] = 3600
    config["security"]["max_login_attempts"] = 5
    config["security"]["lockout_duration"] = 300
    
    # Default configurations
    config["trading"] = {
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
    
    config["risk_management"] = {
        "daily_loss_limit": 100.0,
        "max_drawdown_percent": 10.0,
        "emergency_stop_enabled": True,
        "position_size_limit": 0.1,
        "correlation_limit": 0.8
    }
    
    config["alerts"] = {
        "price_alerts": {
            "enabled": True,
            "max_alerts_per_user": 20,
            "check_interval": 5
        },
        "funding_rate_alerts": {
            "enabled": True,
            "threshold": 0.0001,
            "check_interval": 60
        },
        "position_alerts": {
            "enabled": True,
            "pnl_threshold": 50.0,
            "margin_ratio_threshold": 0.2
        }
    }
    
    config["storage"] = {
        "type": "csv",
        "data_dir": "data",
        "backup_enabled": True,
        "backup_interval_hours": 24
    }
    
    config["logging"] = {
        "level": "INFO",
        "file": "logs/bot.log",
        "max_bytes": 10485760,
        "backup_count": 5,
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    }
    
    config["features"] = {
        "spot_trading": True,
        "futures_trading": True,
        "funding_rate_monitoring": True,
        "portfolio_tracking": True,
        "backtesting": False,
        "paper_trading": False
    }
    
    return config

def save_config(config, filename="config.json"):
    """Save configuration to file"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print(f"\n✅ Configuration saved to {filename}")
        return True
    except Exception as e:
        print(f"\n❌ Failed to save configuration: {e}")
        return False

def main():
    """Main setup function"""
    try:
        # Check if config already exists
        if Path("config.json").exists():
            overwrite = input("config.json already exists. Overwrite? (y/n): ").lower()
            if overwrite != 'y':
                print("Setup cancelled.")
                return
        
        # Create configuration
        config = create_config()
        
        # Save configuration
        if save_config(config):
            print("\n🎉 Configuration setup completed!")
            print("\nNext steps:")
            print("1. Review your config.json file")
            print("2. Run: python test_bot.py")
            print("3. Start the bot: python start_bot.py")
        else:
            print("\n❌ Configuration setup failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
