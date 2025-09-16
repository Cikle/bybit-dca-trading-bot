@echo off
echo Testing Python...
python --version
echo.
echo Testing imports...
python -c "print('Python is working')"
echo.
echo Testing config...
python -c "import sys; sys.path.append('src'); from config import Config; print('Config import successful')"
pause
