@echo off
echo Stopping existing chat server on port 8001...

:: 查找并杀死监听8001端口的进程
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8001 ^| findstr LISTENING') do (
    echo Killing process PID %%a...
    taskkill /F /PID %%a
)

timeout /t 2 /nobreak >nul

echo Starting new chat server...
echo.
echo ========================================
echo DevOps Agent Chat Server
echo ========================================
echo.
echo Access: http://localhost:8001
echo.
echo Press Ctrl+C to stop the server
echo ========================================
echo.

python start_chat.py