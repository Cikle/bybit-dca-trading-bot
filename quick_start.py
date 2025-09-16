#!/usr/bin/env python3
"""
Quick Start Script for Leveraged Grid + DCA Hybrid Trading Bot
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Quick start setup"""
    print("🚀 Leveraged Grid + DCA Hybrid Trading Bot - Quick Start")
    print("=" * 60)
    
    # Check if .env exists
    if not Path('.env').exists():
        print("📝 Setting up environment file...")
        if Path('env.example').exists():
            import shutil
            shutil.copy('env.example', '.env')
            print("✅ Created .env file from env.example")
            print("⚠️  Please edit .env file with your Bybit API keys")
        else:
            print("❌ env.example file not found")
            return 1
    
    # Check if dependencies are installed
    print("\n📦 Checking dependencies...")
    try:
        import pybit
        import pandas
        import numpy
        import loguru
        import rich
        import typer
        print("✅ All dependencies are installed")
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Installing dependencies...")
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
            print("✅ Dependencies installed successfully")
        except subprocess.CalledProcessError:
            print("❌ Failed to install dependencies")
            return 1
    
    # Create necessary directories
    print("\n📁 Creating directories...")
    directories = ['logs', 'data', 'backtests']
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created directory: {directory}")
    
    # Run test setup
    print("\n🧪 Running setup tests...")
    try:
        result = subprocess.run([sys.executable, 'test_setup.py'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Setup tests passed")
        else:
            print("❌ Setup tests failed")
            print(result.stdout)
            print(result.stderr)
            return 1
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return 1
    
    print("\n" + "=" * 60)
    print("🎉 Quick start completed successfully!")
    print("\nNext steps:")
    print("1. Edit .env file with your Bybit API keys")
    print("2. Configure your trading parameters in .env")
    print("3. Test with demo mode: python main.py start --demo")
    print("4. Check status: python main.py status")
    print("5. Run backtest: python main.py backtest")
    print("\nFor help: python main.py --help")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
