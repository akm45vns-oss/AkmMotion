@echo off
echo Starting AkmMotion Backend...
start cmd /k "cd backend && uvicorn app.main:app --reload"

echo Starting AkmMotion Frontend...
start cmd /k "cd frontend && npm run dev"

echo Both servers are starting up!
