@echo off
echo 使用MSVC编译器编译GNSS定位软件...
echo.

REM 检查cl.exe是否可用
cl >nul 2>&1
if errorlevel 1 (
    echo 错误：未找到MSVC编译器，请先运行Visual Studio Developer Command Prompt
    echo 或者安装Visual Studio Build Tools
    pause
    exit /b 1
)

REM 编译主程序
echo 编译主程序...
cl /Fe:rnx2rtkp.exe ^
    app/main/rnx2rtkp.cpp ^
    src/bdgim.cpp ^
    src/bdssh.cpp ^
    src/common.cpp ^
    src/datum.cpp ^
    src/DBSCAN.cpp ^
    src/ephemeris.cpp ^
    src/geoid.cpp ^
    src/ionex.cpp ^
    src/lambda.cpp ^
    src/options.cpp ^
    src/pntpos.cpp ^
    src/postpos.cpp ^
    src/ppp.cpp ^
    src/ppp_ar.cpp ^
    src/ppp_corr.cpp ^
    src/preceph.cpp ^
    src/qzslex.cpp ^
    src/rinex.cpp ^
    src/rtcm.cpp ^
    src/rtcm2.cpp ^
    src/rtcm3.cpp ^
    src/rtcm3e.cpp ^
    src/rtkcmn.cpp ^
    src/rtkpos.cpp ^
    src/sbas.cpp ^
    src/solution.cpp ^
    src/test_src.cpp ^
    src/tides.cpp ^
    src/tle.cpp ^
    src/Nequick/nequick_test.cpp ^
    src/Nequick/NeQuickG_JRC.c ^
    src/Nequick/NeQuickG_JRC_CCIR.c ^
    src/Nequick/NeQuickG_JRC_ccir11.c ^
    src/Nequick/NeQuickG_JRC_ccir12.c ^
    src/Nequick/NeQuickG_JRC_ccir13.c ^
    src/Nequick/NeQuickG_JRC_ccir14.c ^
    src/Nequick/NeQuickG_JRC_ccir15.c ^
    src/Nequick/NeQuickG_JRC_ccir16.c ^
    src/Nequick/NeQuickG_JRC_ccir17.c ^
    src/Nequick/NeQuickG_JRC_ccir18.c ^
    src/Nequick/NeQuickG_JRC_ccir19.c ^
    src/Nequick/NeQuickG_JRC_ccir20.c ^
    src/Nequick/NeQuickG_JRC_ccir21.c ^
    src/Nequick/NeQuickG_JRC_ccir22.c ^
    src/Nequick/NeQuickG_JRC_coordinates.c ^
    src/Nequick/NeQuickG_JRC_electron_density.c ^
    src/Nequick/NeQuickG_JRC_exception.c ^
    src/Nequick/NeQuickG_JRC_Gauss_Kronrod_integration.c ^
    src/Nequick/NeQuickG_JRC_geometry.c ^
    src/Nequick/NeQuickG_JRC_input_data.c ^
    src/Nequick/NeQuickG_JRC_input_data_std_stream.c ^
    src/Nequick/NeQuickG_JRC_input_data_stream.c ^
    src/Nequick/NeQuickG_JRC_interpolate.c ^
    src/Nequick/NeQuickG_JRC_iono_E_layer.c ^
    src/Nequick/NeQuickG_JRC_iono_F1_layer.c ^
    src/Nequick/NeQuickG_JRC_iono_F2_layer.c ^
    src/Nequick/NeQuickG_JRC_iono_F2_layer_fourier_coefficients.c ^
    src/Nequick/NeQuickG_JRC_iono_profile.c ^
    src/Nequick/NeQuickG_JRC_math_utils.c ^
    src/Nequick/NeQuickG_JRC_MODIP.c ^
    src/Nequick/NeQuickG_JRC_MODIP_grid.c ^
    src/Nequick/NeQuickG_JRC_ray.c ^
    src/Nequick/NeQuickG_JRC_ray_slant.c ^
    src/Nequick/NeQuickG_JRC_ray_vertical.c ^
    src/Nequick/NeQuickG_JRC_solar.c ^
    src/Nequick/NeQuickG_JRC_solar_activity.c ^
    src/Nequick/NeQuickG_JRC_TEC_integration.c ^
    src/Nequick/NeQuickG_JRC_time.c ^
    /I src ^
    /I src/Nequick/lib/private ^
    /I src/Nequick/lib/public ^
    /D WIN32 ^
    /D NDEBUG ^
    /D _CONSOLE ^
    /D _CRT_SECURE_NO_DEPRECATE ^
    /D ENAGLO ^
    /D ENACMP ^
    /D ENAGAL ^
    /D NFREQ=6 ^
    /D TRACE ^
    /std:c++11 ^
    /O2

if errorlevel 1 (
    echo 编译失败！
    pause
    exit /b 1
) else (
    echo 编译成功！生成 rnx2rtkp.exe
    echo.
    echo 运行程序...
    rnx2rtkp.exe -k IGS-Data/GNSS_Option.opt -x 5
)

pause




