@echo off
echo === KHOI DONG CARO ONLINE ===
echo.

:: Chuyen den thu muc chua file bat
cd /d %~dp0

:: Kiem tra moi truong ao da ton tai chua
if not exist ".venv" (
    echo Khong tim thay moi truong ao. Dang tao...
    py -3.14 -m venv .venv
    if errorlevel 1 (
        echo LOI: Khong the tao moi truong ao!
        echo Vui long kiem tra Python 3.14 da duoc cai dat chua.
        pause
        exit /b 1
    )
    echo Moi truong ao da duoc tao thanh cong!
    echo.
)

:: Kich hoat moi truong ao va kiem tra thu vien
echo Dang kiem tra thu vien...
call .venv\Scripts\activate

:: Kiem tra pygame da cai chua (thu vien chinh)
python -c "import pygame" 2>nul
if errorlevel 1 (
    echo Dang cai dat thu vien tu requirements.txt...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo LOI: Khong the cai dat thu vien!
        pause
        exit /b 1
    )
    echo Thu vien da duoc cai dat thanh cong!
    echo.
)

:: Chay Server trong terminal moi
echo Dang khoi dong Server...
start "Caro Server" cmd /k "cd /d %~dp0 && .venv\Scripts\activate && python server.py"

:: Doi 2 giay de server khoi dong
timeout /t 2 /nobreak > nul

:: Chay 3 Client trong cac terminal moi
echo Dang khoi dong Client 1...
start "Caro Client 1" cmd /k "cd /d %~dp0 && .venv\Scripts\activate && python game.py"

timeout /t 1 /nobreak > nul

echo Dang khoi dong Client 2...
start "Caro Client 2" cmd /k "cd /d %~dp0 && .venv\Scripts\activate && python game.py"

timeout /t 1 /nobreak > nul

echo Dang khoi dong Client 3...
start "Caro Client 3" cmd /k "cd /d %~dp0 && .venv\Scripts\activate && python game.py"

echo.
echo === DA KHOI DONG XONG ===
echo - 1 Server
echo - 3 Client
echo.
echo Nhan phim bat ky de dong cua so nay...
pause > nul
