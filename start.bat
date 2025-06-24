@echo off
REM Batch script to set up and run the Bulletproof Gemini Voice Synthesizer on Windows

ECHO Bulletproof Gemini Voice Synthesizer - Windows Start Script
ECHO ---------------------------------------------------------

REM Set the name of the virtual environment directory
set VENV_DIR=venv

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not found in PATH.
    echo Please install Python 3 and ensure it's added to your PATH.
    pause
    exit /b 1
)

REM Check if the virtual environment directory exists
IF NOT EXIST "%VENV_DIR%\Scripts\activate.bat" (
    ECHO Creating virtual environment in "%VENV_DIR%\"...
    python -m venv "%VENV_DIR%"
    IF %errorlevel% neq 0 (
        ECHO ERROR: Failed to create virtual environment.
        pause
        exit /b 1
    )
    ECHO Virtual environment created.
) ELSE (
    ECHO Virtual environment "%VENV_DIR%\" already exists.
)

REM Activate the virtual environment
ECHO Activating virtual environment...
CALL "%VENV_DIR%\Scripts\activate.bat"
IF %errorlevel% neq 0 (
    ECHO ERROR: Failed to activate virtual environment.
    pause
    exit /b 1
)

REM Install/update dependencies
ECHO Installing/Updating dependencies from requirements.txt...
pip install -r requirements.txt
IF %errorlevel% neq 0 (
    ECHO ERROR: Failed to install dependencies. Check requirements.txt and your internet connection.
    pause
    exit /b 1
)
ECHO Dependencies installed/updated successfully.

REM Check for .env file and API keys (basic check)
IF NOT EXIST ".env" (
    ECHO WARNING: .env file not found.
    ECHO Please copy .env.example to .env and add your GOOGLE_API_KEYS.
    ECHO Application might run in simulated mode or fail if keys are required by the actual API.
)

ECHO Starting the Flask application...
ECHO You can access it at http://localhost:5000 or http://127.0.0.1:5000
python app.py

ECHO Application finished.
pause
exit /b 0
