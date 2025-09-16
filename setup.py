#!/usr/bin/env python3
"""
Setup script for Leveraged Grid + DCA Hybrid Trading Bot
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

def create_directories():
    """Create necessary directories"""
    directories = [
        'logs',
        'data',
        'backtests',
        'config'
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✓ Created directory: {directory}")

def setup_environment():
    """Set up environment file"""
    env_example = Path('env.example')
    env_file = Path('.env')
    
    if not env_file.exists():
        if env_example.exists():
            shutil.copy(env_example, env_file)
            print("✓ Created .env file from env.example")
            print("⚠️  Please edit .env file with your API keys and configuration")
        else:
            print("❌ env.example file not found")
            return False
    else:
        print("✓ .env file already exists")
    
    return True

def install_dependencies():
    """Install Python dependencies"""
    print("Installing Python dependencies...")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        print("✓ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 Setting up Leveraged Grid + DCA Hybrid Trading Bot")
    print("=" * 60)
    
    # Create directories
    create_directories()
    
    # Setup environment
    if not setup_environment():
        return False
    
    # Install dependencies
    if not install_dependencies():
        return False
    
    print("\n" + "=" * 60)
    print("✅ Setup completed successfully!")
    print("\nNext steps:")
    print("1. Edit .env file with your Bybit API keys")
    print("2. Configure your trading parameters in .env")
    print("3. Run: python main.py --help")
    print("4. Start with demo mode: python main.py start --demo")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
