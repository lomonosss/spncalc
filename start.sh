#!/bin/bash
# Shell script to set up and run the Bulletproof Gemini Voice Synthesizer on Linux/macOS

echo "Bulletproof Gemini Voice Synthesizer - Linux/macOS Start Script"
echo "------------------------------------------------------------"

# Set the name of the virtual environment directory
VENV_DIR="venv"

# Function to display error and exit
error_exit() {
    echo "ERROR: $1" >&2
    exit 1
}

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    error_exit "Python 3 is not installed or not found in PATH. Please install Python 3."
fi

# Check if the virtual environment directory exists
if [ ! -d "$VENV_DIR/bin" ]; then
    echo "Creating virtual environment in '$VENV_DIR/'..."
    python3 -m venv "$VENV_DIR" || error_exit "Failed to create virtual environment."
    echo "Virtual environment created."
else
    echo "Virtual environment '$VENV_DIR/' already exists."
fi

# Activate the virtual environment
echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate" || error_exit "Failed to activate virtual environment."

# Install/update dependencies
echo "Installing/Updating dependencies from requirements.txt..."
pip install -r requirements.txt || error_exit "Failed to install dependencies. Check requirements.txt and your internet connection."
echo "Dependencies installed/updated successfully."

# Check for .env file and API keys (basic check)
if [ ! -f ".env" ]; then
    echo "WARNING: .env file not found."
    echo "Please copy .env.example to .env and add your GOOGLE_API_KEYS."
    echo "Application might run in simulated mode or fail if keys are required by the actual API."
fi

echo "Starting the Flask application..."
echo "You can access it at http://localhost:5000 or http://127.0.0.1:5000"
echo "Press Ctrl+C to stop the server."
python3 app.py

# Deactivate virtual environment (optional, as script exit will effectively do this)
# echo "Deactivating virtual environment..."
# deactivate

echo "Application finished."
exit 0
