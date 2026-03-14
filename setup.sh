#!/bin/bash

echo "Setting up environment..."

# Check if Python3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is not installed or not in PATH. Please install Python 3.8 or higher."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
    echo "Error: Python version must be 3.8 or higher. Current: $PYTHON_VERSION"
    exit 1
fi

# Check for tkinter (on Linux systems)
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    python3 -c "import tkinter" 2>/dev/null
    if [ $? -ne 0 ]; then
        echo "Warning: tkinter is not available. GUI mode will not work."
        echo "On Ubuntu/Debian: sudo apt-get install python3-tk"
        echo "On Fedora/CentOS: sudo dnf install python3-tkinter"
        echo "On Arch: sudo pacman -S tk"
        echo "You can still use CLI mode."
    fi
fi

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "Error: Failed to create virtual environment."
        exit 1
    fi
else
    echo "Virtual environment already exists."
fi

echo "Activating virtual environment..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "Error: Failed to activate virtual environment."
    exit 1
fi

echo "Installing dependencies..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "Error: Failed to install Python dependencies."
    exit 1
fi

echo "Installing Playwright browsers..."
playwright install
if [ $? -ne 0 ]; then
    echo "Error: Failed to install Playwright browsers."
    exit 1
fi

echo "Setup complete!"
echo "You can now run the application using ./run.sh"