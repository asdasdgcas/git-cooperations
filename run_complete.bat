@echo off
chcp 65001 >nul
title GNSS-STAMP 完整运行系统
color 0A

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                    GNSS-STAMP 完整运行系统                    ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

REM 检查Python是否安装
echo [1/4] 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误：未找到Python，请先安装Python 3.7+
    echo 下载地址：https://www.python.org/downloads/
    pause
    exit /b 1
)
echo ✅ Python环境检查通过

REM 检查必要文件
echo.
echo [2/4] 检查必要文件...
if not exist "rnx2rtkp.exe" (
    echo ❌ 错误：未找到 rnx2rtkp.exe
    echo 请先运行 build.bat 编译程序
    pause
    exit /b 1
)

if not exist "stamp_improved.py" (
    echo ❌ 错误：未找到 stamp_improved.py
    pause
    exit /b 1
)

if not exist "gnss_stamp_integration.py" (
    echo ❌ 错误：未找到 gnss_stamp_integration.py
    pause
    exit /b 1
)

if not exist "IGS-Data/GNSS_Option.opt" (
    echo ❌ 错误：未找到配置文件 IGS-Data/GNSS_Option.opt
    pause
    exit /b 1
)
echo ✅ 必要文件检查通过

REM 检查数据文件
echo.
echo [3/4] 检查GNSS数据文件...
if not exist "IGS-Data\JBDH\2025\121\JBDH_2025_121_WUH2_B_D.pos" (
    echo ⚠️  GNSS数据文件不存在，需要先生成
    echo.
    set /p choice="是否现在运行GNSS定位软件生成数据？(y/n): "
    if /i "%choice%"=="y" (
        echo.
        echo 🔄 正在运行GNSS定位软件...
        echo 使用配置文件：IGS-Data/GNSS_Option.opt
        echo.
        
        REM 确保输出目录存在
        if not exist "IGS-Data\JBDH\2025\121" (
            mkdir "IGS-Data\JBDH\2025\121"
        )
        
        rnx2rtkp.exe -k IGS-Data/GNSS_Option.opt -x 5
        
        if errorlevel 1 (
            echo ❌ GNSS定位软件运行失败
            pause
            exit /b 1
        )
        
        echo ✅ GNSS定位数据生成完成
    ) else (
        echo ❌ 需要GNSS数据文件才能继续
        pause
        exit /b 1
    )
) else (
    echo ✅ GNSS数据文件已存在
)

REM 运行STAMP处理
echo.
echo [4/4] 运行STAMP处理系统...
echo 🚀 启动GNSS-STAMP集成系统...
echo.

REM 清空之前的日志
if exist "gnss_stamp.log" del "gnss_stamp.log"

REM 运行Python程序
python run_gnss_stamp.py -t

if errorlevel 1 (
    echo ❌ STAMP处理失败
    pause
    exit /b 1
)

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                        处理完成！                            ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
echo 📊 查看 gnss_stamp.log 文件获取详细日志
echo 📁 输出文件位置：IGS-Data\JBDH\2025\121\
echo.

REM 询问是否查看日志
set /p view_log="是否现在查看日志文件？(y/n): "
if /i "%view_log%"=="y" (
    if exist "gnss_stamp.log" (
        echo.
        echo 📋 日志文件内容：
        echo ═══════════════════════════════════════════════════════════════
        type "gnss_stamp.log"
        echo ═══════════════════════════════════════════════════════════════
    ) else (
        echo ❌ 日志文件不存在
    )
)

echo.
pause
