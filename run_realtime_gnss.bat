@echo off
chcp 65001 >nul
title 实时GNSS-STAMP处理系统

echo.
echo ==========================================
echo    实时GNSS-STAMP处理系统
echo ==========================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未找到Python，请先安装Python
    pause
    exit /b 1
)

REM 检查必要的文件是否存在
if not exist "run_realtime_gnss.py" (
    echo ❌ 错误: 找不到 run_realtime_gnss.py 文件
    pause
    exit /b 1
)

if not exist "realtime_gnss_stamp.py" (
    echo ❌ 错误: 找不到 realtime_gnss_stamp.py 文件
    pause
    exit /b 1
)

echo ✅ 环境检查通过
echo.

REM 显示菜单
:menu
echo 请选择操作:
echo   1. 快速启动 (推荐)
echo   2. 配置系统
echo   3. 测试串口连接
echo   4. 查看帮助
echo   5. 退出
echo.

set /p choice="请输入选择 (1-5): "

if "%choice%"=="1" (
    echo.
    echo 🚀 启动实时处理系统...
    python run_realtime_gnss.py --quick
    goto end
) else if "%choice%"=="2" (
    echo.
    echo ⚙️ 进入配置模式...
    python run_realtime_gnss.py --config
    goto menu
) else if "%choice%"=="3" (
    echo.
    echo 🔧 测试串口连接...
    python run_realtime_gnss.py --test
    echo.
    pause
    goto menu
) else if "%choice%"=="4" (
    echo.
    python run_realtime_gnss.py --help
    echo.
    pause
    goto menu
) else if "%choice%"=="5" (
    goto end
) else (
    echo.
    echo ❌ 无效选择，请重新输入
    echo.
    goto menu
)

:end
echo.
echo 👋 感谢使用实时GNSS-STAMP处理系统
pause
