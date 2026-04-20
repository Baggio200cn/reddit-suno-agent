@echo off
chcp 65001 >nul
title Reddit AI 资讯助手 - 安装程序

echo.
echo ================================================
echo   Reddit AI 资讯助手  -  Setup
echo   Designed by Claude Code
echo ================================================
echo.

:: 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.8+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo [OK] Python 已安装

:: 安装依赖
echo.
echo [1/3] 安装 Python 依赖包...
pip install requests pystray Pillow schedule --quiet
if errorlevel 1 (
    echo [警告] 部分依赖安装失败，尝试单独安装...
    pip install requests
    pip install pystray
    pip install Pillow
    pip install schedule
)
echo [OK] 依赖安装完成

:: 创建启动脚本
echo.
echo [2/3] 创建启动脚本...
set "AGENT_DIR=%~dp0"
set "RUN_BAT=%AGENT_DIR%run_agent.bat"

(
echo @echo off
echo cd /d "%AGENT_DIR%"
echo start pythonw "%AGENT_DIR%reddit_desktop_agent.py"
) > "%RUN_BAT%"
echo [OK] run_agent.bat 已创建

:: 注册开机自启
echo.
echo [3/3] 注册开机自启...
set "STARTUP=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
copy /Y "%RUN_BAT%" "%STARTUP%\reddit_ai_agent.bat" >nul
if errorlevel 1 (
    echo [警告] 开机自启注册失败（可能需要管理员权限）
    echo 请手动将 run_agent.bat 复制到:
    echo   %STARTUP%
) else (
    echo [OK] 开机自启已注册
)

:: 完成
echo.
echo ================================================
echo   安装完成！
echo ================================================
echo.
echo 现在可以运行程序：
echo   python reddit_desktop_agent.py
echo.
echo 或直接双击：run_agent.bat
echo.
set /p LAUNCH="是否立即启动程序？[Y/N] "
if /i "%LAUNCH%"=="Y" (
    start pythonw "%AGENT_DIR%reddit_desktop_agent.py"
    echo 程序已在后台启动，请查看系统托盘。
)

echo.
pause
