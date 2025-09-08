@echo off
echo 分步编译GNSS定位软件...
echo.

REM 编译缺失的test_src.cpp
echo 编译 test_src.cpp...
g++ -c -o test_src.o src/test_src.cpp -I src -I src/Nequick/lib/private -I src/Nequick/lib/public -D WIN32 -D NDEBUG -D _CONSOLE -D _CRT_SECURE_NO_DEPRECATE -D ENAGLO -D ENACMP -D ENAGAL -D NFREQ=6 -D TRACE -std=c++11 -O2

if errorlevel 1 (
    echo test_src.cpp 编译失败！
    pause
    exit /b 1
)

echo test_src.cpp 编译成功！

REM 现在尝试链接
echo 开始链接...
g++ -o rnx2rtkp.exe *.o

if errorlevel 1 (
    echo 链接失败！检查错误信息...
    echo.
    echo 尝试使用现有的.o文件进行链接...
    g++ -o rnx2rtkp.exe main.o bdgim.o bdssh.o common.o datum.o DBSCAN.o ephemeris.o geoid.o ionex.o lambda.o options.o pntpos.o postpos.o ppp.o ppp_ar.o ppp_corr.o preceph.o qzslex.o rinex.o rtcm.o rtcm2.o rtcm3.o rtcm3e.o rtkcmn.o rtkpos.o sbas.o solution.o test_src.o tides.o tle.o
) else (
    echo 链接成功！生成 rnx2rtkp.exe
    echo.
    echo 检查可执行文件...
    if exist "rnx2rtkp.exe" (
        echo 可执行文件已生成！
        echo.
        echo 运行程序...
        rnx2rtkp.exe -k IGS-Data/GNSS_Option.opt -x 5
    ) else (
        echo 错误：可执行文件未生成！
    )
)

pause




