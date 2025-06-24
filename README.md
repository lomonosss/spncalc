# Bulletproof Gemini Voice Synthesizer

A high-performance, parallelized Text-to-Speech (TTS) web application designed for ease of use and simple setup. This application allows users to synthesize long texts quickly by leveraging multiple Google Gemini API keys in parallel.

## Features

*   **Parallel TTS Processing**: Splits long texts into manageable chunks and processes them in parallel using different API keys for speed.
*   **Multiple API Key Support**: Reads Google API keys from a `.env` file.
*   **Natural Pauses**: Inserts a 500ms silent segment between audio from different text chunks for more natural-sounding long narrations.
*   **User-Friendly Interface**: Clean, modern, and responsive web UI for text input, voice selection, and audio download.
*   **"Bulletproof" Launch Scripts**: Comes with `start.bat` (Windows) and `start.sh` (Linux/macOS) for automated setup (virtual environment creation, dependency installation) and application launch.
*   **Robust Error Logging**: Detailed backend error logging for easier debugging.

## Prerequisites

*   **Python 3**: Ensure Python 3 (python3) is installed and accessible in your system's PATH.
*   **FFmpeg**: `pydub` (used for audio manipulation) requires FFmpeg.
    *   **Windows**: Download FFmpeg from [ffmpeg.org](https://ffmpeg.org/download.html), extract it, and add the `bin` directory to your PATH.
    *   **macOS**: `brew install ffmpeg`
    *   **Linux**: `sudo apt-get install ffmpeg` or `sudo yum install ffmpeg`

## Setup and Launch

1.  **Clone or Download the Repository.**

2.  **Prepare API Keys:**
    *   Make a copy of the `.env.example` file and rename it to `.env`.
    *   Open the `.env` file and replace the placeholder API keys with your actual Google API keys, separated by commas if you have multiple.
    ```
    GOOGLE_API_KEYS="YOUR_ACTUAL_API_KEY_1,YOUR_ACTUAL_API_KEY_2"
    ```

3.  **Run the Application using the appropriate script:**

    *   **Windows:**
        1.  Simply double-click the `start.bat` file.
        2.  It will create a virtual environment, install dependencies, and start the web server.

    *   **Linux / macOS:**
        1.  Open your terminal in the project directory.
        2.  Make the script executable: `chmod +x start.sh`
        3.  Run the script: `./start.sh`
        4.  It will create a virtual environment, install dependencies, and start the web server.

4.  **Access the Application:**
    *   Once the server is running (the script will indicate this), open your web browser and go to: `http://127.0.0.1:5000` or `http://localhost:5000`.

## Important Note on Gemini API

*   The Text-to-Speech (TTS) functionality in `app.py` currently **simulates** the call to the Google Gemini API. You will need to:
    1.  Ensure you have the correct `google-generativeai` Python library version that supports the TTS features you intend to use.
    2.  Replace the simulation block in the `synthesize_chunk_worker` function within `app.py` with the actual SDK calls to Google's Gemini text-to-speech service, including appropriate model selection and voice parameter handling.

This project provides the framework for parallelization, API key management, and user interface. The core TTS API interaction needs to be implemented with your specific Gemini project credentials and SDK usage.