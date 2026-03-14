@echo off
echo Setting up environment...

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH. Please install Python 3.8 or higher.
    pause
    exit /b 1
)

REM Check Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set version=%%i
for /f "tokens=1,2 delims=." %%a in ("%version%") do (
    if %%a lss 3 (
        echo Error: Python version must be 3.8 or higher. Current: %version%
        pause
        exit /b 1
    )
    if %%a equ 3 if %%b lss 8 (
        echo Error: Python version must be 3.8 or higher. Current: %version%
        pause
        exit /b 1
    )
)

if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo Error: Failed to create virtual environment.
        pause
        exit /b 1
    )
) else (
    echo Virtual environment already exists.
)

echo Activating virtual environment...
call venv\Scripts\activate
if %errorlevel% neq 0 (
    echo Error: Failed to activate virtual environment.
    pause
    exit /b 1
)

echo Installing dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Error: Failed to install Python dependencies.
    pause
    exit /b 1
)

echo Installing Playwright browsers...
playwright install
if %errorlevel% neq 0 (
    echo Error: Failed to install Playwright browsers.
    pause
    exit /b 1
)

echo Setup complete!
echo You can now run the application using run.bat