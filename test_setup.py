#!/usr/bin/env python3
"""
Test script to verify the trading bot setup
"""

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

def test_imports():
    """Test if all modules can be imported"""
    print("Testing imports...")
    
    try:
        from src.config import Config
        print("✅ Config module imported successfully")
    except Exception as e:
        print(f"❌ Config import failed: {e}")
        return False
    
    try:
        from src.logger import get_logger
        print("✅ Logger module imported successfully")
    except Exception as e:
        print(f"❌ Logger import failed: {e}")
        return False
    
    try:
        from src.bybit_client import BybitClient
        print("✅ BybitClient module imported successfully")
    except Exception as e:
        print(f"❌ BybitClient import failed: {e}")
        return False
    
    try:
        from src.grid_engine import GridEngine
        print("✅ GridEngine module imported successfully")
    except Exception as e:
        print(f"❌ GridEngine import failed: {e}")
        return False
    
    try:
        from src.dca_engine import DCAEngine
        print("✅ DCAEngine module imported successfully")
    except Exception as e:
        print(f"❌ DCAEngine import failed: {e}")
        return False
    
    try:
        from src.risk_manager import RiskManager
        print("✅ RiskManager module imported successfully")
    except Exception as e:
        print(f"❌ RiskManager import failed: {e}")
        return False
    
    try:
        from src.trading_bot import TradingBot
        print("✅ TradingBot module imported successfully")
    except Exception as e:
        print(f"❌ TradingBot import failed: {e}")
        return False
    
    try:
        from src.backtest import BacktestEngine
        print("✅ BacktestEngine module imported successfully")
    except Exception as e:
        print(f"❌ BacktestEngine import failed: {e}")
        return False
    
    try:
        from src.database import Database
        print("✅ Database module imported successfully")
    except Exception as e:
        print(f"❌ Database import failed: {e}")
        return False
    
    return True

def test_config():
    """Test configuration loading"""
    print("\nTesting configuration...")
    
    try:
        from src.config import Config
        config = Config.load()
        
        print(f"✅ Configuration loaded successfully")
        print(f"   Symbol: {config.trading.symbol}")
        print(f"   Leverage: {config.trading.leverage}")
        print(f"   Grid levels: {config.grid.levels}")
        print(f"   DCA enabled: {config.dca.enabled}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_dependencies():
    """Test if all required dependencies are available"""
    print("\nTesting dependencies...")
    
    required_packages = [
        'pybit',
        'pandas',
        'numpy',
        'loguru',
        'rich',
        'typer',
        'dotenv'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} is available")
        except ImportError:
            print(f"❌ {package} is missing")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n❌ Missing packages: {', '.join(missing_packages)}")
        print("Run: pip install -r requirements.txt")
        return False
    
    return True

def test_file_structure():
    """Test if all required files exist"""
    print("\nTesting file structure...")
    
    required_files = [
        'env.example',
        'requirements.txt',
        'setup.py',
        'main.py',
        'README.md',
        'src/__init__.py',
        'src/config.py',
        'src/logger.py',
        'src/bybit_client.py',
        'src/grid_engine.py',
        'src/dca_engine.py',
        'src/risk_manager.py',
        'src/trading_bot.py',
        'src/backtest.py',
        'src/database.py'
    ]
    
    missing_files = []
    
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path} exists")
        else:
            print(f"❌ {file_path} is missing")
            missing_files.append(file_path)
    
    if missing_files:
        print(f"\n❌ Missing files: {', '.join(missing_files)}")
        return False
    
    return True

def main():
    """Run all tests"""
    print("🚀 Testing Leveraged Grid + DCA Hybrid Trading Bot Setup")
    print("=" * 60)
    
    tests = [
        test_file_structure,
        test_dependencies,
        test_imports,
        test_config
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 60)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("✅ All tests passed! The bot is ready to use.")
        print("\nNext steps:")
        print("1. Copy env.example to .env")
        print("2. Edit .env with your API keys")
        print("3. Run: python main.py start --demo")
    else:
        print("❌ Some tests failed. Please fix the issues above.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
