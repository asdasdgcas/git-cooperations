@echo off
echo 正在运行GNSS定位软件...

REM 确保输出目录存在
if not exist "IGS-Data\JBDH\2025\121" (
    mkdir "IGS-Data\JBDH\2025\121"
)

REM 运行程序
rnx2rtkp.exe -k IGS-Data/GNSS_Option.opt -x 5

echo 程序运行完成！
pause
