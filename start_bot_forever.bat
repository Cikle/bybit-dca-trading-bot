@echo off
echo ========================================
echo   Auto-Recovery Trading Bot Launcher
echo ========================================
echo.
echo This will start your trading bot with auto-recovery
echo The bot will automatically restart if it crashes
echo.
echo Press Ctrl+C to stop the bot
echo.
pause

python run_forever.py

echo.
echo Bot has stopped.
pause
