@echo off
setlocal

:: ����Ҫɾ�����ļ�����
set "ext1=.trace"
set "ext2=.pospsu_res"
set "ext3=.pospsu_snr"
set "ext4=.pos"

:: ��ȡ��ǰ·��
set "target_dir=%cd%"

:: �л���Ŀ��·��
cd /d "%target_dir%"

echo ����ɾ���������͵��ļ���
echo   %ext1%
echo   %ext2%
echo   %ext3%
echo.

:: ɾ�� .trace �ļ�
if exist *%ext1% (
    echo ɾ�� %ext1% �ļ�...
    del /q *%ext1%
) else (
    echo û���ҵ� %ext1% �ļ���
)

:: ɾ�� .pospsu_res �ļ�
if exist *%ext2% (
    echo ɾ�� %ext2% �ļ�...
    del /q *%ext2%
) else (
    echo û���ҵ� %ext2% �ļ���
)

:: ɾ�� .pospsu_snr �ļ�
if exist *%ext3% (
    echo ɾ�� %ext3% �ļ�...
    del /q *%ext3%
) else (
    echo û���ҵ� %ext3% �ļ���
)

echo.
echo ����ָ����ʽ�ļ���������ɣ�
echo.
:: �����pos�ļ�ת����Solution�ļ���
:: ���� Solution �ļ��У���������ڣ�
if not exist "Solution" (
    mkdir "Solution"
)
:: �����н�� .pos �ļ��ƶ��� Solution �ļ���
echo ����ת�� %ext4% �ļ���
if exist *%ext4% (
    move *.pos "Solution\" >nul 2>&1
) else (
    echo û���ҵ� %ext4% �ļ���
)

echo.
echo ȫ��.pos�ļ������ƶ��� Solution �ļ���
:: ���ִ��ڲ��ر�
cmd /k