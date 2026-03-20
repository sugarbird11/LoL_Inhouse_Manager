#!/usr/bin/env bash
set -e

# LoL Inhouse Manager macOS 실행 스크립트
# 사용법: 프로젝트 루트( manage.py 있는 위치 )에서 실행

if [ ! -f "project/manage.py" ]; then
  echo "[ERROR] This directory doesn't have manage.py"
  exit 1
fi

if [ ! -d "venv" ]; then
  echo "[INFO] Creating a virtual environment..."
  python3 -m venv venv
fi

source venv/bin/activate

echo "[INFO] Installing packages..."
pip install -r requirements.txt


echo "[INFO] Migrating database..."
python project/manage.py migrate

# 브라우저에서 lobbies 페이지 열기
LOBBY_URL="http://127.0.0.1:8000/lobbies"

if command -v open >/dev/null 2>&1; then
  echo "[INFO] Opening ${LOBBY_URL} in your browser."
  open "${LOBBY_URL}" >/dev/null 2>&1 || echo "[WARN] Can't open automatically. Try yourself in your browser : ${LOBBY_URL}"
else
  echo "[WARN] Can't found command 'open'. Try yourself in your browser: ${LOBBY_URL}"
fi

python project/manage.py runserver
