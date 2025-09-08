@echo off
echo 运行GNSS定位软件...
echo.

REM 检查可执行文件是否存在
if not exist "rnx2rtkp.exe" (
    echo 错误：未找到 rnx2rtkp.exe，请先运行 build.bat 编译程序
    pause
    exit /b 1
)

REM 检查配置文件是否存在
if not exist "IGS-Data/GNSS_Option.opt" (
    echo 错误：未找到配置文件 IGS-Data/GNSS_Option.opt
    pause
    exit /b 1
)

echo 使用配置文件：IGS-Data/GNSS_Option.opt
echo 开始运行程序...
echo.

rnx2rtkp.exe -k IGS-Data/GNSS_Option.opt -x 5

echo.
echo 程序运行完成！
pause
