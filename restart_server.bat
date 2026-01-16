@echo off
echo ========================================
echo  Restarting Server with Groq
echo ========================================
echo.
echo Step 1: Clearing old data...
rmdir /s /q data\faiss_index 2>nul
del /q uploads\*.pdf 2>nul
echo [OK] Cleared cached data
echo.
echo Step 2: Verifying .env configuration...
findstr "LLM_PROVIDER" .env
echo.
echo Step 3: Starting server...
echo Server will start on http://127.0.0.1:8000
echo.
uvicorn main:app --reload
