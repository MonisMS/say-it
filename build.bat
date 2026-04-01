@echo off
pushd "%~dp0"

echo Installing/updating dependencies...
pip install pyinstaller keyboard pystray pillow faster-whisper sounddevice numpy huggingface_hub

echo.
echo Killing any running say-it.exe...
taskkill /f /im say-it.exe 2>nul

echo.
echo Cleaning old build...
if exist build rmdir /s /q build
if exist dist  rmdir /s /q dist

echo.
echo Building say-it.exe ...
pyinstaller ^
  --onefile ^
  --noconsole ^
  --clean ^
  --name say-it ^
  --collect-all faster_whisper ^
  --collect-all ctranslate2 ^
  --collect-all sounddevice ^
  --collect-all huggingface_hub ^
  --hidden-import keyboard ^
  --hidden-import tokenizers ^
  --hidden-import pystray ^
  --hidden-import PIL ^
  main.py

echo.
echo Done! Your exe is at: dist\say-it.exe
echo.
echo NOTE: First run will download the medium model (~1.5 GB). Be patient.
popd
pause
