@echo off
echo Installing say-it dependencies...
pip install keyboard sounddevice numpy faster-whisper pystray pillow

echo.
echo Checking for NVIDIA GPU...
nvidia-smi >nul 2>&1
if %errorlevel% == 0 (
    echo GPU found! Installing CUDA support for faster transcription...
    pip install nvidia-cublas-cu12 nvidia-cudnn-cu12
) else (
    echo No GPU detected, will use CPU.
)

echo.
echo Done! Run say-it with: run.bat
pause
