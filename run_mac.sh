#!/usr/bin/env bash
set -e

# LoL Inhouse Manager macOS 실행 스크립트
# 사용법: 프로젝트 루트( manage.py 있는 위치 )에서 실행

if [ ! -f "project/manage.py" ]; then
  echo "[ERROR] manage.py 파일이 현재 폴더에 없습니다."
  echo "프로젝트 루트 폴더에서 다시 실행하세요."
  exit 1
fi

if [ ! -d "venv" ]; then
  echo "[INFO] 가상환경이 없어 새로 생성합니다..."
  python3 -m venv venv
fi

source venv/bin/activate

echo "[INFO] 패키지 설치를 진행합니다..."
pip install -r requirements.txt

if [ ! -f ".env" ] && [ -f ".env.example" ]; then
  echo "[INFO] .env.example 을 .env 로 복사합니다..."
  cp .env.example .env
fi

echo "[INFO] 데이터베이스 migration을 진행합니다..."
python project/manage.py migrate

echo "[INFO] 서버를 실행합니다..."
echo "[INFO] 브라우저에서 http://127.0.0.1:8000/ 로 접속하세요."
python project/manage.py runserver

# 브라우저에서 lobbies 페이지 열기
LOBBY_URL="http://127.0.0.1:8000/lobbies"

if command -v open >/dev/null 2>&1; then
  echo "[INFO] 브라우저에서 ${LOBBY_URL} 를 엽니다."
  open "${LOBBY_URL}" >/dev/null 2>&1 || echo "[WARN] 브라우저를 자동으로 열지 못했습니다. 직접 접속하세요: ${LOBBY_URL}"
else
  echo "[WARN] 'open' 명령을 찾지 못했습니다. 직접 접속하세요: ${LOBBY_URL}"
fi
