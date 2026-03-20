# LoL Inhouse Manager

리그 오브 레전드 내전 팀 배정, 경기 결과 업로드, PS 반영을 위한 Django 프로젝트입니다.

## 주요 기능
- 플레이어 등록 및 관리
- 내전 팀 자동 배정
- 경기 결과 업로드
- OCR 기반 결과 자동 입력
- PS 반영 및 롤백

## 실행 방법
1. 가상환경 생성
2. 패키지 설치
3. migrate 실행
4. runserver 실행

### Windows
```cmd
python -m venv venv
venv\Scripts\activate.bat
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### macOS
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```
