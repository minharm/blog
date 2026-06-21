# 🎯 start_project.ps1 (구형 경로 수정 완료)
# 최상위 루트 폴더(blog)에서 백엔드와 프론트엔드 서버를 올바르게 순차 기동합니다.

Start-Process powershell -ArgumentList "-NoExit", "-Command", "uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "npm run dev"