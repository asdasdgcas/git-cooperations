@echo off
chcp 65001 >nul
echo   GNSS-STAMP集成系统
echo ================================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo  错误：未找到Python，请先安装Python 3.7+
    pause
    exit /b 1
)

REM 检查必要文件是否存在
if not exist "stamp_improved.py" (
    echo  错误：找不到 stamp_improved.py 文件
    pause
    exit /b 1
)

if not exist "gnss_stamp_integration.py" (
    echo  错误：找不到 gnss_stamp_integration.py 文件
    pause
    exit /b 1
)

REM 检查GNSS数据文件
if not exist "IGS-Data\JBDH\2025\121\JBDH_2025_121_WUH2_B_D.pos" (
    echo   警告：找不到GNSS数据文件
    echo 请先运行 run.bat 生成定位数据
    echo.
    set /p choice="是否继续？(y/n): "
    if /i not "%choice%"=="y" exit /b 1
)

echo 🚀 启动GNSS-STAMP集成系统...
echo.

REM 运行Python程序
python run_gnss_stamp.py -t

echo.
echo 📊 处理完成！查看 gnss_stamp.log 获取详细日志
echo.
pause
