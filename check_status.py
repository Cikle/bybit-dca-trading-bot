#!/usr/bin/env python3
"""
Quick Status Checker
Simple script to quickly check if your bot is running and healthy
"""

import subprocess
import sys
import os
from datetime import datetime

def check_bot_status():
    """Quick status check"""
    print("🤖 Trading Bot Status Check")
    print("=" * 40)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Check if auto-recovery bot is running
    try:
        result = subprocess.run([
            sys.executable, "monitor_bot.py"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ Bot is running and healthy!")
        else:
            print("❌ Bot has issues or is not running")
            print("💡 Run 'python run_forever.py' to start with auto-recovery")
    except Exception as e:
        print(f"❌ Error checking status: {e}")
        print("💡 Run 'python run_forever.py' to start with auto-recovery")
    
    print()
    print("📊 Quick Commands:")
    print("  python run_forever.py     - Start bot with auto-recovery")
    print("  python monitor_bot.py     - Detailed health check")
    print("  start_bot_forever.bat     - Windows batch file")

if __name__ == "__main__":
    check_bot_status()
