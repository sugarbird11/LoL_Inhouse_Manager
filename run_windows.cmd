@echo off
setlocal

REM LoL Inhouse Manager Windows 실행 스크립트
REM 사용법: 프로젝트 루트( manage.py 있는 위치 )에서 실행

if not exist manage.py (
    echo [ERROR] manage.py 파일이 현재 폴더에 없습니다.
    echo 프로젝트 루트 폴더에서 다시 실행하세요.
    pause
    exit /b 1
)

if not exist venv (
    echo [INFO] 가상환경이 없어 새로 생성합니다...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] 가상환경 생성 실패
        pause
        exit /b 1
    )
)

call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] 가상환경 활성화 실패
    pause
    exit /b 1
)

echo [INFO] 패키지 설치를 진행합니다...
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] requirements.txt 설치 실패
    pause
    exit /b 1
)

if not exist .env (
    if exist .env.example (
        echo [INFO] .env.example 을 .env 로 복사합니다...
        copy .env.example .env > nul
    )
)

echo [INFO] 데이터베이스 migration을 진행합니다...
python manage.py migrate
if errorlevel 1 (
    echo [ERROR] migrate 실패
    pause
    exit /b 1
)

echo [INFO] 서버를 실행합니다...
echo [INFO] 브라우저에서 http://127.0.0.1:8000/ 로 접속하세요.
python manage.py runserver

endlocal
