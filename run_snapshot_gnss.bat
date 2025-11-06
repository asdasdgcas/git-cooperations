@echo off
chcp 65001 >nul
title 快照GNSS-STAMP处理系统

echo.
echo ==========================================
echo    快照GNSS-STAMP处理系统
echo ==========================================
echo    获取当前时刻的GNSS数据并进行STAMP编码
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
if not exist "run_snapshot_gnss.py" (
    echo ❌ 错误: 找不到 run_snapshot_gnss.py 文件
    pause
    exit /b 1
)

if not exist "snapshot_gnss_stamp.py" (
    echo ❌ 错误: 找不到 snapshot_gnss_stamp.py 文件
    pause
    exit /b 1
)

echo ✅ 环境检查通过
echo.

REM 显示菜单
:menu
echo 请选择操作:
echo   1. 快速获取快照 (推荐)
echo   2. 配置系统
echo   3. 查看帮助
echo   4. 退出
echo.

set /p choice="请输入选择 (1-4): "

if "%choice%"=="1" (
    echo.
    echo 📸 启动快照获取...
    python run_snapshot_gnss.py --quick
    echo.
    echo 📊 快照获取完成！
    echo 💡 提示: 查看 IGS-Data/STAMP-Snapshot 目录中的输出文件
    echo.
    pause
    goto menu
) else if "%choice%"=="2" (
    echo.
    echo ⚙️ 进入配置模式...
    python run_snapshot_gnss.py --config
    echo.
    pause
    goto menu
) else if "%choice%"=="3" (
    echo.
    python run_snapshot_gnss.py --help
    echo.
    pause
    goto menu
) else if "%choice%"=="4" (
    goto end
) else (
    echo.
    echo ❌ 无效选择，请重新输入
    echo.
    goto menu
)

:end
echo.
echo 👋 感谢使用快照GNSS-STAMP处理系统
pause

