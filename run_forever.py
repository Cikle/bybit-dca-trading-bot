#!/usr/bin/env python3
"""
Forever Running Bot
Simple script that keeps the bot running forever with auto-recovery
"""

import subprocess
import time
import sys
import os
from datetime import datetime

def run_bot_forever():
    """Run the bot forever with auto-recovery"""
    print("🚀 Starting Forever Bot Runner...")
    print("=" * 60)
    print("This will keep your trading bot running forever with auto-recovery")
    print("Press Ctrl+C to stop")
    print("=" * 60)
    
    restart_count = 0
    last_restart = 0
    
    while True:
        try:
            restart_count += 1
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            print(f"\n🔄 Starting bot (attempt #{restart_count}) - {current_time}")
            
            # Run the auto-recovery bot
            process = subprocess.Popen([
                sys.executable, "auto_recovery_bot.py"
            ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
            
            # Monitor the process
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    print(output.strip())
            
            # Process ended
            return_code = process.poll()
            print(f"\n⚠️ Bot process ended with code: {return_code}")
            
            # Check if we should restart
            time_since_last_restart = time.time() - last_restart
            if time_since_last_restart < 10:  # Less than 10 seconds
                print("⏳ Bot restarted too quickly, waiting 30 seconds...")
                time.sleep(30)
            
            last_restart = time.time()
            print("🔄 Restarting bot in 5 seconds...")
            time.sleep(5)
            
        except KeyboardInterrupt:
            print("\n🛑 Received interrupt signal, stopping...")
            if 'process' in locals():
                process.terminate()
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            print("🔄 Restarting in 10 seconds...")
            time.sleep(10)

if __name__ == "__main__":
    run_bot_forever()
