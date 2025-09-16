#!/usr/bin/env python3
"""
Simple test script for the trading bot
"""

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

def test_basic_imports():
    """Test basic imports"""
    try:
        from src.config import Config
        print("✅ Config import successful")
        
        config = Config.load()
        print("✅ Config loaded successfully")
        print(f"   Symbol: {config.trading.symbol}")
        print(f"   Demo mode: {config.bybit.demo_mode}")
        
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_bybit_connection():
    """Test Bybit connection"""
    try:
        from src.config import Config
        from src.bybit_client import BybitClient
        
        config = Config.load()
        client = BybitClient(config.bybit, config.trading)
        
        if client.connect():
            print("✅ Bybit connection successful")
            return True
        else:
            print("❌ Bybit connection failed")
            return False
            
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 Testing Trading Bot Components")
    print("=" * 40)
    
    # Test imports
    if not test_basic_imports():
        return 1
    
    print()
    
    # Test connection
    if not test_bybit_connection():
        return 1
    
    print()
    print("✅ All tests passed! Bot is ready to use.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
