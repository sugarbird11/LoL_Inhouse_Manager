@echo off
setlocal

REM LoL Inhouse Manager Windows 실행 스크립트
REM 사용법: 프로젝트 루트( project\manage.py 있는 위치 )에서 실행

if not exist "project\manage.py" (
    echo [ERROR] This directory doesn't have manage.py
    exit /b 1
)

if not exist "venv" (
    echo [INFO] Creating a virtual environment...
    python -m venv venv
)

call venv\Scripts\activate.bat

echo [INFO] Installing packages...
pip install -r requirements.txt

echo [INFO] Migrating database...
python project\manage.py migrate

REM 브라우저에서 lobbies 페이지 열기
set LOBBY_URL=http://127.0.0.1:8000/lobbies

echo [INFO] Opening %LOBBY_URL% in your browser.
start "" "%LOBBY_URL%"

python project\manage.py runserver

endlocal
