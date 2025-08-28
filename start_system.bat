@echo off
echo 🎬 Video Caption Enhancement System - Startup Script
echo ============================================================

echo.
echo 🔍 Verifying setup...
"C:/Program Files/Python312/python.exe" test_setup.py

echo.
echo 🚀 Starting FastAPI backend...
echo Backend will be available at: http://localhost:8000
echo.

start "FastAPI Backend" cmd /k ""C:/Program Files/Python312/python.exe" main.py"

timeout /t 10 /nobreak >nul

echo.
echo 🌐 Starting Streamlit frontend...
echo Frontend will be available at: http://localhost:8502
echo.

start "Streamlit Frontend" cmd /k ""C:/Program Files/Python312/python.exe" -m streamlit run app.py --server.port=8502 --server.headless=true"

timeout /t 5 /nobreak >nul

echo.
echo ✅ Both services are starting...
echo 🌐 Opening browser to: http://localhost:8502
start http://localhost:8502
echo.
echo 📖 Check the README.md for usage instructions
echo.
pause
