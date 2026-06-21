@echo off
start cmd /k "cd backend && uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"
start cmd /k "npm run dev"