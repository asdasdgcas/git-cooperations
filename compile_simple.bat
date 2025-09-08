@echo off
echo 正在编译GNSS定位软件（简化版本）...
echo.

REM 先编译主要的C++文件，不包含Nequick库
g++ -c -o main.o app/main/rnx2rtkp.cpp -I src -I src/Nequick/lib/private -I src/Nequick/lib/public -D WIN32 -D NDEBUG -D _CONSOLE -D _CRT_SECURE_NO_DEPRECATE -D ENAGLO -D ENACMP -D ENAGAL -D NFREQ=6 -D TRACE -std=c++11 -O2

if errorlevel 1 (
    echo 主程序编译失败！
    pause
    exit /b 1
)

echo 主程序编译成功！

REM 编译其他源文件
g++ -c -o bdgim.o src/bdgim.cpp -I src -I src/Nequick/lib/private -I src/Nequick/lib/public -D WIN32 -D NDEBUG -D _CONSOLE -D _CRT_SECURE_NO_DEPRECATE -D ENAGLO -D ENACMP -D ENAGAL -D NFREQ=6 -D TRACE -std=c++11 -O2
g++ -c -o bdssh.o src/bdssh.cpp -I src -I src/Nequick/lib/private -I src/Nequick/lib/public -D WIN32 -D NDEBUG -D _CONSOLE -D _CRT_SECURE_NO_DEPRECATE -D ENAGLO -D ENACMP -D ENAGAL -D NFREQ=6 -D TRACE -std=c++11 -O2
g++ -c -o common.o src/common.cpp -I src -I src/Nequick/lib/private -I src/Nequick/lib/public -D WIN32 -D NDEBUG -D _CONSOLE -D _CRT_SECURE_NO_DEPRECATE -D ENAGLO -D ENACMP -D ENAGAL -D NFREQ=6 -D TRACE -std=c++11 -O2
g++ -c -o datum.o src/datum.cpp -I src -I src/Nequick/lib/private -I src/Nequick/lib/public -D WIN32 -D NDEBUG -D _CONSOLE -D _CRT_SECURE_NO_DEPRECATE -D ENAGLO -D ENACMP -D ENAGAL -D NFREQ=6 -D TRACE -std=c++11 -O2
g++ -c -o DBSCAN.o src/DBSCAN.cpp -I src -I src/Nequick/lib/private -I src/Nequick/lib/public -D WIN32 -D NDEBUG -D _CONSOLE -D _CRT_SECURE_NO_DEPRECATE -D ENAGLO -D ENACMP -D ENAGAL -D NFREQ=6 -D TRACE -std=c++11 -O2
g++ -c -o ephemeris.o src/ephemeris.cpp -I src -I src/Nequick/lib/private -I src/Nequick/lib/public -D WIN32 -D NDEBUG -D _CONSOLE -D _CRT_SECURE_NO_DEPRECATE -D ENAGLO -D ENACMP -D ENAGAL -D NFREQ=6 -D TRACE -std=c++11 -O2
g++ -c -o geoid.o src/geoid.cpp -I src -I src/Nequick/lib/private -I src/Nequick/lib/public -D WIN32 -D NDEBUG -D _CONSOLE -D _CRT_SECURE_NO_DEPRECATE -D ENAGLO -D ENACMP -D ENAGAL -D NFREQ=6 -D TRACE -std=c++11 -O2
g++ -c -o ionex.o src/ionex.cpp -I src -I src/Nequick/lib/private -I src/Nequick/lib/public -D WIN32 -D NDEBUG -D _CONSOLE -D _CRT_SECURE_NO_DEPRECATE -D ENAGLO -D ENACMP -D ENAGAL -D NFREQ=6 -D TRACE -std=c++11 -O2
g++ -c -o lambda.o src/lambda.cpp -I src -I src/Nequick/lib/private -I src/Nequick/lib/public -D WIN32 -D NDEBUG -D _CONSOLE -D _CRT_SECURE_NO_DEPRECATE -D ENAGLO -D ENACMP -D ENAGAL -D NFREQ=6 -D TRACE -std=c++11 -O2
g++ -c -o options.o src/options.cpp -I src -I src/Nequick/lib/private -I src/Nequick/lib/public -D WIN32 -D NDEBUG -D _CONSOLE -D _CRT_SECURE_NO_DEPRECATE -D ENAGLO -D ENACMP -D ENAGAL -D NFREQ=6 -D TRACE -std=c++11 -O2
g++ -c -o pntpos.o src/pntpos.cpp -I src -I src/Nequick/lib/private -I src/Nequick/lib/public -D WIN32 -D NDEBUG -D _CONSOLE -D _CRT_SECURE_NO_DEPRECATE -D ENAGLO -D ENACMP -D ENAGAL -D NFREQ=6 -D TRACE -std=c++11 -O2
g++ -c -o postpos.o src/postpos.cpp -I src -I src/Nequick/lib/private -I src/Nequick/lib/public -D WIN32 -D NDEBUG -D _CONSOLE -D _CRT_SECURE_NO_DEPRECATE -D ENAGLO -D ENACMP -D ENAGAL -D NFREQ=6 -D TRACE -std=c++11 -O2
g++ -c -o ppp.o src/ppp.cpp -I src -I src/Nequick/lib/private -I src/Nequick/lib/public -D WIN32 -D NDEBUG -D _CONSOLE -D _CRT_SECURE_NO_DEPRECATE -D ENAGLO -D ENACMP -D ENAGAL -D NFREQ=6 -D TRACE -std=c++11 -O2
g++ -c -o ppp_ar.o src/ppp_ar.cpp -I src -I src/Nequick/lib/private -I src/Nequick/lib/public -D WIN32 -D NDEBUG -D _CONSOLE -D _CRT_SECURE_NO_DEPRECATE -D ENAGLO -D ENACMP -D ENAGAL -D NFREQ=6 -D TRACE -std=c++11 -O2
g++ -c -o ppp_corr.o src/ppp_corr.cpp -I src -I src/Nequick/lib/private -I src/Nequick/lib/public -D WIN32 -D NDEBUG -D _CONSOLE -D _CRT_SECURE_NO_DEPRECATE -D ENAGLO -D ENACMP -D ENAGAL -D NFREQ=6 -D TRACE -std=c++11 -O2
g++ -c -o preceph.o src/preceph.cpp -I src -I src/Nequick/lib/private -I src/Nequick/lib/public -D WIN32 -D NDEBUG -D _CONSOLE -D _CRT_SECURE_NO_DEPRECATE -D ENAGLO -D ENACMP -D ENAGAL -D NFREQ=6 -D TRACE -std=c++11 -O2
g++ -c -o qzslex.o src/qzslex.cpp -I src -I src/Nequick/lib/private -I src/Nequick/lib/public -D WIN32 -D NDEBUG -D _CONSOLE -D _CRT_SECURE_NO_DEPRECATE -D ENAGLO -D ENACMP -D ENAGAL -D NFREQ=6 -D TRACE -std=c++11 -O2
g++ -c -o rinex.o src/rinex.cpp -I src -I src/Nequick/lib/private -I src/Nequick/lib/public -D WIN32 -D NDEBUG -D _CONSOLE -D _CRT_SECURE_NO_DEPRECATE -D ENAGLO -D ENACMP -D ENAGAL -D NFREQ=6 -D TRACE -std=c++11 -O2
g++ -c -o rtcm.o src/rtcm.cpp -I src -I src/Nequick/lib/private -I src/Nequick/lib/public -D WIN32 -D NDEBUG -D _CONSOLE -D _CRT_SECURE_NO_DEPRECATE -D ENAGLO -D ENACMP -D ENAGAL -D NFREQ=6 -D TRACE -std=c++11 -O2
g++ -c -o rtcm2.o src/rtcm2.cpp -I src -I src/Nequick/lib/private -I src/Nequick/lib/public -D WIN32 -D NDEBUG -D _CONSOLE -D _CRT_SECURE_NO_DEPRECATE -D ENAGLO -D ENACMP -D ENAGAL -D NFREQ=6 -D TRACE -std=c++11 -O2
g++ -c -o rtcm3.o src/rtcm3.cpp -I src -I src/Nequick/lib/private -I src/Nequick/lib/public -D WIN32 -D NDEBUG -D _CONSOLE -D _CRT_SECURE_NO_DEPRECATE -D ENAGLO -D ENACMP -D ENAGAL -D NFREQ=6 -D TRACE -std=c++11 -O2
g++ -c -o rtcm3e.o src/rtcm3e.cpp -I src -I src/Nequick/lib/private -I src/Nequick/lib/public -D WIN32 -D NDEBUG -D _CONSOLE -D _CRT_SECURE_NO_DEPRECATE -D ENAGLO -D ENACMP -D ENAGAL -D NFREQ=6 -D TRACE -std=c++11 -O2
g++ -c -o rtkcmn.o src/rtkcmn.cpp -I src -I src/Nequick/lib/private -I src/Nequick/lib/public -D WIN32 -D NDEBUG -D _CONSOLE -D _CRT_SECURE_NO_DEPRECATE -D ENAGLO -D ENACMP -D ENAGAL -D NFREQ=6 -D TRACE -std=c++11 -O2
g++ -c -o rtkpos.o src/rtkpos.cpp -I src -I src/Nequick/lib/private -I src/Nequick/lib/public -D WIN32 -D NDEBUG -D _CONSOLE -D _CRT_SECURE_NO_DEPRECATE -D ENAGLO -D ENACMP -D ENAGAL -D NFREQ=6 -D TRACE -std=c++11 -O2
g++ -c -o sbas.o src/sbas.cpp -I src -I src/Nequick/lib/private -I src/Nequick/lib/public -D WIN32 -D NDEBUG -D _CONSOLE -D _CRT_SECURE_NO_DEPRECATE -D ENAGLO -D ENACMP -D ENAGAL -D NFREQ=6 -D TRACE -std=c++11 -O2
g++ -c -o solution.o src/solution.cpp -I src -I src/Nequick/lib/private -I src/Nequick/lib/public -D WIN32 -D NDEBUG -D _CONSOLE -D _CRT_SECURE_NO_DEPRECATE -D ENAGLO -D ENACMP -D ENAGAL -D NFREQ=6 -D TRACE -std=c++11 -O2
g++ -c -o test_src.o src/test_src.cpp -I src -I src/Nequick/lib/private -I src/Nequick/lib/public -D WIN32 -D NDEBUG -D _CONSOLE -D _CRT_SECURE_NO_DEPRECATE -D ENAGLO -D ENACMP -D ENAGAL -D NFREQ=6 -D TRACE -std=c++11 -O2
g++ -c -o tides.o src/tides.cpp -I src -I src/Nequick/lib/private -I src/Nequick/lib/public -D WIN32 -D NDEBUG -D _CONSOLE -D _CRT_SECURE_NO_DEPRECATE -D ENAGLO -D ENACMP -D ENAGAL -D NFREQ=6 -D TRACE -std=c++11 -O2
g++ -c -o tle.o src/tle.cpp -I src -I src/Nequick/lib/private -I src/Nequick/lib/public -D WIN32 -D NDEBUG -D _CONSOLE -D _CRT_SECURE_NO_DEPRECATE -D ENAGLO -D ENACMP -D ENAGAL -D NFREQ=6 -D TRACE -std=c++11 -O2

echo 所有源文件编译完成！

REM 链接生成可执行文件
g++ -o rnx2rtkp.exe *.o

if errorlevel 1 (
    echo 链接失败！
    pause
    exit /b 1
) else (
    echo 编译成功！生成 rnx2rtkp.exe
    echo.
    echo 运行程序...
    rnx2rtkp.exe -k IGS-Data/GNSS_Option.opt -x 5
)

pause
