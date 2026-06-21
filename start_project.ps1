Start-Process cmd -ArgumentList '/k "cd frontend && npm run dev"'
Start-Process cmd -ArgumentList '/k "cd backend && .venv\Scripts\activate && uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"'
