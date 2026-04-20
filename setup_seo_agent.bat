@echo off
chcp 65001 >nul
echo ============================================================
echo  SEO 学习助手 - 一键安装 / SEO Learning Assistant Setup
echo ============================================================
echo.

echo [1/3] 检查 Python 版本 / Checking Python version...
python --version
if errorlevel 1 (
    echo.
    echo 错误：未检测到 Python，请先安装 Python 3.9+
    echo Error: Python not found. Please install Python 3.9+ first.
    echo https://www.python.org/downloads/
    pause
    exit /b 1
)

echo.
echo [2/3] 安装依赖包 / Installing dependencies...
pip install requests feedparser beautifulsoup4
if errorlevel 1 (
    echo.
    echo 警告：部分依赖安装失败，请手动运行：
    echo Warning: Some dependencies failed. Run manually:
    echo   pip install requests feedparser beautifulsoup4
    pause
)

echo.
echo [3/3] 启动 SEO 学习助手 / Launching SEO Learning Assistant...
echo.
python seo_desktop_agent.py

pause
